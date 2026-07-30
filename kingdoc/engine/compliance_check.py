"""KingDoc 文档内容合规检查模块

自研实现，零第三方依赖（仅 Python 标准库 re）。
目标：为政企客户提供敏感词扫描、数据泄露检测、格式规范检查、密级标注。

设计原则：
- 本地降级优先：不依赖外部 AI API，纯正则+规则引擎
- 硬件自适应：大文档分块扫描，不拖累用户电脑
- 词库可更新：支持用户自定义白名单/黑名单
- 保守优先：命中即标注，不自动修改内容
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from engine.hardware import get_recommended_settings

# 词库路径（相对于 skill 根目录）
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SENSITIVE_WORDS = SKILL_ROOT / "references" / "sensitive_words.txt"
DEFAULT_FORMAT_SPEC = SKILL_ROOT / "references" / "format_spec.md"
USER_BLACKLIST = SKILL_ROOT / "references" / "user_blacklist.txt"
USER_WHITELIST = SKILL_ROOT / "references" / "user_whitelist.txt"

# 数据泄露正则（中国大陆常见）
LEAK_PATTERNS = {
    "phone": {
        "pattern": r"(?<!\d)(1[3-9]\d{9})(?!\d)",
        "label": "手机号",
        "risk": "high",
    },
    "id_card": {
        "pattern": r"(?<!\d)(\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])(?!\d)",
        "label": "身份证号",
        "risk": "critical",
    },
    "bank_card": {
        "pattern": r"(?<!\d)(\d{16,19})(?!\d)",
        "label": "银行卡号",
        "risk": "critical",
    },
    "email": {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "label": "邮箱地址",
        "risk": "medium",
    },
    "ip_address": {
        "pattern": r"(?<!\d)((?:\d{1,3}\.){3}\d{1,3})(?!\d)",
        "label": "IP地址",
        "risk": "low",
    },
}

# 密级关键词（用于自动建议密级）
CLASSIFICATION_KEYWORDS = {
    "机密": [
        "绝密", "机密", "核心机密", "最高机密", "核心秘密",
        "国家安全", "战略部署", "军事机密", "情报来源",
    ],
    "秘密": [
        "秘密", "内部秘密", "商业机密", "技术机密", "研发机密",
        "客户名单", "定价策略", "并购", "未公开财报",
    ],
    "内部": [
        "内部资料", "内部文件", "内部通知", "内部会议",
        "仅限内部", "不得外传", "内部使用",
    ],
}

# 格式规范（默认企业文档规范）
DEFAULT_FORMAT_SPEC = {
    "font_name": {"expected": "宋体", "severity": "warning"},
    "font_size_body": {"expected": "12pt", "severity": "warning"},
    "font_size_h1": {"expected": "18pt", "severity": "warning"},
    "font_size_h2": {"expected": "15pt", "severity": "warning"},
    "line_spacing": {"expected": "1.5倍行距", "severity": "info"},
    "margin_top": {"expected": "2.54cm", "severity": "info"},
    "margin_bottom": {"expected": "2.54cm", "severity": "info"},
    "margin_left": {"expected": "3.17cm", "severity": "info"},
    "margin_right": {"expected": "3.17cm", "severity": "info"},
}


# ---------------------------------------------------------------------------
# 核心检查器
# ---------------------------------------------------------------------------

class ComplianceChecker:
    """文档内容合规检查"""

    def __init__(self):
        hw = get_recommended_settings()
        self.max_chunk_chars = hw["batch_chunk"] * 200
        self._sensitive_words: Optional[List[str]] = None
        self._whitelist: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # 1. 敏感词扫描
    # ------------------------------------------------------------------

    def scan_sensitive(
        self,
        text: str,
        custom_words: Optional[List[str]] = None,
        ignore_whitelist: bool = True,
    ) -> Dict:
        """扫描敏感词，返回命中列表+位置。

        Args:
            text: 待扫描全文
            custom_words: 额外敏感词（追加到内置词库）
            ignore_whitelist: 是否跳过白名单中的词
        """
        words = self._load_sensitive_words()
        if custom_words:
            words = list(set(words + custom_words))

        whitelist = self._load_whitelist() if ignore_whitelist else []

        hits = []
        for word in words:
            if not word:
                continue
            if word in whitelist:
                continue
            # 使用 finditer 获取位置
            for m in re.finditer(re.escape(word), text, re.IGNORECASE):
                # 取上下文（前后各 10 字）
                start = max(0, m.start() - 10)
                end = min(len(text), m.end() + 10)
                context = text[start:end].replace("\n", " ")
                hits.append({
                    "word": word,
                    "position": m.start(),
                    "line": text[:m.start()].count("\n") + 1,
                    "context": f"...{context}...",
                })

        # 按位置排序
        hits.sort(key=lambda x: x["position"])

        risk_level = "critical" if len(hits) > 10 else ("high" if len(hits) > 5 else ("medium" if hits else "low"))

        return {
            "hits": hits,
            "total_hits": len(hits),
            "unique_words": len(set(h["word"] for h in hits)),
            "risk_level": risk_level,
            "scanned_chars": len(text),
        }

    # ------------------------------------------------------------------
    # 2. 数据泄露检测
    # ------------------------------------------------------------------

    def detect_leak(self, text: str) -> Dict:
        """检测数据泄露：手机号、身份证号、银行卡号、邮箱等。"""
        findings = []
        for key, cfg in LEAK_PATTERNS.items():
            for m in re.finditer(cfg["pattern"], text):
                # 简单校验：银行卡号 Luhn 算法
                if key == "bank_card" and not self._luhn_check(m.group(0)):
                    continue
                # 身份证校验码
                if key == "id_card" and not self._id_card_valid(m.group(0)):
                    continue
                start = max(0, m.start() - 5)
                end = min(len(text), m.end() + 5)
                context = text[start:end].replace("\n", " ")
                findings.append({
                    "type": key,
                    "label": cfg["label"],
                    "risk": cfg["risk"],
                    "position": m.start(),
                    "line": text[:m.start()].count("\n") + 1,
                    "masked": self._mask(m.group(0), key),
                    "context": f"...{context}...",
                })

        findings.sort(key=lambda x: x["position"])

        # 整体风险 = 最高单项风险
        risk_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        overall = "low"
        for f in findings:
            if risk_order.get(f["risk"], 0) > risk_order.get(overall, 0):
                overall = f["risk"]

        return {
            "findings": findings,
            "total": len(findings),
            "by_type": self._group_by_type(findings),
            "overall_risk": overall,
        }

    # ------------------------------------------------------------------
    # 3. 格式规范检查
    # ------------------------------------------------------------------

    def check_format(self, file_path: str) -> Dict:
        """检查文档格式规范（针对本地 DOCX/PPTX）。

        解析 XML 结构，逐项比对规范。
        """
        p = Path(file_path)
        if not p.exists():
            return {"error": f"文件不存在: {file_path}", "issues": []}

        suffix = p.suffix.lower()
        if suffix == ".docx":
            return self._check_docx_format(p)
        elif suffix == ".pptx":
            return self._check_pptx_format(p)
        elif suffix == ".txt" or suffix == ".md":
            return self._check_plain_format(p)
        else:
            return {
                "error": f"不支持的格式: {suffix}（仅支持 .docx/.pptx/.txt/.md）",
                "issues": [],
            }

    # ------------------------------------------------------------------
    # 4. 密级自动标注
    # ------------------------------------------------------------------

    def classify(self, text: str) -> Dict:
        """根据内容自动建议密级（公开/内部/秘密/机密）。"""
        scores = {"机密": 0, "秘密": 0, "内部": 0}
        matched_keywords = {"机密": [], "秘密": [], "内部": []}

        for level, keywords in CLASSIFICATION_KEYWORDS.items():
            for kw in keywords:
                count = text.count(kw)
                if count > 0:
                    scores[level] += count
                    matched_keywords[level].append(kw)

        # 取最高级别
        if scores["机密"] > 0:
            suggested = "机密"
        elif scores["秘密"] > 0:
            suggested = "秘密"
        elif scores["内部"] > 0:
            suggested = "内部"
        else:
            suggested = "公开"

        return {
            "suggested_level": suggested,
            "scores": scores,
            "matched_keywords": matched_keywords,
            "confidence": "high" if scores.get(suggested, 0) >= 3 else "medium",
        }

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _load_sensitive_words(self) -> List[str]:
        """加载敏感词库（内置 + 用户黑名单）。"""
        if self._sensitive_words is not None:
            return self._sensitive_words

        words = []
        # 内置词库
        if DEFAULT_SENSITIVE_WORDS.exists():
            try:
                content = DEFAULT_SENSITIVE_WORDS.read_text(encoding="utf-8")
                words.extend(
                    line.strip() for line in content.splitlines()
                    if line.strip() and not line.startswith("#")
                )
            except Exception:
                pass

        # 用户黑名单
        if USER_BLACKLIST.exists():
            try:
                content = USER_BLACKLIST.read_text(encoding="utf-8")
                words.extend(
                    line.strip() for line in content.splitlines()
                    if line.strip() and not line.startswith("#")
                )
            except Exception:
                pass

        self._sensitive_words = words
        return self._sensitive_words

    def _load_whitelist(self) -> List[str]:
        """加载用户白名单。"""
        if self._whitelist is not None:
            return self._whitelist

        words = []
        if USER_WHITELIST.exists():
            try:
                content = USER_WHITELIST.read_text(encoding="utf-8")
                words.extend(
                    line.strip() for line in content.splitlines()
                    if line.strip() and not line.startswith("#")
                )
            except Exception:
                pass

        self._whitelist = words
        return self._whitelist

    @staticmethod
    def _luhn_check(number: str) -> bool:
        """Luhn 算法校验银行卡号。"""
        if not number.isdigit():
            return False
        digits = [int(d) for d in number]
        digits.reverse()
        total = 0
        for i, d in enumerate(digits):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return total % 10 == 0

    @staticmethod
    def _id_card_valid(id_number: str) -> bool:
        """校验身份证号校验码。"""
        if len(id_number) != 18:
            return False
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = "10X98765432"
        try:
            total = sum(int(id_number[i]) * weights[i] for i in range(17))
            return check_codes[total % 11].upper() == id_number[17].upper()
        except (ValueError, IndexError):
            return False

    @staticmethod
    def _mask(value: str, vtype: str) -> str:
        """脱敏显示。"""
        if vtype == "phone" and len(value) == 11:
            return value[:3] + "****" + value[7:]
        if vtype == "id_card" and len(value) == 18:
            return value[:4] + "**********" + value[14:]
        if vtype == "bank_card" and len(value) >= 16:
            return value[:4] + " **** **** " + value[-4:]
        if vtype == "email":
            at = value.find("@")
            if at > 1:
                return value[0] + "***" + value[at:]
        return value[:2] + "***" + value[-2:] if len(value) > 4 else "***"

    @staticmethod
    def _group_by_type(findings: List[Dict]) -> Dict:
        result = {}
        for f in findings:
            t = f["type"]
            if t not in result:
                result[t] = {"label": f["label"], "count": 0, "risk": f["risk"]}
            result[t]["count"] += 1
        return result

    def _check_docx_format(self, path: Path) -> Dict:
        """检查 DOCX 格式（解析 XML）。"""
        import zipfile
        from xml.etree import ElementTree as ET

        issues = []
        try:
            with zipfile.ZipFile(path) as z:
                # 读取 document.xml
                with z.open("word/document.xml") as f:
                    tree = ET.parse(f)
                    root = tree.getroot()

                    # 检查字体
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    rpr_elements = root.findall(".//w:rPr", ns)
                    for rpr in rpr_elements:
                        rfonts = rpr.findall(".//w:rFonts", ns)
                        for rf in rfonts:
                            font = rf.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia")
                            if font and font != "宋体":
                                issues.append({
                                    "type": "font_name",
                                    "expected": "宋体",
                                    "actual": font,
                                    "severity": "warning",
                                    "message": f"字体应为宋体，实际为 {font}",
                                })

                    # 检查字号
                    sz_elements = root.findall(".//w:sz", ns)
                    for sz in sz_elements:
                        size_val = sz.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val")
                        if size_val:
                            # 单位是 half-points，24 = 12pt
                            pt = int(size_val) / 2
                            if pt < 10 or pt > 14:
                                issues.append({
                                    "type": "font_size",
                                    "expected": "10-14pt",
                                    "actual": f"{pt}pt",
                                    "severity": "warning",
                                    "message": f"正文字号应在 10-14pt 之间，实际为 {pt}pt",
                                })

        except Exception as e:
            issues.append({
                "type": "parse_error",
                "expected": "正常解析",
                "actual": str(e),
                "severity": "error",
                "message": f"解析 DOCX 失败: {e}",
            })

        return {
            "file": str(path),
            "format": "docx",
            "issues": issues,
            "issue_count": len(issues),
            "compliant": len(issues) == 0,
        }

    def _check_pptx_format(self, path: Path) -> Dict:
        """检查 PPTX 格式。"""
        import zipfile
        from xml.etree import ElementTree as ET

        issues = []
        try:
            with zipfile.ZipFile(path) as z:
                slide_files = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
                for sf in slide_files:
                    with z.open(sf) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
                        # 检查文本框是否为空
                        txbody_elements = root.findall(".//a:txBody", ns)
                        for txbody in txbody_elements:
                            p_elements = txbody.findall("a:p", ns)
                            has_text = False
                            for p in p_elements:
                                t_elements = p.findall(".//a:t", ns)
                                for t in t_elements:
                                    if t.text and t.text.strip():
                                        has_text = True
                                        break
                                if has_text:
                                    break
                            if not has_text:
                                issues.append({
                                    "type": "empty_textbox",
                                    "expected": "有内容",
                                    "actual": "空文本框",
                                    "severity": "info",
                                    "message": f"{sf} 中存在空文本框",
                                })
        except Exception as e:
            issues.append({
                "type": "parse_error",
                "expected": "正常解析",
                "actual": str(e),
                "severity": "error",
                "message": f"解析 PPTX 失败: {e}",
            })

        return {
            "file": str(path),
            "format": "pptx",
            "issues": issues,
            "issue_count": len(issues),
            "compliant": len(issues) == 0,
        }

    def _check_plain_format(self, path: Path) -> Dict:
        """检查纯文本/Markdown 格式。"""
        issues = []
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # 检查行长度（不超过 80 字符）
            for i, line in enumerate(lines, 1):
                if len(line) > 80:
                    issues.append({
                        "type": "line_too_long",
                        "expected": "≤80字符",
                        "actual": f"{len(line)}字符",
                        "severity": "info",
                        "message": f"第{i}行超过80字符（{len(line)}字符）",
                    })

            # 检查是否包含标题层级（Markdown）
            if path.suffix == ".md":
                h1_count = sum(1 for l in lines if l.startswith("# "))
                if h1_count == 0 and len(lines) > 10:
                    issues.append({
                        "type": "missing_h1",
                        "expected": "至少1个 H1 标题",
                        "actual": "无 H1 标题",
                        "severity": "warning",
                        "message": "长文档缺少 H1 标题",
                    })

        except Exception as e:
            issues.append({
                "type": "parse_error",
                "expected": "正常解析",
                "actual": str(e),
                "severity": "error",
                "message": f"读取文件失败: {e}",
            })

        return {
            "file": str(path),
            "format": path.suffix.lstrip("."),
            "issues": issues,
            "issue_count": len(issues),
            "compliant": len(issues) == 0,
        }


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------

_checker = None


def _get() -> ComplianceChecker:
    global _checker
    if _checker is None:
        _checker = ComplianceChecker()
    return _checker


def scan_sensitive(text: str, custom_words: Optional[List[str]] = None) -> Dict:
    return _get().scan_sensitive(text, custom_words)


def detect_leak(text: str) -> Dict:
    return _get().detect_leak(text)


def check_format(file_path: str) -> Dict:
    return _get().check_format(file_path)


def classify(text: str) -> Dict:
    return _get().classify(text)
