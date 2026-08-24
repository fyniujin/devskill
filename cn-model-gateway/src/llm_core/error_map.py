"""Unified error mapping for llm-core shared kernel.

Maps provider-specific errors to MCP standard error codes.
"""
from __future__ import annotations

from typing import Dict

# MCP standard error codes
ERROR_PARAM_INVALID = -32602
ERROR_MODEL_UNAVAILABLE = -32001
ERROR_RATE_LIMITED = -32002
ERROR_INTERNAL = -32603
ERROR_PROVIDER_NOT_FOUND = -32000

# Provider-specific error patterns → MCP error codes
ERROR_MAP: Dict[str, Dict[str, Dict[str, str]]] = {
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


def map_error(provider: str, error_msg: str) -> str:
    """Map provider-specific errors to unified MCP error codes."""
    provider_map = ERROR_MAP.get(provider, {})
    for pattern, info in provider_map.items():
        if pattern.lower() in error_msg.lower():
            return f"[MCP {info['code']}] {info['message']}"
    return f"[MCP {ERROR_INTERNAL}] {provider} 调用失败: {error_msg}"
