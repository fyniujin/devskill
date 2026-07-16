"""Model router with unified error mapping."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Type

from .adapters.base import BaseAdapter, ChatMessage, ChatResponse, ContentChunk


# MCP standard error codes
ERROR_PARAM_INVALID = -32602
ERROR_MODEL_UNAVAILABLE = -32001
ERROR_RATE_LIMITED = -32002
ERROR_INTERNAL = -32603
ERROR_PROVIDER_NOT_FOUND = -32000


# Provider-specific error patterns → MCP error codes
ERROR_MAP: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "invalid_api_key": {"code": ERROR_PARAM_INVALID, "message": "DeepSeek API key 无效或已过期"},
        "insufficient_quota": {"code": ERROR_RATE_LIMITED, "message": "DeepSeek 额度不足"},
        "rate_limit": {"code": ERROR_RATE_LIMITED, "message": "DeepSeek 请求过于频繁，请稍后重试"},
    },
    "tongyi": {
        "InvalidApiKey": {"code": ERROR_PARAM_INVALID, "message": "通义 API key 无效"},
        "Throttling.RateLimit": {"code": ERROR_RATE_LIMITED, "message": "通义 请求频率超限"},
        "Throttling": {"code": ERROR_RATE_LIMITED, "message": "通义 请求被限流"},
    },
    "zhipu": {
        "data_inspection_failed": {"code": ERROR_PARAM_INVALID, "message": "智谱 内容审核未通过，请检查输入内容"},
        "invalid_api_key": {"code": ERROR_PARAM_INVALID, "message": "智谱 API key 无效"},
        "rate_limit_reached": {"code": ERROR_RATE_LIMITED, "message": "智谱 请求频率超限"},
    },
    "kimi": {
        "invalid_api_key": {"code": ERROR_PARAM_INVALID, "message": "Kimi API key 无效"},
        "rate_limit_exceeded": {"code": ERROR_RATE_LIMITED, "message": "Kimi 请求频率超限"},
        "content_blocked": {"code": ERROR_PARAM_INVALID, "message": "Kimi 内容审核未通过"},
    },
    "hunyuan": {
        "AuthFailure.SecretIdNotFound": {"code": ERROR_PARAM_INVALID, "message": "混元 SecretId 无效"},
        "AuthFailure.SignatureFailure": {"code": ERROR_PARAM_INVALID, "message": "混元 签名失败，请检查 SecretKey"},
        "LimitExceeded": {"code": ERROR_RATE_LIMITED, "message": "混元 请求频率超限"},
    },
    "doubao": {
        "AuthenticationError": {"code": ERROR_PARAM_INVALID, "message": "豆包 API key 无效或 endpoint_id 错误"},
        "RateLimitError": {"code": ERROR_RATE_LIMITED, "message": "豆包 请求频率超限"},
        "BadRequestError": {"code": ERROR_PARAM_INVALID, "message": "豆包 请求参数错误"},
    },
}


class ModelRouter:
    """Routes requests to the correct model adapter with error mapping."""

    PROVIDER_REGISTRY: Dict[str, Type[BaseAdapter]] = {}

    def __init__(self) -> None:
        self._adapters: Dict[str, BaseAdapter] = {}

    def register_adapter(self, provider: str, adapter: BaseAdapter) -> None:
        self._adapters[provider] = adapter

    def register_all(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Initialize all adapters from config. Returns availability map."""
        from .adapters import (
            DeepSeekAdapter, TongYiAdapter, ZhiPuAdapter,
            KimiAdapter, HunYuanAdapter, DouBaoAdapter,
        )
        mapping: Dict[str, Type[BaseAdapter]] = {
            "deepseek": DeepSeekAdapter,
            "tongyi": TongYiAdapter,
            "zhipu": ZhiPuAdapter,
            "kimi": KimiAdapter,
            "hunyuan": HunYuanAdapter,
            "doubao": DouBaoAdapter,
        }
        availability: Dict[str, bool] = {}
        for provider, cls in mapping.items():
            provider_cfg = config.get(provider, {})
            api_key = provider_cfg.get("api_key", "")
            if not api_key:
                availability[provider] = False
                continue
            try:
                adapter = cls(api_key, **{k: v for k, v in provider_cfg.items() if k != "api_key"})
                self.register_adapter(provider, adapter)
                availability[provider] = True
            except Exception:
                availability[provider] = False
        return availability

    def get_adapter(self, provider: str) -> Optional[BaseAdapter]:
        return self._adapters.get(provider)

    def list_available(self) -> List[str]:
        return [p for p, a in self._adapters.items() if a.is_available()]

    def auto_select(self) -> Optional[str]:
        """Pick a random available provider."""
        available = self.list_available()
        if not available:
            return None
        return random.choice(available)

    def chat(self, messages: List[ChatMessage], provider: Optional[str] = None,
             **kwargs: Any) -> ChatResponse:
        p = provider or self.auto_select()
        if not p:
            raise RuntimeError(
                f"没有可用的模型提供商。请在 config.json 中至少填写一家的 api_key。"
                f"当前已配置: {list(self._adapters.keys())}"
            )
        adapter = self._adapters.get(p)
        if not adapter:
            raise RuntimeError(
                f"未知的模型提供商: {p}。支持的提供商: {list(self._adapters.keys())}"
            )
        try:
            return adapter.chat(messages, **kwargs)
        except RuntimeError:
            raise
        except Exception as e:
            raise self._map_error(p, str(e))

    def stream_chat(self, messages: List[ChatMessage], provider: Optional[str] = None,
                    **kwargs: Any):
        p = provider or self.auto_select()
        if not p:
            raise RuntimeError("没有可用的模型提供商。")
        adapter = self._adapters.get(p)
        if not adapter:
            raise RuntimeError(f"未知的模型提供商: {p}")
        try:
            yield from adapter.stream_chat(messages, **kwargs)
        except RuntimeError:
            raise
        except Exception as e:
            raise self._map_error(p, str(e))

    def _map_error(self, provider: str, error_msg: str) -> RuntimeError:
        """Map provider-specific errors to unified MCP error codes."""
        provider_map = ERROR_MAP.get(provider, {})
        for pattern, info in provider_map.items():
            if pattern.lower() in error_msg.lower():
                return RuntimeError(f"[MCP {info['code']}] {info['message']}")
        return RuntimeError(f"[MCP {ERROR_INTERNAL}] {provider} 调用失败: {error_msg}")

    def compare_models(self, messages: List[ChatMessage],
                       providers: Optional[List[str]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Send the same question to multiple providers and return comparison."""
        targets = providers or self.list_available()
        results: Dict[str, Any] = {}
        for p in targets:
            adapter = self._adapters.get(p)
            if not adapter or not adapter.is_available():
                results[p] = {"error": "不可用"}
                continue
            try:
                resp = adapter.chat(messages, **kwargs)
                results[p] = {
                    "content": resp.content,
                    "model": resp.model,
                    "duration_ms": resp.duration_ms,
                    "usage": resp.usage,
                }
            except Exception as e:
                results[p] = {"error": str(e)}
        return results
