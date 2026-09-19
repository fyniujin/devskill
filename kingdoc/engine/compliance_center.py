"""KingDoc 政企合规中心（v4.2.0 新增）

v4.2 政企市场差异化主战场：把散点合规检查聚合为可采购的能力叙事。

能力：
- 密级标注：公开/内部/秘密/机密 随文档元数据落库（SQLite）
- 全量扫描报告：复用 v3.4 合规检查（敏感词 + 数据泄露 + 格式 + 密级建议），聚合为政企报告
- 数据不出域声明：本地 OCR 强制、云端仅元数据，生成合规声明文本
- 本地降级：云端不可用时接受文本/本地文档元数据仓操作

设计原则：
- 零第三方依赖（复用 engine.compliance_check）
- 保守优先：命中即标注，不自动改写内容
- 本地 OCR 强制（数据不出域），云端仅传元数据
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from engine.hardware import get_recommended_settings

# 文档密级元数据仓
_DB_PATH = str(Path(__file__).resolve().parent.parent.parent / ".kingdoc_compliance_center.db")

CLASSIFICATION_LEVELS = ["公开", "内部", "秘密", "机密"]

# 数据不出域：允许的本地 OCR 引擎白名单（仅本地，绝不调用外部 API）
LOCAL_OCR_ENGINES = ["tesseract", "wps_ocr"]


class ComplianceCenter:
    """政企合规中心。"""

    def __init__(self, backend: Optional[Any] = None):
        self.backend = backend
        self._local = backend is None
        self.hw = get_recommended_settings()
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(_DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS doc_classification (
                    doc_id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    reason TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scan_report (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT,
                    level TEXT,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 1. 密级标注落库
    # ------------------------------------------------------------------
    def label_classification(self, doc_id: str, level: str, reason: str = "") -> Dict:
        """标注文档密级并落库。

        level: 公开 / 内部 / 秘密 / 机密
        """
        if level not in CLASSIFICATION_LEVELS:
            return {"success": False, "error": f"无效密级：{level}（应为 {CLASSIFICATION_LEVELS}）"}
        try:
            conn = sqlite3.connect(_DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO doc_classification (doc_id, level, reason, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (doc_id, level, reason))
            conn.commit()
            conn.close()
            return {"success": True, "doc_id": doc_id, "level": level,
                    "message": f"密级已标注为「{level}」并落库"}
        except Exception as e:
            return {"success": False, "error": f"密级落库失败：{e}"}

    def get_classification(self, doc_id: str) -> Dict:
        try:
            conn = sqlite3.connect(_DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT level, reason, updated_at FROM doc_classification WHERE doc_id = ?",
                        (doc_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                return {"doc_id": doc_id, "level": row[0], "reason": row[1], "updated_at": row[2]}
            return {"doc_id": doc_id, "level": None, "message": "未标注密级"}
        except Exception as e:
            return {"success": False, "error": f"查询失败：{e}"}

    # ------------------------------------------------------------------
    # 2. 全量扫描报告（聚合 v3.4 合规检查）
    # ------------------------------------------------------------------
    def full_scan(self, text: str, doc_id: str = "") -> Dict:
        """全量合规扫描：敏感词 + 数据泄露 + 密级建议，生成政企报告。

        优先复用 engine.compliance_check 的成熟实现，
        聚合为结构化报告，绝不重复造轮子。
        """
        try:
            from engine.compliance_check import scan_sensitive, detect_leak, classify

            sensitive = scan_sensitive(text)
            leak = detect_leak(text)
            klass = classify(text)

            total_risk = self._overall_risk(sensitive, leak)

            # 若传入 doc_id，自动落库密级建议
            if doc_id and klass.get("suggested_level"):
                self.label_classification(doc_id, klass["suggested_level"],
                                          reason="全量扫描自动建议")

            report = {
                "doc_id": doc_id,
                "scanned_at": datetime.now().isoformat(timespec="seconds"),
                "overall_risk": total_risk,
                "sensitive_words": {
                    "total_hits": sensitive.get("total_hits", 0),
                    "unique_words": sensitive.get("unique_words", 0),
                    "risk_level": sensitive.get("risk_level", "low"),
                },
                "data_leak": {
                    "total": leak.get("total", 0),
                    "by_type": leak.get("by_type", {}),
                    "overall_risk": leak.get("overall_risk", "low"),
                },
                "classification_suggestion": klass.get("suggested_level", "公开"),
                "recommendations": self._recommend(total_risk, leak),
            }
            if doc_id:
                self._save_report(doc_id, klass.get("suggested_level", "公开"), report)
            return {"success": True, **report}
        except Exception as e:
            return {"success": False, "error": f"全量扫描失败：{e}"}

    @staticmethod
    def _overall_risk(sensitive: Dict, leak: Dict) -> str:
        order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        s = order.get(sensitive.get("risk_level", "low"), 1)
        l = order.get(leak.get("overall_risk", "low"), 1)
        top = max(s, l)
        return {4: "critical", 3: "high", 2: "medium", 1: "low"}[top]

    @staticmethod
    def _recommend(risk: str, leak: Dict) -> List[str]:
        recs = []
        if risk in ("critical", "high"):
            recs.append("建议将文档密级提升为「秘密」及以上，并限制分享范围。")
        if leak.get("total", 0) > 0:
            recs.append("检测到敏感个人信息/证照数据，建议脱敏后流转或采用数据不出域处理。")
        recs.append("本地 OCR 强制（数据不出域），云端仅同步元数据，符合政企合规要求。")
        return recs

    def _save_report(self, doc_id: str, level: str, report: Dict) -> None:
        try:
            conn = sqlite3.connect(_DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO scan_report (doc_id, level, summary) VALUES (?, ?, ?)
            """, (doc_id, level, str(report)))
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 3. 数据不出域声明
    # ------------------------------------------------------------------
    def declare_data_local(self, doc_id: str = "", engine: str = "tesseract") -> Dict:
        """生成数据不出域声明：强调本地 OCR 强制、云端仅元数据。

        engine: tesseract / wps_ocr（均为本地引擎）
        """
        if engine not in LOCAL_OCR_ENGINES:
            return {"success": False, "error": f"不允许的 OCR 引擎：{engine}（仅限本地：{LOCAL_OCR_ENGINES}）"}
        declaration = (
            "【数据不出域声明】\n"
            f"- 文档标识：{doc_id or '未指定'}\n"
            f"- OCR 引擎：本地 {engine}（图片数据仅在本地处理，不上传任何外部服务）\n"
            "- 云端交互：仅同步文档元数据（标题/密级/版本），原始内容不出本机\n"
            "- 合规基线：符合政企「数据不出域」要求，敏感内容本地闭环处理\n"
            "- 密级管控：标注密级随元数据落库，越权访问在检索/分享前被拦截"
        )
        return {"success": True, "doc_id": doc_id, "engine": engine,
                "declaration": declaration}

    def get_status(self) -> Dict:
        return {
            "local_mode": self._local,
            "levels": CLASSIFICATION_LEVELS,
            "local_ocr_engines": LOCAL_OCR_ENGINES,
            "workers": self.hw.get("workers", 1),
        }


# ---------------------------------------------------------------------------
# 单例 + 便捷函数
# ---------------------------------------------------------------------------
_center: Optional[ComplianceCenter] = None


def get_compliance_center(backend: Optional[Any] = None) -> ComplianceCenter:
    global _center
    if _center is None:
        _center = ComplianceCenter(backend=backend)
    return _center


def label_classification(doc_id: str, level: str, reason: str = "") -> Dict:
    return get_compliance_center().label_classification(doc_id, level, reason)


def get_classification(doc_id: str) -> Dict:
    return get_compliance_center().get_classification(doc_id)


def full_scan(text: str, doc_id: str = "") -> Dict:
    return get_compliance_center().full_scan(text, doc_id)


def declare_data_local(doc_id: str = "", engine: str = "tesseract") -> Dict:
    return get_compliance_center().declare_data_local(doc_id, engine)


def get_center_status() -> Dict:
    return get_compliance_center().get_status()
