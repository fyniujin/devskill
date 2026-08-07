"""Model router with unified error mapping and failover support."""
from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, List, Optional, Type

from .adapters.base import BaseAdapter, ChatMessage, ChatResponse, ContentChunk


# MCP standard error codes
ERROR_PARAM_INVALID = -32602
ERROR_MODEL_UNAVAILABLE = -32001
ERROR_RATE_LIMITED = -32002
ERROR_INTERNAL = -32603
ERROR_PROVIDER_NOT_FOUND = -32000


# Environment variable names for API keys (security improvement v1.4.0)
ENV_KEY_MAP: Dict[str, str] = {
    "deepseek": "DEEPSEEK_API_KEY",
    "tongyi": "DASHSCOPE_API_KEY",
    "zhipu": "ZHIPU_API_KEY",
    "kimi": "KIMI_API_KEY",
    "hunyuan": "HUNYUAN_SECRET_ID",  # 混元需要 SECRET_ID:SECRET_KEY 格式
    "doubao": "DOUBAO_API_KEY",
    "minimax": "MINIMAX_API_KEY",
    "lingyi": "LINGYI_API_KEY",
    "baichuan": "BAICHUAN_API_KEY",
    "stepfun": "STEPFUN_API_KEY",
}

# Health check cache TTL (seconds)
HEALTH_CHECK_CACHE_TTL = 60


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
    "minimax": {
        "api_key_invalid": {"code": ERROR_PARAM_INVALID, "message": "MiniMax API key 无效"},
        "insufficient_balance": {"code": ERROR_RATE_LIMITED, "message": "MiniMax 余额不足"},
        "rate_limit": {"code": ERROR_RATE_LIMITED, "message": "MiniMax 请求频率超限"},
    },
    "lingyi": {
        "invalid_token": {"code": ERROR_PARAM_INVALID, "message": "零一万物 API key 无效"},
        "rate_limit_exceeded": {"code": ERROR_RATE_LIMITED, "message": "零一万物 请求频率超限"},
        "content_filter": {"code": ERROR_PARAM_INVALID, "message": "零一万物 内容审核未通过"},
    },
    "baichuan": {
        "invalid_apikey": {"code": ERROR_PARAM_INVALID, "message": "百川智能 API key 无效"},
        "quota_exceeded": {"code": ERROR_RATE_LIMITED, "message": "百川智能 额度不足"},
        "rate_limit": {"code": ERROR_RATE_LIMITED, "message": "百川智能 请求频率超限"},
    },
    "stepfun": {
        "auth_failed": {"code": ERROR_PARAM_INVALID, "message": "阶跃星辰 API key 无效"},
        "rate_limit": {"code": ERROR_RATE_LIMITED, "message": "阶跃星辰 请求频率超限"},
        "invalid_param": {"code": ERROR_PARAM_INVALID, "message": "阶跃星辰 请求参数错误"},
    },
}


