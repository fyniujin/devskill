"""HunYuan (Tencent Cloud) model adapter - https://hunyuan.tencentcloudapi.com"""
from __future__ import annotations

import json
import hashlib
import hmac
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Generator, List, Optional

from .base import BaseAdapter, ChatMessage, ChatResponse, ContentChunk


# HunYuan uses a special signing mechanism, not simple Bearer token
API_HOST = "hunyuan.tencentcloudapi.com"
API_ACTION = "ChatCompletions"
API_VERSION = "2023-09-01"
API_REGION = "ap-guangzhou"


class HunYuanAdapter(BaseAdapter):
    provider_name = "hunyuan"
    default_model = "hunyuan-standard"

    def __init__(self, api_key: str, **kwargs: Any) -> None:
        # For HunYuan, api_key is "secret_id:secret_key"
        if ":" not in api_key:
            raise ValueError(
                "[HunYuan] api_key 格式错误。应为 'secret_id:secret_key'（用冒号分隔）。"
                "请在 config.json 中按 'YOUR_SECRET_ID:YOUR_SECRET_KEY' 格式填写。"
            )
        parts = api_key.split(":", 1)
        self.secret_id = parts[0].strip()
        self.secret_key = parts[1].strip()
        super().__init__(api_key, **kwargs)

    def _sign(self, payload: str, timestamp: int) -> str:
        """HunYuan TC3-HMAC-SHA256 signing."""
        canonical_headers = f"content-type:application/json\nhost:{API_HOST}\n"
        signed_headers = "content-type;host"
        hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            f"POST\n/\n\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{hashed_payload}"
        )
        date = time.gmtime(timestamp)[:6]
        date_str = time.strftime("%Y-%m-%d", time.struct_time(date))
        credential_scope = f"{date_str}/hunyuan/tc3_request"
        hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = (
            f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashed_canonical}"
        )
        secret_date = hmac.new(
            f"TC3{self.secret_key}".encode("utf-8"), date_str.encode("utf-8"), hashlib.sha256
        ).digest()
        secret_service = hmac.new(secret_date, b"hunyuan", hashlib.sha256).digest()
        secret_signing = hmac.new(secret_service, b"tc3_request", hashlib.sha256).digest()
        return hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    def _build_headers(self, payload_str: str) -> Dict[str, str]:
        timestamp = int(time.time())
        signature = self._sign(payload_str, timestamp)
        return {
            "Content-Type": "application/json",
            "Host": API_HOST,
            "X-TC-Action": API_ACTION,
            "X-TC-Version": API_VERSION,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": API_REGION,
            "X-TC-Authorization": (
                f"TC3-HMAC-SHA256 Credential={self.secret_id}/"
                f"{time.strftime('%Y-%m-%d', time.gmtime(timestamp))}/hunyuan/tc3_request, "
                f"SignedHeaders=content-type;host, Signature={signature}"
            ),
        }

    def _build_payload(self, messages: List[ChatMessage], model: str,
                       stream: bool = False, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "Model": model,
            "Messages": [{"Role": m.role, "Content": m.content} for m in messages],
            "Stream": stream,
        }
        for key in ("Temperature", "TopP", "MaxLength"):
            if key.lower() in kwargs and kwargs[key.lower()] is not None:
                payload[key] = kwargs[key.lower()]
        return payload

    def chat(self, messages: List[ChatMessage], *,
             model: Optional[str] = None, **kwargs: Any) -> ChatResponse:
        m = model or self.default_model
        start = self._now_ms()
        payload = self._build_payload(messages, m, stream=False, **kwargs)
        payload_str = json.dumps(payload, ensure_ascii=False)
        headers = self._build_headers(payload_str)
        req = urllib.request.Request(
            f"https://{API_HOST}", data=payload_str.encode("utf-8"),
            headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"[HunYuan] HTTP {e.code}: {body[:200]}。请检查 secret_id/secret_key 是否正确。"
            ) from e
        except Exception as e:
            raise RuntimeError(f"[HunYuan] 网络错误: {e}") from e

        response = raw.get("Response", {})
        usage = response.get("Usage", {})
        usage_map = {
            "prompt_tokens": usage.get("PromptTokens", 0),
            "completion_tokens": usage.get("CompletionTokens", 0),
            "total_tokens": usage.get("TotalTokens", 0),
        }
        try:
            text = response["Choices"][0]["Message"]["Content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"[HunYuan] 解析响应失败: {response}") from e

        self._is_available = True
        return ChatResponse(
            content=text, model=m, provider=self.provider_name,
            usage=usage_map,
            finish_reason=response.get("Choices", [{}])[0].get("FinishReason", "stop"),
            duration_ms=self._now_ms() - start,
        )

    def stream_chat(self, messages: List[ChatMessage], *,
                    model: Optional[str] = None, **kwargs: Any) -> Generator[ContentChunk, None, None]:
        m = model or self.default_model
        payload = self._build_payload(messages, m, stream=True, **kwargs)
        payload_str = json.dumps(payload, ensure_ascii=False)
        headers = self._build_headers(payload_str)
        req = urllib.request.Request(
            f"https://{API_HOST}", data=payload_str.encode("utf-8"),
            headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    line = line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "":
                        continue
                    try:
                        chunk = json.loads(data)
                        chunk_resp = chunk.get("Response", {})
                        choices = chunk_resp.get("Choices", [{}])
                        if choices:
                            delta = choices[0].get("Delta", {})
                            content = delta.get("Content", "")
                            if content:
                                yield ContentChunk(type="text", text=content,
                                                   metadata={"provider": self.provider_name, "model": m})
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"[HunYuan] 流式 HTTP {e.code}: {body[:200]}") from e

    def check_health(self) -> bool:
        try:
            msgs = [ChatMessage(role="user", content="hi")]
            self.chat(msgs, max_tokens=1)
            self._is_available = True
        except Exception:
            self._is_available = False
        self._last_health_check = self._now_ms()
        return self._is_available
