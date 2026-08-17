#!/usr/bin/env python3
"""
bilingual_aligner.py v5.1
多语种合同对齐引擎
功能：段落对齐算法、版本不一致检测、优先级标注、多语种术语表懒加载
v5.0 新增：多语言合同支持（中英双语对照审查）
v5.1 新增：日语/韩语术语表支持，多语种扩展
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
REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"
GLOSSARY_FILE = REFERENCES_DIR / "bilingual_glossary.yaml"
JA_GLOSSARY_FILE = REFERENCES_DIR / "ja_legal_terms.yaml"
KO_GLOSSARY_FILE = REFERENCES_DIR / "ko_legal_terms.yaml"

# === 支持的语言对 ===
SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "glossary": GLOSSARY_FILE,
        "zh_field": "zh",
        "target_field": "en",
        "clause_patterns": [
            (r'Article\s+(\d+)', '第{}条'),
            (r'Section\s+(\d+)', '第{}条'),
            (r'^(\d+)[\.、]', '第{}条'),
        ],
    },
    "ja": {
        "name": "日本語",
        "glossary": JA_GLOSSARY_FILE,
        "zh_field": "zh",
        "target_field": "ja",
        "clause_patterns": [
            (r'第([一二三四五六七八九十百\d]+)条', '第{}条'),
            (r'第([一二三四五六七八九十百\d]+)項', '第{}項'),
            (r'^(\d+)[\.、]', '第{}条'),
        ],
    },
    "ko": {
        "name": "한국어",
        "glossary": KO_GLOSSARY_FILE,
        "zh_field": "zh",
        "target_field": "ko",
        "clause_patterns": [
            (r'제([一二三四五六七八九十百\d]+)조', '제{}조'),
            (r'제([一二三四五六七八九十百\d]+)항', '제{}항'),
            (r'^(\d+)[\.、]', '제{}조'),
        ],
    },
}


class BilingualAligner:
    """多语种对齐引擎 — 段落匹配 + 不一致检测 + 术语表懒加载"""

    def __init__(self, target_lang: str = "en", glossary_file: Optional[Path] = None):
        """
        :param target_lang: 目标语言代码 ("en", "ja", "ko")
        :param glossary_file: 自定义术语表路径（可选）
        """
        self.target_lang = target_lang.lower()
        if self.target_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"不支持的目标语言: {target_lang}，支持: {list(SUPPORTED_LANGUAGES.keys())}")

        self._lang_config = SUPPORTED_LANGUAGES[self.target_lang]
        self.glossary_file = glossary_file or self._lang_config["glossary"]
        self._glossary: List[Dict[str, str]] = []
        self._zh_to_target: Dict[str, str] = {}
        self._target_to_zh: Dict[str, str] = {}
        self._glossary_loaded: bool = False

    # ---------- 加载（懒加载） ----------
    def _ensure_glossary_loaded(self):
        """确保术语表已加载（懒加载）"""
        if self._glossary_loaded:
            return
        self._load_glossary()
        self._glossary_loaded = True

    def _load_glossary(self):
        if not self.glossary_file.exists():
            logger.warning(f"术语对照表不存在: {self.glossary_file}")
            return
        try:
            import yaml
            with open(self.glossary_file, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self._glossary = data.get("terms", [])
            target_field = self._lang_config["target_field"]
            for t in self._glossary:
                zh = t.get("zh", "").strip()
                target = t.get(target_field, "").strip()
                if zh and target:
                    self._zh_to_target[zh] = target
                    self._target_to_zh[target.lower()] = zh
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
        """提取条款编号（归一化为阿拉伯数字，便于多语种对照）"""
        # 匹配"第X条"、"第X款"、"Article X"、"Section X"等
        patterns = self._lang_config.get("clause_patterns", [])
        # 也尝试通用中文模式
        cn_patterns = [
            (r'第([一二三四五六七八九十百\d]+)条', '第{}条'),
            (r'第([一二三四五六七八九十百\d]+)款', '第{}款'),
        ]
        all_patterns = cn_patterns + patterns

        for p, fmt in all_patterns:
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
        target_paragraphs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        对齐中文与目标语言段落
        返回对齐结果列表，每个元素包含 zh、target 和匹配分数
        """
        self._ensure_glossary_loaded()
        aligned = []
        used_target = set()

        # 第一轮：按条款编号精确匹配
        zh_with_id = {p["clause_id"]: p for p in zh_paragraphs if p["clause_id"]}
        target_with_id = {p["clause_id"]: p for p in target_paragraphs if p["clause_id"]}

        for clause_id, zh_p in zh_with_id.items():
            if clause_id in target_with_id:
                target_p = target_with_id[clause_id]
                aligned.append({
                    "type": "matched",
                    "clause_id": clause_id,
                    "zh": zh_p["text"],
                    "target": target_p["text"],
                    "target_lang": self.target_lang,
                    "match_score": 1.0,
                    "match_method": "clause_id",
                })
                used_target.add(target_p["index"])
            else:
                aligned.append({
                    "type": "zh_only",
                    "clause_id": clause_id,
                    "zh": zh_p["text"],
                    "target": "",
                    "target_lang": self.target_lang,
                    "match_score": 0,
                    "match_method": "none",
                })

        # 第二轮：按顺序和相似度匹配剩余段落
        unmatched_zh = [p for p in zh_paragraphs if p["clause_id"] not in zh_with_id]
        unmatched_target = [p for p in target_paragraphs if p["index"] not in used_target]

        # 使用位置 + 术语相似度进行匹配
        for zh_p in unmatched_zh:
            best_match = None
            best_score = 0

            for target_p in unmatched_target:
                score = self._similarity_score(zh_p["text"], target_p["text"])
                # 位置权重：越接近的位置分数越高
                pos_weight = 1.0 - abs(zh_p["index"] - target_p["index"]) / max(len(zh_paragraphs), len(target_paragraphs))
                score = score * 0.7 + pos_weight * 0.3

                if score > best_score and score > 0.3:
                    best_score = score
                    best_match = target_p

            if best_match:
                aligned.append({
                    "type": "matched",
                    "clause_id": zh_p["clause_id"] or f"pos_{zh_p['index']}",
                    "zh": zh_p["text"],
                    "target": best_match["text"],
                    "target_lang": self.target_lang,
                    "match_score": round(best_score, 3),
                    "match_method": "similarity",
                })
                unmatched_target.remove(best_match)
            else:
                aligned.append({
                    "type": "zh_only",
                    "clause_id": zh_p["clause_id"] or f"pos_{zh_p['index']}",
                    "zh": zh_p["text"],
                    "target": "",
                    "target_lang": self.target_lang,
                    "match_score": 0,
                    "match_method": "none",
                })

        # 目标语言剩余段落（中文没有的）
        for target_p in unmatched_target:
            aligned.append({
                "type": "target_only",
                "clause_id": target_p["clause_id"] or f"pos_{target_p['index']}",
                "zh": "",
                "target": target_p["text"],
                "target_lang": self.target_lang,
                "match_score": 0,
                "match_method": "none",
            })

        return aligned

    def _similarity_score(self, zh_text: str, target_text: str) -> float:
        """计算中文与目标语言段落相似度（基于术语翻译匹配）"""
        if not zh_text or not target_text:
            return 0.0

        # 统计匹配的术语数
        matched_terms = 0
        for zh_term, target_term in self._zh_to_target.items():
            if zh_term in zh_text and target_term.lower() in target_text.lower():
                matched_terms += 1

        # 基于术语数量计算分数
        total_terms = max(len(self._glossary), 1)
        term_score = matched_terms / total_terms

        # 长度比
        zh_len = len(re.findall(r'[\u4e00-\u9fff]', zh_text))
        # 目标语言：英文按单词，日文按假名，韩文按谚文
        if self.target_lang == "en":
            target_len = len(re.findall(r'[a-zA-Z]+', target_text))
        elif self.target_lang == "ja":
            target_len = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', target_text))
        elif self.target_lang == "ko":
            target_len = len(re.findall(r'[\uac00-\ud7af\u1100-\u11ff]', target_text))
        else:
            target_len = len(target_text)

        if zh_len > 0 and target_len > 0:
            ratio = zh_len / target_len
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
        """检测中文与目标语言版本不一致"""
        inconsistencies = []

        for item in aligned:
            if item["type"] == "zh_only":
                inconsistencies.append({
                    "type": "missing_in_target",
                    "severity": "high",
                    "clause_id": item.get("clause_id", ""),
                    "message": f"条款仅存在于中文版：{item['zh'][:50]}...",
                    "zh": item["zh"],
                    "target": "",
                    "target_lang": self.target_lang,
                })
            elif item["type"] == "target_only":
                inconsistencies.append({
                    "type": "missing_in_zh",
                    "severity": "high",
                    "clause_id": item.get("clause_id", ""),
                    "message": f"条款仅存在于{self._lang_config['name']}版：{item['target'][:50]}...",
                    "zh": "",
                    "target": item["target"],
                    "target_lang": self.target_lang,
                })
            elif item["type"] == "matched":
                # 检测数值/金额/日期不一致
                contradictions = self._detect_contradictions(item["zh"], item["target"])
                for c in contradictions:
                    inconsistencies.append({
                        "type": "contradiction",
                        "severity": "medium",
                        "clause_id": item.get("clause_id", ""),
                        "message": c,
                        "zh": item["zh"],
                        "target": item["target"],
                        "target_lang": self.target_lang,
                    })

        return inconsistencies

    def _detect_contradictions(self, zh: str, target: str) -> List[str]:
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
        target_numbers = extract_numbers(target)

        # 过滤掉条款编号（如 "第1条" 中的 "1"）
        zh_clause_nums = set()
        target_clause_nums = set()
        for m in re.findall(r'第([一二三四五六七八九十百\d]+)条', zh):
            zh_clause_nums.add(m)
        # 目标语言的条款编号
        if self.target_lang == "en":
            for m in re.findall(r'Article\s+(\d+)', target):
                target_clause_nums.add(m)
        elif self.target_lang == "ja":
            for m in re.findall(r'第([一二三四五六七八九十百\d]+)条', target):
                target_clause_nums.add(m)
        elif self.target_lang == "ko":
            for m in re.findall(r'제(\d+)조', target):
                target_clause_nums.add(m)

        # 移除条款编号对应的数字
        zh_numbers -= zh_clause_nums
        target_numbers -= target_clause_nums

        # 简单判断：中文有的数字目标语言没有，或反之
        only_zh = zh_numbers - target_numbers
        only_target = target_numbers - zh_numbers

        # 过滤掉个位数（很可能是条款编号残留）
        only_zh = {n for n in only_zh if len(n) > 1 or int(n) > 9}
        only_target = {n for n in only_target if len(n) > 1 or int(n) > 9}

        if only_zh or only_target:
            contradictions.append(
                f"数值不一致 — 中文: {', '.join(list(only_zh)[:3])} vs {self._lang_config['name']}: {', '.join(list(only_target)[:3])}"
            )

        # 提取金额（包括中英文货币符号）
        zh_amounts = set(re.findall(r'[¥￥]\s*[\d,]+', zh))
        target_amounts = set(re.findall(r'[¥￥\$€]\s*[\d,]+', target))
        # CNY/USD 等货币代码
        zh_amounts_code = set(re.findall(r'(?:CNY|RMB)\s*[\d,]+', zh, re.IGNORECASE))
        target_amounts_code = set(re.findall(r'(?:CNY|USD|EUR|GBP|JPY|KRW)\s*[\d,]+', target, re.IGNORECASE))

        # 如果两边都有金额（无论符号还是代码），不算矛盾
        has_zh_amount = bool(zh_amounts) or bool(zh_amounts_code)
        has_target_amount = bool(target_amounts) or bool(target_amounts_code)

        if has_zh_amount != has_target_amount:
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
        :param priority: "zh" 以中文版为准 / "target" 以目标语言版为准 / "strict" 严格模式
        """
        marked = []
        for inc in inconsistencies:
            inc = dict(inc)
            if priority == "zh":
                if inc["type"] == "missing_in_zh":
                    inc["priority_note"] = f"中文版未找到对应条款，建议以{self._lang_config['name']}版为准补充"
                    inc["action"] = "review_target"
                elif inc["type"] == "missing_in_target":
                    inc["priority_note"] = f"中文版特有条款，如需{self._lang_config['name']}版包含，需补充翻译"
                    inc["action"] = "optional"
                else:
                    inc["priority_note"] = "以中文版为准，修正目标语言版"
                    inc["action"] = "align_to_zh"
            elif priority == "target":
                if inc["type"] == "missing_in_target":
                    inc["priority_note"] = f"{self._lang_config['name']}版未找到对应条款，建议以中文版为准补充"
                    inc["action"] = "review_zh"
                elif inc["type"] == "missing_in_zh":
                    inc["priority_note"] = f"{self._lang_config['name']}版特有条款，如需中文版包含，需补充翻译"
                    inc["action"] = "optional"
                else:
                    inc["priority_note"] = f"以{self._lang_config['name']}版为准，修正中文版"
                    inc["action"] = "align_to_target"
            else:  # strict
                inc["priority_note"] = "严格模式：所有不一致需双方确认"
                inc["action"] = "manual_review"

            marked.append(inc)

        return marked

    # ---------- 完整流程 ----------
    def analyze(
        self,
        zh_text: str,
        target_text: str,
        priority: str = "zh",
    ) -> Dict[str, Any]:
        """完整分析流程"""
        self._ensure_glossary_loaded()
        zh_paras = self.split_paragraphs(zh_text)
        target_paras = self.split_paragraphs(target_text)
        aligned = self.align_paragraphs(zh_paras, target_paras)
        inconsistencies = self.detect_inconsistencies(aligned)
        marked = self.mark_priority(inconsistencies, priority)

        # 统计
        matched = sum(1 for a in aligned if a["type"] == "matched")
        zh_only = sum(1 for a in aligned if a["type"] == "zh_only")
        target_only = sum(1 for a in aligned if a["type"] == "target_only")

        return {
            "priority": priority,
            "target_lang": self.target_lang,
            "target_lang_name": self._lang_config["name"],
            "statistics": {
                "zh_paragraphs": len(zh_paras),
                "target_paragraphs": len(target_paras),
                "matched": matched,
                "zh_only": zh_only,
                "target_only": target_only,
                "inconsistencies": len(marked),
            },
            "aligned": aligned,
            "inconsistencies": marked,
        }

    # ---------- 报告生成 ----------
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """生成多语种对照审查报告"""
        lines = []
        stats = analysis["statistics"]
        target_name = analysis.get("target_lang_name", self._lang_config["name"])

        lines.append(f"# 中文/{target_name}双语合同对照审查报告")
        lines.append(f"\n优先语言：{'中文' if analysis['priority'] == 'zh' else target_name}")
        lines.append("")

        # 摘要
        lines.append("## 摘要")
        lines.append(f"- 中文段落数：{stats['zh_paragraphs']}")
        lines.append(f"- {target_name}段落数：{stats['target_paragraphs']}")
        lines.append(f"- 已匹配段落：{stats['matched']}")
        lines.append(f"- 仅中文存在：{stats['zh_only']}")
        lines.append(f"- 仅{target_name}存在：{stats['target_only']}")
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
            if item.get("target"):
                lines.append(f"{target_name}：{item['target'][:80]}")
        lines.append("")

        return "\n".join(lines)


# ---------- 便捷函数 ----------
_default_aligners: Dict[str, BilingualAligner] = {}


def get_aligner(target_lang: str = "en") -> BilingualAligner:
    """获取全局单例（按语言缓存）"""
    if target_lang not in _default_aligners:
        _default_aligners[target_lang] = BilingualAligner(target_lang=target_lang)
    return _default_aligners[target_lang]


def analyze_bilingual(
    zh_text: str,
    target_text: str,
    target_lang: str = "en",
    priority: str = "zh",
) -> Dict[str, Any]:
    """便捷函数：分析双语合同"""
    return get_aligner(target_lang).analyze(zh_text, target_text, priority)


def generate_bilingual_report(
    zh_text: str,
    target_text: str,
    target_lang: str = "en",
    priority: str = "zh",
) -> str:
    """便捷函数：生成双语审查报告"""
    aligner = get_aligner(target_lang)
    analysis = aligner.analyze(zh_text, target_text, priority)
    return aligner.generate_report(analysis)


if __name__ == "__main__":
    # 简单测试
    aligner = BilingualAligner(target_lang="en")
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
    print(f"  仅英文: {result['statistics']['target_only']}")
    print(f"  不一致: {result['statistics']['inconsistencies']}")

    report = aligner.generate_report(result)
    print("\n" + report[:500])