class ModelRouter:
    """Routes requests to the correct model adapter with error mapping and failover."""

    PROVIDER_REGISTRY: Dict[str, Type[BaseAdapter]] = {}

    def __init__(self, timeout: int = 30, failover: bool = True) -> None:
        self._adapters: Dict[str, BaseAdapter] = {}
        self._timeout = timeout
        self._failover = failover
        # Capability score cache (loaded from benchmark.db)
        self._capability_scores: Dict[str, float] = {}
        # Health check cache {provider: (timestamp, result)}
        self._health_cache: Dict[str, tuple] = {}
        # Load capability scores from benchmark database
        self._load_capability_scores()

    def register_adapter(self, provider: str, adapter: BaseAdapter) -> None:
        self._adapters[provider] = adapter

    def register_all(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Initialize all adapters from config. Returns availability map.

        API key resolution order:
        1. Environment variable (PROVIDER_API_KEY)
        2. config.json api_key field (fallback for backward compatibility)
        """
        from .adapters import (
            DeepSeekAdapter, TongYiAdapter, ZhiPuAdapter,
            KimiAdapter, HunYuanAdapter, DouBaoAdapter,
            MiniMaxAdapter, LingYiAdapter, BaichuanAdapter, StepFunAdapter,
        )
        mapping: Dict[str, Type[BaseAdapter]] = {
            "deepseek": DeepSeekAdapter,
            "tongyi": TongYiAdapter,
            "zhipu": ZhiPuAdapter,
            "kimi": KimiAdapter,
            "hunyuan": HunYuanAdapter,
            "doubao": DouBaoAdapter,
            "minimax": MiniMaxAdapter,
            "lingyi": LingYiAdapter,
            "baichuan": BaichuanAdapter,
            "stepfun": StepFunAdapter,
        }
        availability: Dict[str, bool] = {}
        for provider, cls in mapping.items():
            provider_cfg = config.get(provider, {})
            # Priority 1: Environment variable
            env_key = ENV_KEY_MAP.get(provider, "")
            api_key = os.environ.get(env_key, "") if env_key else ""
            # Priority 2: config.json (fallback)
            if not api_key:
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
        """Pick the best available provider using capability + health scoring.

        Scoring: capability_score (0-1) * health_status (0 or 1)
        Returns the highest-scored available provider.
        """
        available = self.list_available()
        if not available:
            return None

        # Score each provider
        scored: List[tuple] = []
        for provider in available:
            score = self._get_capability_score(provider) * (1 if self._check_health_cached(provider) else 0)
            scored.append((provider, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    def chat(self, messages: List[ChatMessage], provider: Optional[str] = None,
             **kwargs: Any) -> ChatResponse:
        """Send chat request with automatic failover support.

        If failover is enabled, tries providers in capability order until success.
        """
        if provider:
            # Explicit provider, no failover
            return self._chat_with_provider(messages, provider, **kwargs)

        # Auto mode: try providers in capability order
        if not self._failover:
            return self._chat_with_provider(messages, self.auto_select(), **kwargs)

        # Failover mode: try each provider until success
        sorted_providers = self._get_sorted_providers()
        last_error: Optional[Exception] = None

        for p in sorted_providers:
            try:
                return self._chat_with_provider(messages, p, **kwargs)
            except Exception as e:
                last_error = e
                # Continue to next provider
                continue

        raise RuntimeError(
            f"所有模型提供商均调用失败。已尝试: {sorted_providers}。"
            f"最后错误: {last_error}"
        )

    def stream_chat(self, messages: List[ChatMessage], provider: Optional[str] = None,
                    **kwargs: Any):
        """Send streaming chat request with failover support."""
        if provider:
            yield from self._stream_with_provider(messages, provider, **kwargs)
            return

        if not self._failover:
            yield from self._stream_with_provider(messages, self.auto_select(), **kwargs)
            return

        # Failover mode
        sorted_providers = self._get_sorted_providers()
        last_error: Optional[Exception] = None

        for p in sorted_providers:
            try:
                yield from self._stream_with_provider(messages, p, **kwargs)
                return  # Success, stop iterating
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(
            f"所有模型提供商均调用失败。已尝试: {sorted_providers}。"
            f"最后错误: {last_error}"
        )

    def _chat_with_provider(self, messages: List[ChatMessage], provider: str,
                            **kwargs: Any) -> ChatResponse:
        """Internal: chat with a specific provider."""
        adapter = self._adapters.get(provider)
        if not adapter:
            raise RuntimeError(
                f"未知的模型提供商: {provider}。支持的提供商: {list(self._adapters.keys())}"
            )
        try:
            return adapter.chat(messages, **kwargs)
        except RuntimeError:
            raise
        except Exception as e:
            raise self._map_error(provider, str(e))

    def _stream_with_provider(self, messages: List[ChatMessage], provider: str,
                              **kwargs: Any):
        """Internal: stream chat with a specific provider."""
        adapter = self._adapters.get(provider)
        if not adapter:
            raise RuntimeError(f"未知的模型提供商: {provider}")
        try:
            yield from adapter.stream_chat(messages, **kwargs)
        except RuntimeError:
            raise
        except Exception as e:
            raise self._map_error(provider, str(e))

    def _get_sorted_providers(self) -> List[str]:
        """Get providers sorted by capability score and health status."""
        available = self.list_available()
        scored: List[tuple] = []
        for provider in available:
            score = self._get_capability_score(provider) * (1 if self._check_health_cached(provider) else 0)
            scored.append((provider, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored]

    def _load_capability_scores(self) -> None:
        """Load capability scores from benchmark database."""
        try:
            import sqlite3
            from pathlib import Path
            db_path = str(Path.home() / ".cn-model-gateway" / "benchmark.db")
            if not Path(db_path).exists():
                return
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    "SELECT provider, AVG(score) as avg_score "
                    "FROM benchmark_results GROUP BY provider"
                ).fetchall()
            for row in rows:
                self._capability_scores[row[0]] = row[1]
        except Exception:
            pass

    def _get_capability_score(self, provider: str) -> float:
        """Get capability score for a provider (0-1). Default 0.5 if unknown."""
        return self._capability_scores.get(provider, 0.5)

    def _check_health_cached(self, provider: str) -> bool:
        """Check provider health with caching."""
        now = time.time()
        if provider in self._health_cache:
            timestamp, result = self._health_cache[provider]
            if now - timestamp < HEALTH_CHECK_CACHE_TTL:
                return result
        # Perform health check
        adapter = self._adapters.get(provider)
        if not adapter:
            return False
        try:
            result = adapter.check_health()
        except Exception:
            result = False
        self._health_cache[provider] = (now, result)
        return result

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
