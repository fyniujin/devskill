#!/usr/bin/env python3
"""
报告生成模块
将审查结果生成为结构化报告
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 严重等级排序权重
SEVERITY_WEIGHTS = {
    '严重': 0,
    '中等': 1,
    '一般': 2,
    '提示': 3,
}

# 严重等级 emoji
SEVERITY_EMOJI = {
    '严重': '🔴',
    '中等': '🟡',
    '一般': '🟢',
    '提示': 'ℹ️',
}

# 评分影响
SCORE_IMPACT = {
    '严重': -15,
    '中等': -8,
    '一般': -3,
    '提示': 0,
}


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        pass
    
    def generate(self, risks: List[Dict], contract_info: Dict,
                 output_format: str = 'markdown') -> str:
        """
        生成审查报告
        
        Args:
            risks: 风险项列表
            contract_info: 合同基本信息
            output_format: 输出格式（markdown/json）
            
        Returns:
            报告内容字符串
        """
        # 按严重等级排序
        sorted_risks = sorted(risks, key=lambda r: SEVERITY_WEIGHTS.get(r.get('severity', '一般'), 99))
        
        # 计算评分
        score = self._calculate_score(risks)
        
        # 统计
        stats = self._count_by_severity(risks)
        
        if output_format == 'json':
            return self._generate_json(sorted_risks, contract_info, score, stats)
        else:
            return self._generate_markdown(sorted_risks, contract_info, score, stats)
    
    def _calculate_score(self, risks: List[Dict]) -> int:
        """计算综合评分（0-100，分数越高风险越低）"""
        score = 100
        
        for risk in risks:
            severity = risk.get('severity', '一般')
            score += SCORE_IMPACT.get(severity, 0)
        
        return max(0, min(100, score))
    
    def _count_by_severity(self, risks: List[Dict]) -> Dict[str, int]:
        """按严重等级统计"""
        counts = {'严重': 0, '中等': 0, '一般': 0, '提示': 0}
        for risk in risks:
            severity = risk.get('severity', '一般')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _generate_markdown(self, risks: List[Dict], contract_info: Dict,
                           score: int, stats: Dict) -> str:
        """生成 Markdown 格式报告"""
        lines = []
        
        # 标题
        lines.append("# 合同审查报告")
        lines.append("")
        
        # 基本信息
        lines.append("## 基本信息")
        lines.append("")
        lines.append(f"- **合同名称**：{contract_info.get('title', '未知')}")
        lines.append(f"- **合同类型**：{contract_info.get('contract_type', '未知')}")
        lines.append(f"- **审查视角**：{contract_info.get('party_role', '双方')}")
        lines.append(f"- **审查日期**：{datetime.now().strftime('%Y-%m-%d')}")
        
        parties = contract_info.get('parties', [])
        if parties:
            party_names = [f"{p.get('role', '')}: {p.get('name', '')}" for p in parties]
            lines.append(f"- **合同主体**：{'; '.join(party_names)}")
        
        if contract_info.get('total_amount'):
            lines.append(f"- **合同金额**：{contract_info.get('total_amount', '')} {contract_info.get('currency', 'CNY')}")
        
        lines.append("")
        
        # 风险概况
        lines.append("## 📊 风险概况")
        lines.append("")
        lines.append("| 等级 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| 🔴 严重 | {stats.get('严重', 0)} 项 |")
        lines.append(f"| 🟡 中等 | {stats.get('中等', 0)} 项 |")
        lines.append(f"| 🟢 一般 | {stats.get('一般', 0)} 项 |")
        lines.append(f"| ℹ️ 提示 | {stats.get('提示', 0)} 项 |")
        lines.append("")
        
        # 评分
        risk_level = "风险较低" if score >= 80 else "风险中等" if score >= 60 else "风险偏高" if score >= 40 else "风险很高"
        lines.append(f"**⭐ 综合评分：{score}/100**（{risk_level}）")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 风险详情
        current_severity = None
        
        for risk in risks:
            severity = risk.get('severity', '一般')
            
            if severity != current_severity:
                current_severity = severity
                emoji = SEVERITY_EMOJI.get(severity, '⚪')
                lines.append(f"## {emoji} {severity}风险")
                lines.append("")
            
            # 风险标题
            title = risk.get('title', '未命名风险')
            lines.append(f"### {title}")
            lines.append("")
            
            # 位置
            if risk.get('clause_ref'):
                lines.append(f"- **位置**：{risk['clause_ref']} / 第 {risk.get('page', '?')} 页")
            
            # 原文引用
            if risk.get('text_snippet'):
                lines.append(f"- **原文**：{risk['text_snippet']}")
            
            # 问题描述
            if risk.get('description'):
                lines.append(f"- **问题**：{risk['description']}")
            
            # 法律依据
            if risk.get('legal_basis'):
                lines.append(f"- **法律依据**：{risk['legal_basis']}")
            
            # 修改建议
            if risk.get('suggestion'):
                lines.append(f"- **修改建议**：{risk['suggestion']}")
            
            # 推荐范本
            if risk.get('template'):
                lines.append(f"- **推荐范本**：\n\n  > {risk['template']}")
            
            lines.append("")
        
        # 缺失条款
        missing = contract_info.get('missing_clauses', [])
        if missing:
            lines.append("## 📋 缺失条款清单")
            lines.append("")
            for item in missing:
                lines.append(f"- {item}")
            lines.append("")
        
        # 特别提示
        special_notes = contract_info.get('special_notes', [])
        if special_notes:
            lines.append("## ℹ️ 特别提示")
            lines.append("")
            for note in special_notes:
                lines.append(f"- {note}")
            lines.append("")
        
        # 修改建议汇总
        if risks:
            lines.append("## 📝 修改建议汇总")
            lines.append("")
            for i, risk in enumerate(risks, 1):
                if risk.get('suggestion'):
                    lines.append(f"{i}. **{risk.get('title', '')}**")
                    lines.append(f"   → {risk['suggestion']}")
                    lines.append("")
        
        # 法规依据
        legal_bases = set()
        for risk in risks:
            if risk.get('legal_basis'):
                legal_bases.add(risk['legal_basis'])
        
        if legal_bases:
            lines.append("## ⚖️ 法规依据")
            lines.append("")
            for basis in sorted(legal_bases):
                lines.append(f"- {basis}")
            lines.append("")
        
        # 免责声明
        lines.append("---")
        lines.append("")
        lines.append("**免责声明**：本报告由 AI 生成，仅供使用者参考，不构成法律意见。对于重大合同（标的额超过 100 万元或涉及核心商业利益），建议咨询专业执业律师。")
        
        return '\n'.join(lines)
    
    def _generate_json(self, risks: List[Dict], contract_info: Dict,
                       score: int, stats: Dict) -> str:
        """生成 JSON 格式报告"""
        report = {
            'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generated_at': datetime.now().isoformat(),
            'contract_info': contract_info,
            'score': score,
            'statistics': stats,
            'risks': risks,
            'disclaimer': '本报告由 AI 生成，仅供使用者参考，不构成法律意见。',
        }
        return json.dumps(report, ensure_ascii=False, indent=2)


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python generate_report.py <风险JSON文件> [合同信息JSON文件]")
        sys.exit(1)
    
    risks_path = sys.argv[1]
    contract_info_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(risks_path, 'r', encoding='utf-8') as f:
        risks = json.load(f)
    
    contract_info = {}
    if contract_info_path:
        with open(contract_info_path, 'r', encoding='utf-8') as f:
            contract_info = json.load(f)
    
    generator = ReportGenerator()
    report = generator.generate(risks, contract_info)
    
    print(report)


if __name__ == '__main__':
    main()
