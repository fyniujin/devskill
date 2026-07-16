"""Abstract base adapter for all model backends."""
from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str          # "user" | "assistant" | "system"
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ContentChunk:
    """A single content chunk in a streaming response (MCP standard)."""
    type: str = "text"
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": self.type, "text": self.text}
        if self.metadata:
            d["metadata"] = self.metadata
        return d


@dataclass
class ChatResponse:
    """A complete (non-streaming) chat response."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "duration_ms": self.duration_ms,
        }


class BaseAdapter(abc.ABC):
    """All model adapters must inherit from this."""

    provider_name: str = ""
    default_model: str = ""

    def __init__(self, api_key: str, **kwargs: Any) -> None:
        if not api_key:
            raise ValueError(
                f"[{self.provider_name}] API key is empty. "
                f"请在 config.json 中填写 {self.provider_name} 的 api_key。"
            )
        self.api_key = api_key
        self.extra_config = kwargs
        self._last_health_check: Optional[float] = None
        self._is_available: bool = True

    @abc.abstractmethod
    def chat(self, messages: List[ChatMessage], *,
             model: Optional[str] = None, **kwargs: Any) -> ChatResponse:
        """Send a non-streaming chat request. Returns full response."""
        ...

    @abc.abstractmethod
    def stream_chat(self, messages: List[ChatMessage], *,
                    model: Optional[str] = None, **kwargs: Any) -> Generator[ContentChunk, None, None]:
        """Send a streaming chat request. Yields content chunks."""
        ...

    @abc.abstractmethod
    def check_health(self) -> bool:
        """Check if the API key is valid and service is reachable."""
        ...

    def is_available(self) -> bool:
        """Return cached availability (refreshed by health check)."""
        return self._is_available

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} available={self._is_available}>"
