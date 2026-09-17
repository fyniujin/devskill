#!/usr/bin/env python3
"""
锚点+长度双因子句级对齐引擎 v5.3
以数字、日期、专有名词为锚点先配对，剩余句段按长度比与位置校正
输出对齐置信度，低于阈值时人工复核标记
"""

import re
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher

# 置信度阈值（低于此值标记人工复核）
CONFIDENCE_THRESHOLD = 0.6

# 锚点正则（按优先级排序）
ANCHOR_PATTERNS = [
    (r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', 'date'),        # 日期
    (r'\d{4}年\d{1,2}月\d{1,2}日', 'date_cn'),         # 中文日期
    (r'(?<![\d.,])\d{1,3}(?:,\d{3})*(?:\.\d+)?', 'number'),  # 数字（含千分位）
    (r'(?<![\d.,])\d+\.\d+', 'decimal'),                # 小数
    (r'USD\s*\d[\d,]*\.?\d*', 'currency_usd'),          # 美元
    (r'(?:¥|RMB|CNY)\s*\d[\d,]*\.?\d*', 'currency_cny'),  # 人民币
    (r'(?:EUR|€)\s*\d[\d,]*\.?\d*', 'currency_eur'),   # 欧元
    (r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', 'proper_noun'),  # 英文专有名词
    (r'[一-龥]{2,}(?:公司|有限|事务所|银行|集团)', 'cn_entity'),  # 中文机构名
]


def extract_anchors(text: str) -> List[Dict[str, Any]]:
    """从文本中提取所有锚点"""
    anchors = []
    for pattern, anchor_type in ANCHOR_PATTERNS:
        for m in re.finditer(pattern, text):
            anchors.append({
                'text': m.group(0),
                'type': anchor_type,
                'start': m.start(),
                'end': m.end(),
                'normalized': _normalize_number(m.group(0)) if 'number' in anchor_type or 'currency' in anchor_type else m.group(0).lower()
            })
    return anchors


def split_sentences(text: str) -> List[str]:
    """按句子边界分割文本（中英文）"""
    if not text:
        return []
    # 中英文句子分隔符
    sentences = re.split(r'(?<=[。；！？.!?;])\s*', text)
    return [s.strip() for s in sentences if s.strip()]


def _normalize_number(num_str: str) -> str:
    """标准化数字（去除货币符号、千分位）"""
    if not num_str:
        return num_str
    cleaned = re.sub(r'[^\d.]', '', num_str.replace(',', ''))
    try:
        return str(float(cleaned))
    except (ValueError, TypeError):
        return cleaned


def match_by_anchors(zh_sentences: List[str], en_sentences: List[str]) -> List[Dict[str, Any]]:
    """基于锚点匹配句子"""
    zh_anchors = [extract_anchors(s) for s in zh_sentences]
    en_anchors = [extract_anchors(s) for s in en_sentences]
    
    pairs = []
    used_en = set()
    
    for zi, zh_sent in enumerate(zh_sentences):
        best_match = None
        best_score = 0.0
        best_ei = -1
        
        for ei, en_sent in enumerate(en_sentences):
            if ei in used_en:
                continue
            
            # 计算锚点重合度
            score = _anchor_similarity(zh_anchors[zi], en_anchors[ei])
            
            if score > best_score:
                best_score = score
                best_match = en_sent
                best_ei = ei
        
        if best_match and best_score >= CONFIDENCE_THRESHOLD:
            pairs.append({
                'zh': zh_sent,
                'en': best_match,
                'confidence': round(best_score, 2),
                'method': 'anchor'
            })
            used_en.add(best_ei)
    
    return pairs


def _anchor_similarity(zh_anchors: List[Dict], en_anchors: List[Dict]) -> float:
    """计算两组锚点的相似度"""
    if not zh_anchors and not en_anchors:
        return 0.5  # 无锚点时返回中性值
    
    if not zh_anchors or not en_anchors:
        return 0.2  # 一方无锚点，低置信度
    
    matched = 0
    for za in zh_anchors:
        for ea in en_anchors:
            if za['type'] == ea['type']:
                if za['type'] in ('number', 'decimal', 'currency_usd', 'currency_cny', 'currency_eur'):
                    if _normalize_number(za['text']) == _normalize_number(ea['text']):
                        matched += 1
                        break
                elif za['type'] in ('date', 'date_cn'):
                    if _normalize_number(za['text']) == _normalize_number(ea['text']):
                        matched += 1
                        break
                elif za['type'] == 'proper_noun' and ea['type'] == 'proper_noun':
                    if _proper_noun_match(za['text'], ea['text']):
                        matched += 1
                        break
                elif za['type'] == 'cn_entity' and ea['type'] == 'proper_noun':
                    # 中文机构名 vs 英文专有名词（需术语表辅助，这里用模糊匹配）
                    if _term_similarity(za['text'], ea['text']) > 0.6:
                        matched += 1
                        break
    
    total_unique = len(set(a['normalized'] for a in zh_anchors) | set(a['normalized'] for a in en_anchors))
    return matched / total_unique if total_unique > 0 else 0.0


def _proper_noun_match(zh_text: str, en_text: str) -> bool:
    """专有名词模糊匹配"""
    # 简单的首字母/包含匹配
    zh_lower = zh_text.lower().strip()
    en_lower = en_text.lower().strip()
    if zh_lower in en_lower or en_lower in zh_lower:
        return True
    return SequenceMatcher(None, zh_lower, en_lower).ratio() > 0.7


def _term_similarity(zh: str, en: str) -> float:
    """术语相似度"""
    return SequenceMatcher(None, zh.lower(), en.lower()).ratio()


def align(zh_text: str, en_text: str) -> Dict[str, Any]:
    """
    锚点+长度双因子句级对齐
    
    Returns:
        {
            'pairs': [{'zh': str, 'en': str, 'confidence': float, 'method': str}],
            'statistics': {'matched': int, 'total_zh': int, 'total_en': int, 'avg_confidence': float}
        }
    """
    zh_sentences = split_sentences(zh_text)
    en_sentences = split_sentences(en_text)
    
    if not zh_sentences or not en_sentences:
        return {
            'pairs': [],
            'statistics': {'matched': 0, 'total_zh': len(zh_sentences), 'total_en': len(en_sentences), 'avg_confidence': 0.0}
        }
    
    # Phase 1: 锚点匹配
    anchor_pairs = match_by_anchors(zh_sentences, en_sentences)
    used_zh = {p['zh'] for p in anchor_pairs}
    used_en = {p['en'] for p in anchor_pairs}
    
    # Phase 2: 长度+位置匹配（剩余句段）
    remaining_zh = [s for s in zh_sentences if s not in used_zh]
    remaining_en = [s for s in en_sentences if s not in used_en]
    
    length_pairs = _length_position_match(remaining_zh, remaining_en)
    
    # 合并结果
    all_pairs = anchor_pairs + length_pairs
    
    # 统计
    avg_conf = sum(p['confidence'] for p in all_pairs) / len(all_pairs) if all_pairs else 0.0
    below_threshold = sum(1 for p in all_pairs if p['confidence'] < CONFIDENCE_THRESHOLD)
    
    return {
        'pairs': all_pairs,
        'statistics': {
            'matched': len(all_pairs),
            'total_zh': len(zh_sentences),
            'total_en': len(en_sentences),
            'avg_confidence': round(avg_conf, 2),
            'below_threshold': below_threshold
        }
    }


def _length_position_match(zh_sents: List[str], en_sents: List[str]) -> List[Dict[str, Any]]:
    """按长度比和位置对剩余句段做匹配"""
    pairs = []
    used_en = set()
    
    for zi, zh_sent in enumerate(zh_sents):
        best_match = None
        best_score = 0.0
        best_ei = -1
        
        for ei, en_sent in enumerate(en_sents):
            if ei in used_en:
                continue
            
            # 长度比因子
            len_zh = len(zh_sent)
            len_en = len(en_sent)
            if len_zh == 0 or len_en == 0:
                continue
            
            # 长度比（理想情况下中文:英文 ≈ 1:1.5 到 1:2.5）
            length_ratio = len_en / len_zh if len_zh > 0 else 1
            length_score = 1.0 - abs(length_ratio - 1.8) / 2.0  # 1.8是理想比值
            length_score = max(0.1, min(1.0, length_score))
            
            # 位置因子（序号越接近越可能匹配）
            position_diff = abs(zi - ei)
            position_score = 1.0 / (1.0 + position_diff * 0.3)
            
            # 综合得分
            combined = length_score * 0.6 + position_score * 0.4
            
            if combined > best_score:
                best_score = combined
                best_match = en_sent
                best_ei = ei
        
        if best_match and best_score >= 0.3:
            pairs.append({
                'zh': zh_sent,
                'en': best_match,
                'confidence': round(best_score, 2),
                'method': 'length_position'
            })
            used_en.add(best_ei)
    
    return pairs


def get_aligner():
    """获取对齐器实例（兼容函数）"""
    return AnchorAligner()


def align_anchor(zh_text: str, en_text: str) -> Dict[str, Any]:
    """便捷函数：执行锚点对齐"""
    return align(zh_text, en_text)


def generate_anchor_report(result: Dict[str, Any]) -> str:
    """生成锚点对齐报告"""
    stats = result.get('statistics', {})
    lines = [
        "# 锚点+长度双因子句级对齐报告",
        "",
        "## 统计",
        f"- 中文句数：{stats.get('total_zh', 0)}",
        f"- 英文句数：{stats.get('total_en', 0)}",
        f"- 匹配对数：{stats.get('matched', 0)}",
        f"- 平均置信度：{stats.get('avg_confidence', 0):.2f}",
        f"- 置信度不足（<{CONFIDENCE_THRESHOLD}）：{stats.get('below_threshold', 0)} 条（建议人工复核）",
        "",
        "## 对齐结果",
    ]
    
    for i, p in enumerate(result.get('pairs', [])):
        conf = p.get('confidence', 0)
        flag = "⚠️" if conf < CONFIDENCE_THRESHOLD else "✅"
        method = p.get('method', 'unknown')
        lines.append(f"### 对 {i+1} [{method}] 置信度: {conf:.2f} {flag}")
        lines.append(f"- **中文**：{p.get('zh', '')}")
        lines.append(f"- **英文**：{p.get('en', '')}")
        lines.append("")
    
    return "\n".join(lines)


class AnchorAligner:
    """锚点+长度双因子句级对齐器"""
    
    def __init__(self):
        self.threshold = CONFIDENCE_THRESHOLD
    
    def align(self, zh_text: str, en_text: str) -> Dict[str, Any]:
        return align(zh_text, en_text)
    
    def generate_report(self, result: Dict[str, Any]) -> str:
        return generate_anchor_report(result)
