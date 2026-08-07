#!/usr/bin/env python3
"""
bilingual_aligner.py v5.0
中英文双语合同对齐引擎
功能：段落对齐算法、版本不一致检测、优先级标注
v5.0 新增：多语言合同支持（中英双语对照审查）
"""

import hashlib
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
GLOSSARY_FILE = Path(__file__).resolve().parent.parent / "references" / "bilingual_glossary.yaml"


class BilingualAligner:
    """双语对齐引擎 — 段落匹配 + 不一致检测"""

    def __init__(self, glossary_file: Optional[Path] = None):
        self.glossary_file = glossary_file or GLOSSARY_FILE
        self._glossary: List[Dict[str, str]] = []
        self._zh_to_en: Dict[str, str] = {}
        self._en_to_zh: Dict[str, str] = {}
        self._load_glossary()

    # ---------- 加载 ----------
    def _load_glossary(self):
        if not self.glossary_file.exists():
            logger.warning(f"术语对照表不存在: {self.glossary_file}")
            return
        try:
            import yaml
            with open(self.glossary_file, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self._glossary = data.get("terms", [])
            for t in self._glossary:
                zh = t.get("zh", "").strip()
                en = t.get("en", "").strip()
                if zh and en:
                    self._zh_to_en[zh] = en
                    self._en_to_zh[en.lower()] = zh
            logger.debug(f"术语对照表加载成功，共 {len(self._glossary)} 条")
        except ImportError:
            logger.warning("未安装 pyyaml，无法读取术语对照表")
        except Exception as e:
            logger.warning(f"术语对照表加载失败: {e}")

    # ---------- 段落分割 ----------
    def split_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """将合同文本分割为段落，保留条款编号"""
        paragraphs = []
        # 按换行分割，过滤空行
        raw_paras = [p.strip() for p in text.split('\n') if p.strip()]

        for i, para in enumerate(raw_paras):
            # 提取条款编号
            clause_id = self._extract_clause_id(para)
            paragraphs.append({
                "index": i,
                "text": para,
                "clause_id": clause_id,
                "is_clause": bool(clause_id),
            })

        return paragraphs

    def _extract_clause_id(self, text: str) -> Optional[str]:
        """提取条款编号（归一化为阿拉伯数字，便于中英对照）"""
        # 匹配"第X条"、"第X款"、"Article X"、"Section X"等
        patterns = [
            (r'第([一二三四五六七八九十百\d]+)条', '第{}条'),
            (r'第([一二三四五六七八九十百\d]+)款', '第{}款'),
            (r'Article\s+(\d+)', '第{}条'),
            (r'Section\s+(\d+)', '第{}条'),
            (r'^(\d+)[\.、]', '第{}条'),
        ]
        for p, fmt in patterns:
            m = re.search(p, text)
            if m:
                num = m.group(1)
                # 中文数字转阿拉伯数字
                cn_nums = {'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10','百':'100'}
                if num in cn_nums:
                    num = cn_nums[num]
                return fmt.format(num)
        return None

    # ---------- 段落对齐 ----------
    def align_paragraphs(
        self,
        zh_paragraphs: List[Dict[str, Any]],
        en_paragraphs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        对齐中英文段落
        返回对齐结果列表，每个元素包含 zh、en 和匹配分数
        """
        aligned = []
        used_en = set()

        # 第一轮：按条款编号精确匹配
        zh_with_id = {p["clause_id"]: p for p in zh_paragraphs if p["clause_id"]}
        en_with_id = {p["clause_id"]: p for p in en_paragraphs if p["clause_id"]}

        for clause_id, zh_p in zh_with_id.items():
            if clause_id in en_with_id:
                en_p = en_with_id[clause_id]
                aligned.append({
                    "type": "matched",
                    "clause_id": clause_id,
                    "zh": zh_p["text"],
                    "en": en_p["text"],
                    "match_score": 1.0,
                    "match_method": "clause_id",
                })
                used_en.add(en_p["index"])
            else:
                aligned.append({
                    "type": "zh_only",
                    "clause_id": clause_id,
                    "zh": zh_p["text"],
                    "en": "",
                    "match_score": 0,
                    "match_method": "none",
                })

        # 第二轮：按顺序和相似度匹配剩余段落
        unmatched_zh = [p for p in zh_paragraphs if p["clause_id"] not in zh_with_id]
        unmatched_en = [p for p in en_paragraphs if p["index"] not in used_en]

        # 使用位置 + 术语相似度进行匹配
        for zh_p in unmatched_zh:
            best_match = None
            best_score = 0

            for en_p in unmatched_en:
                score = self._similarity_score(zh_p["text"], en_p["text"])
                # 位置权重：越接近的位置分数越高
                pos_weight = 1.0 - abs(zh_p["index"] - en_p["index"]) / max(len(zh_paragraphs), len(en_paragraphs))
                score = score * 0.7 + pos_weight * 0.3

                if score > best_score and score > 0.3:
                    best_score = score
                    best_match = en_p

            if best_match:
                aligned.append({
                    "type": "matched",
                    "clause_id": zh_p["clause_id"] or f"pos_{zh_p['index']}",
                    "zh": zh_p["text"],
                    "en": best_match["text"],
                    "match_score": round(best_score, 3),
                    "match_method": "similarity",
                })
                unmatched_en.remove(best_match)
            else:
                aligned.append({
                    "type": "zh_only",
                    "clause_id": zh_p["clause_id"] or f"pos_{zh_p['index']}",
                    "zh": zh_p["text"],
                    "en": "",
                    "match_score": 0,
                    "match_method": "none",
                })

        # 英文剩余段落（中文没有的）
        for en_p in unmatched_en:
            aligned.append({
                "type": "en_only",
                "clause_id": en_p["clause_id"] or f"pos_{en_p['index']}",
                "zh": "",
                "en": en_p["text"],
                "match_score": 0,
                "match_method": "none",
            })

        return aligned

    def _similarity_score(self, zh_text: str, en_text: str) -> float:
        """计算中英文段落相似度（基于术语翻译匹配）"""
        if not zh_text or not en_text:
            return 0.0

        # 统计匹配的术语数
        matched_terms = 0
        for zh_term, en_term in self._zh_to_en.items():
            if zh_term in zh_text and en_term.lower() in en_text.lower():
                matched_terms += 1

        # 基于术语数量计算分数
        total_terms = max(len(self._glossary), 1)
        term_score = matched_terms / total_terms

        # 长度比（中文字符:英文单词 通常在 1:1.5 到 1:3 之间）
        zh_len = len(re.findall(r'[\u4e00-\u9fff]', zh_text))
        en_len = len(re.findall(r'[a-zA-Z]+', en_text))
        if zh_len > 0 and en_len > 0:
            ratio = zh_len / en_len
            # 理想比例约 1:2
            ratio_score = max(0, 1 - abs(ratio - 0.5) * 2)
        else:
            ratio_score = 0

        return min(1.0, term_score * 2 + ratio_score * 0.3)

    # ---------- 不一致检测 ----------
    def detect_inconsistencies(
        self,
        aligned: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """检测中英文版本不一致"""
        inconsistencies = []

        for item in aligned:
            if item["type"] == "zh_only":
                inconsistencies.append({
                    "type": "missing_in_en",
                    "severity": "high",
                    "clause_id": item.get("clause_id", ""),
                    "message": f"条款仅存在于中文版：{item['zh'][:50]}...",
                    "zh": item["zh"],
                    "en": "",
                })
            elif item["type"] == "en_only":
                inconsistencies.append({
                    "type": "missing_in_zh",
                    "severity": "high",
                    "clause_id": item.get("clause_id", ""),
                    "message": f"条款仅存在于英文版：{item['en'][:50]}...",
                    "zh": "",
                    "en": item["en"],
                })
            elif item["type"] == "matched":
                # 检测数值/金额/日期不一致
                contradictions = self._detect_contradictions(item["zh"], item["en"])
                for c in contradictions:
                    inconsistencies.append({
                        "type": "contradiction",
                        "severity": "medium",
                        "clause_id": item.get("clause_id", ""),
                        "message": c,
                        "zh": item["zh"],
                        "en": item["en"],
                    })

        return inconsistencies

    def _detect_contradictions(self, zh: str, en: str) -> List[str]:
        """检测具体矛盾（数值、金额、日期）"""
        contradictions = []

        # 提取数字（忽略逗号和小数点后的末尾点号）
        def extract_numbers(text):
            nums = set()
            for m in re.findall(r'[\d,]+\.?\d*', text):
                # 标准化：移除逗号、移除末尾点号
                normalized = m.replace(',', '').rstrip('.')
                if normalized and normalized != '.':
                    nums.add(normalized)
            return nums

        zh_numbers = extract_numbers(zh)
        en_numbers = extract_numbers(en)

        # 过滤掉条款编号（如 "第1条" 中的 "1"）
        # 从条款编号中提取数字
        zh_clause_nums = set()
        en_clause_nums = set()
        for m in re.findall(r'第([一二三四五六七八九十百\d]+)条', zh):
            zh_clause_nums.add(m)
        for m in re.findall(r'Article\s+(\d+)', en):
            en_clause_nums.add(m)

        # 移除条款编号对应的数字
        zh_numbers -= zh_clause_nums
        en_numbers -= en_clause_nums

        # 简单判断：中文有的数字英文没有，或反之
        only_zh = zh_numbers - en_numbers
        only_en = en_numbers - zh_numbers

        # 过滤掉个位数（很可能是条款编号残留）
        only_zh = {n for n in only_zh if len(n) > 1 or int(n) > 9}
        only_en = {n for n in only_en if len(n) > 1 or int(n) > 9}

        if only_zh or only_en:
            contradictions.append(
                f"数值不一致 — 中文: {', '.join(list(only_zh)[:3])} vs 英文: {', '.join(list(only_en)[:3])}"
            )

        # 提取金额（包括中英文货币符号）
        zh_amounts = set(re.findall(r'[¥￥]\s*[\d,]+', zh))
        en_amounts = set(re.findall(r'[¥￥\$€]\s*[\d,]+', en))  # ¥ 可能同时出现在中英文
        # CNY/USD 等货币代码
        zh_amounts_code = set(re.findall(r'(?:CNY|RMB)\s*[\d,]+', zh, re.IGNORECASE))
        en_amounts_code = set(re.findall(r'(?:CNY|USD|EUR|GBP|JPY)\s*[\d,]+', en, re.IGNORECASE))

        # 如果两边都有金额（无论符号还是代码），不算矛盾
        has_zh_amount = bool(zh_amounts) or bool(zh_amounts_code)
        has_en_amount = bool(en_amounts) or bool(en_amounts_code)

        if has_zh_amount != has_en_amount:
            contradictions.append("金额标注不一致")

        return contradictions

    # ---------- 优先级标注 ----------
    def mark_priority(
        self,
        inconsistencies: List[Dict[str, Any]],
        priority: str = "zh",
    ) -> List[Dict[str, Any]]:
        """
        根据用户指定的优先级标注处理建议
        :param priority: "zh" 以中文版为准 / "en" 以英文版为准 / "strict" 严格模式（所有不一致都标为高风险）
        """
        marked = []
        for inc in inconsistencies:
            inc = dict(inc)
            if priority == "zh":
                if inc["type"] == "missing_in_zh":
                    inc["priority_note"] = "中文版未找到对应条款，建议以英文版为准补充"
                    inc["action"] = "review_en"
                elif inc["type"] == "missing_in_en":
                    inc["priority_note"] = "中文版特有条款，如需英文版包含，需补充翻译"
                    inc["action"] = "optional"
                else:
                    inc["priority_note"] = "以中文版为准，修正英文版"
                    inc["action"] = "align_to_zh"
            elif priority == "en":
                if inc["type"] == "missing_in_en":
                    inc["priority_note"] = "英文版未找到对应条款，建议以中文版为准补充"
                    inc["action"] = "review_zh"
                elif inc["type"] == "missing_in_zh":
                    inc["priority_note"] = "英文版特有条款，如需中文版包含，需补充翻译"
                    inc["action"] = "optional"
                else:
                    inc["priority_note"] = "以英文版为准，修正中文版"
                    inc["action"] = "align_to_en"
            else:  # strict
                inc["priority_note"] = "严格模式：所有不一致需双方确认"
                inc["action"] = "manual_review"

            marked.append(inc)

        return marked

    # ---------- 完整流程 ----------
    def analyze(
        self,
        zh_text: str,
        en_text: str,
        priority: str = "zh",
    ) -> Dict[str, Any]:
        """完整分析流程"""
        zh_paras = self.split_paragraphs(zh_text)
        en_paras = self.split_paragraphs(en_text)
        aligned = self.align_paragraphs(zh_paras, en_paras)
        inconsistencies = self.detect_inconsistencies(aligned)
        marked = self.mark_priority(inconsistencies, priority)

        # 统计
        matched = sum(1 for a in aligned if a["type"] == "matched")
        zh_only = sum(1 for a in aligned if a["type"] == "zh_only")
        en_only = sum(1 for a in aligned if a["type"] == "en_only")

        return {
            "priority": priority,
            "statistics": {
                "zh_paragraphs": len(zh_paras),
                "en_paragraphs": len(en_paras),
                "matched": matched,
                "zh_only": zh_only,
                "en_only": en_only,
                "inconsistencies": len(marked),
            },
            "aligned": aligned,
            "inconsistencies": marked,
        }

    # ---------- 报告生成 ----------
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """生成双语对照审查报告"""
        lines = []
        stats = analysis["statistics"]

        lines.append("# 中英文双语合同对照审查报告")
        lines.append(f"\n优先语言：{'中文' if analysis['priority'] == 'zh' else '英文'}")
        lines.append("")

        # 摘要
        lines.append("## 摘要")
        lines.append(f"- 中文段落数：{stats['zh_paragraphs']}")
        lines.append(f"- 英文段落数：{stats['en_paragraphs']}")
        lines.append(f"- 已匹配段落：{stats['matched']}")
        lines.append(f"- 仅中文存在：{stats['zh_only']}")
        lines.append(f"- 仅英文存在：{stats['en_only']}")
        lines.append(f"- 不一致项：{stats['inconsistencies']}")
        lines.append("")

        # 不一致详情
        if analysis["inconsistencies"]:
            lines.append("## 不一致详情")
            for inc in analysis["inconsistencies"]:
                lines.append(f"\n### [{inc['severity'].upper()}] {inc['clause_id']}")
                lines.append(f"- 类型：{inc['type']}")
                lines.append(f"- 说明：{inc['message']}")
                lines.append(f"- 建议：{inc.get('priority_note', '')}")
        lines.append("")

        # 对照表
        lines.append("## 段落对照表")
        for item in analysis["aligned"]:
            lines.append(f"\n### {item.get('clause_id', '未编号')} [{item['type']}]")
            if item.get("zh"):
                lines.append(f"中文：{item['zh'][:80]}")
            if item.get("en"):
                lines.append(f"英文：{item['en'][:80]}")
        lines.append("")

        return "\n".join(lines)


# ---------- 便捷函数 ----------
_default_aligner: Optional[BilingualAligner] = None


def get_aligner() -> BilingualAligner:
    """获取全局单例"""
    global _default_aligner
    if _default_aligner is None:
        _default_aligner = BilingualAligner()
    return _default_aligner


def analyze_bilingual(
    zh_text: str,
    en_text: str,
    priority: str = "zh",
) -> Dict[str, Any]:
    """便捷函数：分析双语合同"""
    return get_aligner().analyze(zh_text, en_text, priority)


def generate_bilingual_report(zh_text: str, en_text: str, priority: str = "zh") -> str:
    """便捷函数：生成双语审查报告"""
    aligner = get_aligner()
    analysis = aligner.analyze(zh_text, en_text, priority)
    return aligner.generate_report(analysis)


if __name__ == "__main__":
    # 简单测试
    aligner = BilingualAligner()
    print(f"术语对照表加载: {len(aligner._glossary)} 条")

    zh = """
第1条 合同标的：甲方向乙方采购服务器设备。
第2条 数量：共计 100 台。
第3条 价款：总价人民币 ¥500,000 元。
第4条 交付时间：合同签订后 30 日内交付。
第8条 争议解决：因本合同引起的争议，提交北京仲裁委员会仲裁。
"""

    en = """
Article 1 Subject Matter: Party A shall purchase server equipment from Party B.
Article 2 Quantity: Total 100 units.
Article 3 Price: Total price CNY ¥500,000.
Article 4 Delivery: Within 30 days after contract signing.
Article 8 Dispute Resolution: Any dispute arising from this contract shall be submitted to Beijing Arbitration Commission.
"""

    result = aligner.analyze(zh, en, priority="zh")
    print(f"\n分析结果:")
    print(f"  匹配: {result['statistics']['matched']}")
    print(f"  仅中文: {result['statistics']['zh_only']}")
    print(f"  仅英文: {result['statistics']['en_only']}")
    print(f"  不一致: {result['statistics']['inconsistencies']}")

    report = aligner.generate_report(result)
    print("\n" + report[:500])
