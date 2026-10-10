"""KingDoc 政企合规中心（v4.3.0 起委托 compliance_suite）

v4.2 的 ComplianceCenter / label_classification / get_classification / full_scan /
declare_data_local / get_center_status 现已收敛为 engine.compliance_suite.ComplianceSuite
门面下的能力，本模块仅作兼容委托层，避免双入口维护。

设计原则：零第三方依赖（复用 engine.compliance_suite），本地降级优先。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from engine.compliance_suite import (
    ComplianceSuite,
    ComplianceCore,
    CLASSIFICATION_LEVELS,
    LOCAL_OCR_ENGINES,
)

_SUITE: Optional[ComplianceSuite] = None


def _suite_inst() -> ComplianceSuite:
    global _SUITE
    if _SUITE is None:
        _SUITE = ComplianceSuite()
    return _SUITE


class ComplianceCenter:
    """兼容别名：委托 ComplianceSuite 门面（v4.3.0 单入口）。"""

    def __init__(self, backend: Optional[Any] = None):
        self._s = ComplianceSuite(backend=backend)

    def label_classification(self, doc_id: str, level: str, reason: str = "") -> Dict:
        return self._s.core.label_classification(doc_id, level, reason)

    def get_classification(self, doc_id: str) -> Dict:
        return self._s.core.get_classification(doc_id)

    def full_scan(self, text: str, doc_id: str = "") -> Dict:
        return self._s.full_scan(text, doc_id)

    def declare_data_local(self, doc_id: str = "", engine: str = "tesseract") -> Dict:
        return self._s.core.declare_data_local(doc_id, engine)

    def get_status(self) -> Dict:
        return self._s.get_status()


def get_compliance_center(backend: Optional[Any] = None) -> ComplianceCenter:
    return ComplianceCenter(backend=backend)


def label_classification(doc_id: str, level: str, reason: str = "") -> Dict:
    return _suite_inst().core.label_classification(doc_id, level, reason)


def get_classification(doc_id: str) -> Dict:
    return _suite_inst().core.get_classification(doc_id)


def full_scan(text: str, doc_id: str = "") -> Dict:
    return _suite_inst().full_scan(text, doc_id)


def declare_data_local(doc_id: str = "", engine: str = "tesseract") -> Dict:
    return _suite_inst().core.declare_data_local(doc_id, engine)


def get_center_status() -> Dict:
    return _suite_inst().get_status()
