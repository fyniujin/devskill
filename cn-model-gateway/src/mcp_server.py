"""MCP (Model Context Protocol) server - JSON-RPC 2.0 implementation."""
from __future__ import annotations

import json
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional

from .adapters.base import ChatMessage
from .router import ModelRouter
from .router import (
    ERROR_PARAM_INVALID,
    ERROR_MODEL_UNAVAILABLE,
    ERROR_RATE_LIMITED,
    ERROR_INTERNAL,
    ERROR_PROVIDER_NOT_FOUND,
)
from .monitor import Monitor


class MCPServer:
    """Minimal MCP server implementing JSON-RPC 2.0 over stdio."""

    def __init__(self, router: ModelRouter, monitor: Monitor) -> None:
        self.router = router
        self.monitor = monitor
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._resources: Dict[str, Dict[str, Any]] = {}
        self._prompts: Dict[str, Dict[str, Any]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register built-in tools, resources, and prompts."""
        self._tools = {
            "ask_model": {
                "name": "ask_model",
                "description": "向指定的国产模型提问。provider 可选: deepseek/tongyi/zhipu/kimi/hunyua"
                            "n/doubao，留空则自动选择可用模型。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string", "description": "模型提供商名称"},
                        "question": {"type": "string", "description": "要提问的内容"},
                        "model": {"type": "string", "description": "具体模型 ID（可选）"},
                        "temperature": {"type": "number", "description": "温度参数 0-2（可选）"},
                    },
                    "required": ["question"],
                },
            },
            "compare_models": {
                "name": "compare_models",
                "description": "向多个模型发送同一问题，返回对比结果。用于评估不同模型的回答质量。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "要提问的内容"},
                        "providers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要对比的提供商列表（可选，默认全部可用）",
                        },
                    },
                    "required": ["question"],
                },
            },
            "list_providers": {
                "name": "list_providers",
                "description": "列出所有已配置且可用的模型提供商。",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "health_check": {
                "name": "health_check",
                "description": "检查所有已配置模型提供商的连通性。",
                "inputSchema": {"type": "object", "properties": {}},
            },
        }

        self._resources = {
            "config": {
                "uri": "cn-model-gateway://config",
                "name": "当前配置",
                "description": "查看当前已注册的模型提供商列表（不含 api_key）",
                "mimeType": "application/json",
            },
            "usage_stats": {
                "uri": "cn-model-gateway://usage",
                "name": "使用统计",
                "description": "查看各模型调用次数、token 消耗等统计信息",
                "mimeType": "application/json",
            },
        }

        self._prompts = {
            "code_review": {
                "name": "code_review",
                "description": "代码审查提示模板",
                "arguments": [
                    {"name": "code", "description": "要审查的代码", "required": True},
                    {"name": "language", "description": "编程语言", "required": False},
                ],
            },
            "translate": {
                "name": "translate",
                "description": "翻译提示模板（中英互译）",
                "arguments": [
                    {"name": "text", "description": "要翻译的文本", "required": True},
                    {"name": "target_lang", "description": "目标语言（zh/en/ja）", "required": True},
                ],
            },
        }

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a single JSON-RPC 2.0 request. Returns response or None for notifications."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        # MCP initialization
        if method == "initialize":
            return self._success(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "cn-model-gateway",
                    "version": "1.0.0",
                    "description": "国产模型 MCP 服务器 - DeepSeek/通义/智谱/Kimi/混元/豆包一站式接入",
                },
            })

        # Tools
        if method == "tools/list":
            return self._success(req_id, {"tools": list(self._tools.values())})
        if method == "tools/call":
            return self._handle_tool_call(req_id, params)

        # Resources
        if method == "resources/list":
            return self._success(req_id, {"resources": list(self._resources.values())})
        if method == "resources/read":
            return self._handle_resource_read(req_id, params)

        # Prompts
        if method == "prompts/list":
            return self._success(req_id, {"prompts": list(self._prompts.values())})
        if method == "prompts/get":
            return self._handle_prompt_get(req_id, params)

        # Ping
        if method == "ping":
            return self._success(req_id, {})

        return self._error(req_id, -32601, f"未知方法: {method}")

    def _handle_tool_call(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name", "")
        args = params.get("arguments", {})
        handler: Optional[Callable] = getattr(self, f"_tool_{name}", None)
        if not handler:
            return self._error(req_id, ERROR_PARAM_INVALID, f"未知工具: {name}")
        try:
            result = handler(args)
            self.monitor.record_call(name, args, result)
            return self._success(req_id, {"content": [{"type": "text", "text": result}]})
        except Exception as e:
            return self._error(req_id, ERROR_INTERNAL, f"工具调用失败: {traceback.format_exc()}")

    def _tool_ask_model(self, args: Dict[str, Any]) -> str:
        provider = args.get("provider")
        question = args.get("question", "")
        if not question:
            raise ValueError("question 不能为空")
        msgs = [ChatMessage(role="user", content=question)]
        kwargs = {}
        if args.get("model"):
            kwargs["model"] = args["model"]
        if args.get("temperature") is not None:
            kwargs["temperature"] = args["temperature"]
        resp = self.router.chat(msgs, provider=provider, **kwargs)
        return (
            f"[via {resp.provider}/{resp.model}]\n{resp.content}\n"
            f"---\n耗时: {resp.duration_ms}ms | "
            f"Token: prompt={resp.usage.get('prompt_tokens', '?')}, "
            f"completion={resp.usage.get('completion_tokens', '?')}"
        )

    def _tool_compare_models(self, args: Dict[str, Any]) -> str:
        question = args.get("question", "")
        if not question:
            raise ValueError("question 不能为空")
        providers = args.get("providers")
        msgs = [ChatMessage(role="user", content=question)]
        results = self.router.compare_models(msgs, providers=providers)
        lines = [f"## 模型对比结果\n问题: {question}\n"]
        for provider, info in results.items():
            lines.append(f"### {provider}")
            if "error" in info:
                lines.append(f"  ❌ {info['error']}")
            else:
                lines.append(f"  模型: {info['model']}")
                lines.append(f"  耗时: {info['duration_ms']}ms")
                lines.append(f"  Token: {info['usage']}")
                lines.append(f"  回答: {info['content'][:200]}...")
            lines.append("")
        return "\n".join(lines)

    def _tool_list_providers(self, args: Dict[str, Any]) -> str:
        available = self.router.list_available()
        all_providers = list(self.router._adapters.keys())
        lines = ["## 模型提供商状态"]
        for p in all_providers:
            status = "✅ 可用" if p in available else "❌ 不可用"
            lines.append(f"- {p}: {status}")
        if not all_providers:
            lines.append("尚未配置任何提供商。请在 config.json 中填写 api_key。")
        return "\n".join(lines)

    def _tool_health_check(self, args: Dict[str, Any]) -> str:
        results = {}
        for provider, adapter in self.router._adapters.items():
            try:
                ok = adapter.check_health()
                results[provider] = "✅ 正常" if ok else "❌ 异常"
            except Exception as e:
                results[provider] = f"❌ {e}"
        lines = ["## 健康检查"]
        for p, s in results.items():
            lines.append(f"- {p}: {s}")
        return "\n".join(lines)

    def _handle_resource_read(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = params.get("uri", "")
        if uri == "cn-model-gateway://config":
            config_info = {}
            for provider, adapter in self.router._adapters.items():
                config_info[provider] = {
                    "available": adapter.is_available(),
                    "default_model": adapter.default_model,
                }
            content = json.dumps(config_info, ensure_ascii=False, indent=2)
            return self._success(req_id, {
                "contents": [{"uri": uri, "mimeType": "application/json", "text": content}]
            })
        if uri == "cn-model-gateway://usage":
            stats = self.monitor.get_stats()
            content = json.dumps(stats, ensure_ascii=False, indent=2)
            return self._success(req_id, {
                "contents": [{"uri": uri, "mimeType": "application/json", "text": content}]
            })
        return self._error(req_id, ERROR_PARAM_INVALID, f"未知资源: {uri}")

    def _handle_prompt_get(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        prompt = self._prompts.get(name)
        if not prompt:
            return self._error(req_id, ERROR_PARAM_INVALID, f"未知 prompt: {name}")

        templates = {
            "code_review": self._build_code_review(arguments),
            "translate": self._build_translate(arguments),
        }
        messages = templates.get(name, [])
        return self._success(req_id, {
            "description": prompt["description"],
            "messages": messages,
        })

    @staticmethod
    def _build_code_review(args: Dict[str, Any]) -> List[Dict[str, Any]]:
        code = args.get("code", "")
        language = args.get("language", "python")
        return [
            {
                "role": "system",
                "content": f"你是一位资深 {language} 代码审查专家。请审查以下代码，指出潜在问题、安全隐患和改进建议。",
            },
            {"role": "user", "content": f"```{language}\n{code}\n```"},
        ]

    @staticmethod
    def _build_translate(args: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = args.get("text", "")
        target = args.get("target_lang", "en")
        lang_map = {"zh": "中文", "en": "英文", "ja": "日文"}
        target_name = lang_map.get(target, target)
        return [
            {
                "role": "system",
                "content": f"你是一位专业翻译。请将以下文本翻译为{target_name}，保持语义准确、表达自然。",
            },
            {"role": "user", "content": text},
        ]

    def _success(self, req_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _error(self, req_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def run_stdio(self) -> None:
        """Run the MCP server over stdio (for Claude Code / Cursor / Cline)."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    self._send(self._error(None, -32700, f"JSON 解析错误: {e}"))
                    continue
                response = self.handle_request(request)
                if response is not None:
                    self._send(response)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self._send(self._error(None, ERROR_INTERNAL, f"服务器错误: {e}"))

    def _send(self, response: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()
