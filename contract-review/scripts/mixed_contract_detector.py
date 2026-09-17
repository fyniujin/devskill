#!/usr/bin/env python3
"""
混合合同检测器 v5.3
检测中英文混合合同，当英文段落占比超阈值时自动启用双语报告
"""

import re
from typing import Dict, Any

# 混合合同判定阈值（英文段落占比）
MIXED_CONTRACT_THRESHOLD = 0.30


def _detect_language(text: str) -> str:
    """简单语言检测：基于字符数量判断"""
    if not text:
        return "unknown"
    
    # 统计中文字符数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 统计英文单词字母数
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    # 统计日文字符（平假名+片假名）
    japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
    # 统计韩文字符
    korean_chars = len(re.findall(r'[\uac00-\ud7af\u1100-\u11ff]', text))
    
    total_chars = chinese_chars + english_chars + japanese_chars + korean_chars
    if total_chars == 0:
        return "unknown"
    
    en_ratio = english_chars / total_chars
    zh_ratio = chinese_chars / total_chars
    
    if zh_ratio > 0.7:
        return "zh"
    elif en_ratio > 0.7:
        return "en"
    else:
        return "mixed"


def detect_mixed_contract(text: str) -> Dict[str, Any]:
    """
    检测是否为混合合同（中英文混杂）
    
    Returns:
        {
            'is_mixed': bool,
            'en_ratio': float,
            'zh_ratio': float,
            'recommendation': 'bilingual' | 'en_only' | 'zh_only',
            'details': str
        }
    """
    if not text:
        return {
            'is_mixed': False,
            'en_ratio': 0.0,
            'zh_ratio': 0.0,
            'recommendation': 'zh_only',
            'details': 'Empty text'
        }
    
    # 按段落分割
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\n', text) if p.strip()]
    if not paragraphs:
        return {
            'is_mixed': False,
            'en_ratio': 0.0,
            'zh_ratio': 0.0,
            'recommendation': 'zh_only',
            'details': 'No paragraphs found'
        }
    
    # 逐段检测语言
    en_paragraphs = 0
    zh_paragraphs = 0
    total_para = len(paragraphs)
    
    for para in paragraphs:
        lang = _detect_language(para)
        if lang == "en":
            en_paragraphs += 1
        elif lang == "zh":
            zh_paragraphs += 1
    
    en_ratio = en_paragraphs / total_para if total_para > 0 else 0
    zh_ratio = zh_paragraphs / total_para if total_para > 0 else 0
    
    # 判定是否混合
    is_mixed = en_ratio > MIXED_CONTRACT_THRESHOLD
    
    if is_mixed:
        recommendation = 'bilingual'
        details = f"英文段落占比 {en_ratio:.0%}，超过阈值 {MIXED_CONTRACT_THRESHOLD:.0%}，建议启用双语报告"
    elif en_ratio > 0.1:
        recommendation = 'bilingual'
        details = f"英文段落占比 {en_ratio:.0%}，建议启用双语报告"
    elif zh_ratio > 0.9:
        recommendation = 'zh_only'
        details = f"中文段落占比 {zh_ratio:.0%}，纯中文合同"
    else:
        recommendation = 'zh_only'
        details = f"中文为主（{zh_ratio:.0%}），少量英文术语"
    
    return {
        'is_mixed': is_mixed,
        'en_ratio': round(en_ratio, 3),
        'zh_ratio': round(zh_ratio, 3),
        'recommendation': recommendation,
        'details': details,
        'total_paragraphs': total_para,
        'en_paragraphs': en_paragraphs,
        'zh_paragraphs': zh_paragraphs
    }


def generate_detection_report(result: Dict[str, Any]) -> str:
    """生成混合合同检测报告"""
    lines = [
        "# 混合合同检测报告",
        "",
        f"- 是否为混合合同：{'是' if result.get('is_mixed') else '否'}",
        f"- 英文段落占比：{result.get('en_ratio', 0):.0%}",
        f"- 中文段落占比：{result.get('zh_ratio', 0):.0%}",
        f"- 建议：{result.get('recommendation', 'unknown')}",
        f"- 详情：{result.get('details', '')}",
    ]
    return "\n".join(lines)
