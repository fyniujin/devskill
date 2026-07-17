"""WPS AI 适配器 — 统一接口 + 能力路由

设计：
- 本地降级优先，自研逻辑实现
- 未来如 WPS AI 开放 API，只需新增后端，无需改此文件
- 所有方法异步安全，可集成到 MCP Server
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional

# 确保能 import engine 包
_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from engine.wps_ai.backends.local_fallback import LocalFallbackBackend
from engine.wps_ai.capabilities import detect_intent, get_capability_list


class WpsAiAdapter:
    """WPS AI 适配器 — 统一入口"""

    def __init__(self):
        self._local = LocalFallbackBackend()
        self._backends = {"local": self._local}
        # 预留：未来可加载 open_api / com_automation / web_api 后端
        self._active_backend = "local"

    def write(self, text: str, action: str = "polish", **kwargs) -> Dict:
        """AI 写作辅助"""
        return self._backends[self._active_backend].write(text, action, **kwargs)

    def analyze(self, data, question: str, **kwargs) -> Dict:
        """AI 数据分析"""
        return self._backends[self._active_backend].analyze(data, question, **kwargs)

    def ppt(self, outline: str, **kwargs) -> Dict:
        """AI PPT 生成"""
        return self._backends[self._active_backend].ppt(outline, **kwargs)

    def read(self, content: str, action: str = "summarize", **kwargs) -> Dict:
        """AI 阅读助手"""
        return self._backends[self._active_backend].read(content, action, **kwargs)

    def detect_intent(self, user_input: str) -> Optional[tuple]:
        """检测用户意图"""
        return detect_intent(user_input)

    def get_capabilities(self):
        """获取能力清单"""
        return get_capability_list()


# 全局单例
_adapter: Optional[WpsAiAdapter] = None


def get_adapter() -> WpsAiAdapter:
    """获取 WPS AI 适配器单例"""
    global _adapter
    if _adapter is None:
        _adapter = WpsAiAdapter()
    return _adapter
