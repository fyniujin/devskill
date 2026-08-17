# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 服务器 —— 跨 skill 记忆总线。

把 zwjh-skill 的核心能力暴露为 MCP Tool，让其他 skill / Agent 直接调用：
  - zwjh_query:     语义检索长期记忆
  - zwjh_deposit:   沉淀知识点到记忆底座
  - zwjh_health:    获取记忆健康度报告

协议: MCP over stdio (JSON-RPC 2.0)
零依赖: 纯 Python 标准库实现，不引入任何第三方包。

启动方式: python scripts/mcp_server.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

# 确保能 import 同级模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from scripts import retrieval, deposit, health


# ── MCP 协议常量 ────────────────────────────────────────────────────────────
MCP_VERSION = "2024-11-05"


# ── MCP 消息构建 ────────────────────────────────────────────────────────────
def _rpc_result(request_id: Any, result: dict) -> dict:
    """构建 JSON-RPC 成功响应。"""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _rpc_error(request_id: Any, code: int, message: str) -> dict:
    """构建 JSON-RPC 错误响应。"""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _tool_result(content: str, is_error: bool = False) -> dict:
    """构建 MCP tool 调用结果。"""
    return {
        "content": [{"type": "text", "text": content}],
        "isError": is_error,
    }


# ── MCP Tool 定义 ──────────────────────────────────────────────────────────
TOOL_LIST = [
    {
        "name": "zwjh_query",
        "description": "语义检索长期记忆。输入问题/关键词，返回最相关的记忆片段（含日期、来源、相似度）。纯本地、零密钥。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "要搜索的问题或关键词",
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量（1-20，默认 8）",
                    "default": 8,
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "zwjh_deposit",
        "description": "沉淀一段文本到长期记忆底座。自动去重、事实抽取、关系建立。返回抽取到的事实和冲突信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要沉淀的文本内容",
                },
                "source": {
                    "type": "string",
                    "description": "来源标识（默认 conversation）",
                    "default": "conversation",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "zwjh_health",
        "description": "获取记忆底座健康度报告。包含：记忆数/实体数/关系数/健康度评分(0-100)/DB体积/硬件档位。",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ── MCP Tool 实现 ──────────────────────────────────────────────────────────
def _handle_zwjh_query(arguments: dict) -> dict:
    """处理 zwjh_query tool 调用。"""
    question = arguments.get("question", "")
    if not question:
        return _tool_result("错误：缺少 question 参数", is_error=True)
    top_k = min(max(int(arguments.get("top_k", 8)), 1), 20)

    hits = retrieval.semantic_search(question, top_k=top_k)
    if not hits:
        return _tool_result("未找到与「%s」相关的记忆。" % question)

    lines = []
    for h in hits:
        lines.append("[%s · %s · %.4f] %s" % (h["day"], h["source"], h["score"], h["snippet"]))
    return _tool_result("找到 %d 条相关记忆：\n\n%s" % (len(lines), "\n\n".join(lines)))


def _handle_zwjh_deposit(arguments: dict) -> dict:
    """处理 zwjh_deposit tool 调用。"""
    text = arguments.get("text", "")
    if not text:
        return _tool_result("错误：缺少 text 参数", is_error=True)
    source = arguments.get("source", "conversation")

    r = deposit.deposit_text(text, source=source)
    lines = ["沉淀完成："]
    lines.append("  状态：%s" % r.get("status", "?"))
    if r.get("memory_id"):
        lines.append("  记忆ID：%d" % r["memory_id"])
    if r.get("facts"):
        lines.append("  抽取到 %d 个事实：" % len(r["facts"]))
        for f in r["facts"]:
            lines.append("    - %s 的 %s 是 %s" % (f.get("entity", "?"), f.get("predicate", "?"), f.get("value", "?")))
    if r.get("relations"):
        lines.append("  建立 %d 个关系" % len(r["relations"]))
    conflict = r.get("conflict")
    if conflict:
        resolution = r.get("conflict_resolution", "待仲裁")
        lines.append("  ⚠️ 检测到冲突 → %s" % resolution)
    return _tool_result("\n".join(lines))


def _handle_zwjh_health(arguments: dict) -> dict:
    """处理 zwjh_health tool 调用。"""
    h = health.audit()
    lines = [
        "记忆健康度报告",
        "=" * 30,
        "  记忆条目 : %d" % h.get("memories", 0),
        "  实体数   : %d" % h.get("entities", 0),
        "  关系数   : %d" % h.get("relations", 0),
        "  健康度   : %.1f / 100" % h.get("score", 0),
        "  DB 体积  : %.2f MB" % h.get("db_size_mb", 0),
        "  硬件档位 : %s" % h.get("tier", "?"),
    ]
    if h.get("stale_memories"):
        lines.append("  ⚠️ 陈旧记忆 : %d 条" % h["stale_memories"])
    if h.get("orphan_entities"):
        lines.append("  ⚠️ 孤儿实体 : %d 个" % h["orphan_entities"])
    if h.get("conflicting_facts"):
        lines.append("  ⚠️ 冲突事实 : %d 条" % h["conflicting_facts"])
    return _tool_result("\n".join(lines))


# Tool 名称到处理函数的映射
TOOL_HANDLERS = {
    "zwjh_query": _handle_zwjh_query,
    "zwjh_deposit": _handle_zwjh_deposit,
    "zwjh_health": _handle_zwjh_health,
}


# ── MCP 消息处理 ────────────────────────────────────────────────────────────
def _handle_initialize(request_id: Any, params: dict) -> dict:
    """处理 initialize 请求。"""
    return _rpc_result(request_id, {
        "protocolVersion": MCP_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": "zwjh-skill",
            "version": "2.4.0",
            "description": "跨 skill 记忆总线（长期记忆 + 知识图谱 + 健康度）",
        },
    })


def _handle_tools_list(request_id: Any) -> dict:
    """处理 tools/list 请求。"""
    return _rpc_result(request_id, {"tools": TOOL_LIST})


def _handle_tools_call(request_id: Any, params: dict) -> dict:
    """处理 tools/call 请求。"""
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return _rpc_error(request_id, -32601, "未知 tool: %s" % tool_name)

    try:
        result = handler(arguments)
        return _rpc_result(request_id, result)
    except Exception as e:
        return _rpc_error(request_id, -32600, "%s" % str(e))


def _handle_request(request: dict) -> dict | None:
    """处理单个 JSON-RPC 请求。返回 None 表示是 notification（无需响应）。"""
    if not isinstance(request, dict):
        return None

    # 区分 request（有 id）和 notification（无 id）
    request_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        return _rpc_result(request_id, _handle_initialize(request_id, params)["result"])
    elif method == "notifications/initialized":
        return None  # notification，无需响应
    elif method == "tools/list":
        return _handle_tools_list(request_id)
    elif method == "tools/call":
        return _handle_tools_call(request_id, params)
    elif method == "ping":
        return _rpc_result(request_id, {})
    else:
        if request_id is not None:
            return _rpc_error(request_id, -32601, "未知方法: %s" % method)
        return None


# ── stdio 读写 ─────────────────────────────────────────────────────────────
def _read_message() -> dict | None:
    """从 stdin 读取一行 JSON-RPC 消息。"""
    line = sys.stdin.readline()
    if not line:
        return None
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _send_message(msg: dict) -> None:
    """发送 JSON-RPC 消息到 stdout。"""
    body = json.dumps(msg, ensure_ascii=False, default=str)
    sys.stdout.write(body + "\n")
    sys.stdout.flush()


# ── 主循环 ──────────────────────────────────────────────────────────────────
def run() -> None:
    """运行 MCP 服务器（stdio 模式主循环）。"""
    while True:
        request = _read_message()
        if request is None:
            break

        # 批量消息（JSON array）
        if isinstance(request, list):
            for req in request:
                response = _handle_request(req)
                if response is not None:
                    _send_message(response)
        else:
            response = _handle_request(request)
            if response is not None:
                _send_message(response)


if __name__ == "__main__":
    run()
