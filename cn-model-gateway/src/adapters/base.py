"""Abstract base adapter for all model backends."""
from __future__ import annotations

import abc
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str          # "user" | "assistant" | "system"
    content: str
    image: str = ""    # v1.5.0: base64 / URL / file path (empty = text-only)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": self.role}
        if self.image:
            # Multimodal message: content is a list of content parts
            d["content"] = [
                {"type": "image_url", "image_url": {"url": self.image}},
                {"type": "text", "text": self.content},
            ]
        else:
            d["content"] = self.content
        return d


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
class ToolCall:
    """A single tool call from model response."""
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "arguments": self.arguments}


@dataclass
class ChatResponse:
    """A complete (non-streaming) chat response."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    duration_ms: int = 0
    tool_calls: List[ToolCall] = field(default_factory=list)  # v1.5.0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "duration_ms": self.duration_ms,
        }
        if self.tool_calls:
            d["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        return d


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

    # --- v1.5.0: Multimodal support ---

    def describe_image(self, image: str, prompt: str = "请描述这张图片",
                       *, model: Optional[str] = None, **kwargs: Any) -> ChatResponse:
        """Convenience method for image description.

        Default implementation constructs a multimodal ChatMessage.
        Subclasses may override with provider-specific logic.
        """
        msgs = [ChatMessage(role="user", content=prompt, image=image)]
        return self.chat(msgs, model=model, **kwargs)

    # --- v1.5.0: Function Calling / Tool Use ---

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tool definitions into provider-specific format.

        Default: OpenAI-compatible format (list of {type:function, function:{name,description,parameters}}).
        Subclasses may override for provider-specific differences.
        """
        formatted = []
        for tool in tools:
            formatted.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                },
            })
        return formatted

    def parse_tool_calls(self, raw: Dict[str, Any]) -> List[ToolCall]:
        """Parse tool calls from provider response.

        Default: OpenAI-compatible format (choices[0].message.tool_calls).
        Subclasses may override for provider-specific differences.
        """
        tool_calls = []
        # Navigate to message.tool_calls in OpenAI format
        message = raw.get("choices", [{}])[0].get("message", {})
        raw_calls = message.get("tool_calls", [])
        for tc in raw_calls:
            func = tc.get("function", {})
            args_str = func.get("arguments", "{}")
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except Exception:
                args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                arguments=args,
            ))
        return tool_calls

    def is_available(self) -> bool:
        """Return cached availability (refreshed by health check)."""
        return self._is_available

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} available={self._is_available}>"
