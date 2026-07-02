#!/usr/bin/env python3
"""
合同审查主入口
串联完整的工作流程：文本提取 → 结构解析 → 风险审查 → 报告生成
支持实时进度显示
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional
import argparse
import logging

# 自定义日志处理器，同时输出到控制台和文件
class ProgressHandler(logging.Handler):
    """实时进度日志处理器"""
    def __init__(self):
        super().__init__()
        self.steps = []
    
    def emit(self, record):
        msg = self.format(record)
        # 只显示包含特定关键词的日志
        keywords = ['提取', '解析', '规则', 'LLM', '报告', '完成', '发现', '保存']
        if any(kw in msg for kw in keywords):
            print(f"  → {msg}", flush=True)

# 配置日志
progress_handler = ProgressHandler()
progress_handler.setFormatter(logging.Formatter('%(message)s'))
file_handler = logging.FileHandler('review.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[progress_handler, file_handler]
)
logger = logging.getLogger(__name__)


def print_progress(step: str, detail: str = "", done: bool = False):
    """打印实时进度"""
    if done:
        print(f"  ✅ {step} {detail}", flush=True)
    else:
        print(f"  ⏳ {step} {detail}...", flush=True)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='合同智能审查工具')
    parser.add_argument('file', nargs='?', help='合同文件路径（PDF/Word/图片/纯文本）')
    parser.add_argument('--type', '-t', default='', help='合同类型（如不指定则自动识别）')
    parser.add_argument('--role', '-r', default='双方', choices=['甲方', '乙方', '双方'],
                        help='审查视角（默认：双方）')
    parser.add_argument('--output', '-o', default='report.md', help='输出文件路径（默认：report.md）')
    parser.add_argument('--format', '-f', default='markdown', choices=['markdown', 'json'],
                        help='输出格式（默认：markdown）')
    parser.add_argument('--scope', default='全面审查', choices=['全面审查', '重点审查', '快速审查'],
                        help='审查范围（默认：全面审查）')
    parser.add_argument('--no-llm', action='store_true',
                        help='跳过 LLM 审查（仅使用规则引擎）')
    parser.add_argument('--text', '-x', default='', help='直接传入合同文本（而非文件路径）')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    try:
        print("=" * 50, flush=True)
        print("📋 合同智能审查", flush=True)
        print("=" * 50, flush=True)
        
        # 1. 获取合同文本
        print_progress("接收合同文件")
        
        if args.text:
            contract_text = args.text
            file_type = "txt"
            metadata = {}
            print_progress("接收合同文件", "直接文本输入", done=True)
        elif args.file:
            from extract_text import TextExtractor
            extractor = TextExtractor()
            result = extractor.extract(args.file)
            contract_text = result['text']
            file_type = result['file_type']
            metadata = result.get('metadata', {})
            print_progress("接收合同文件", 
                          f"类型={file_type}, 页数={metadata.get('total_pages', '?')}, 字数={metadata.get('total_words', '?')}", 
                          done=True)
        else:
            print("请提供合同文件路径（--file）或合同文本（--text）")
            sys.exit(1)
        
        # 2. 解析合同结构
        print_progress("结构化解析")
        
        from parse_structure import ContractParser
        parser = ContractParser()
        structure = parser.parse(contract_text)
        
        if args.type:
            structure.contract_type = args.type
        
        print_progress("结构化解析", 
                      f"标题={structure.title[:20]}..., 类型={structure.contract_type}, 条款数={len(structure.clauses)}", 
                      done=True)
        
        # 3. 规则引擎检查
        print_progress("规则引擎检查")
        
        from rule_engine import RuleEngine
        rules_path = Path(__file__).parent.parent / 'references' / 'risk_rules.yaml'
        engine = RuleEngine(str(rules_path))
        rule_risks = engine.check_all(contract_text, structure.contract_type, structure.to_dict())
        
        print_progress("规则引擎检查", f"发现 {len(rule_risks)} 个风险点", done=True)
        
        # 4. LLM 审查（可选）
        llm_risks = []
        missing_clauses = []
        special_notes = []
        
        if not args.no_llm:
            print_progress("LLM 语义审查")
            
            from llm_review import LLMReviewer
            reviewer = LLMReviewer()
            llm_result = reviewer.review(
                contract_text=contract_text,
                contract_type=structure.contract_type,
                party_role=args.role,
            )
            llm_risks = llm_result.get('risks', [])
            missing_clauses = llm_result.get('missing_clauses', [])
            special_notes = llm_result.get('special_notes', [])
            
            print_progress("LLM 语义审查", f"发现 {len(llm_risks)} 个风险点", done=True)
        else:
            print("  ⏭️  跳过 LLM 审查（--no-llm）", flush=True)
        
        # 5. 合并风险结果
        print_progress("汇总去重")
        
        all_risks = []
        
        # 添加规则引擎结果
        for r in rule_risks:
            all_risks.append(r.to_dict())
        
        # 添加 LLM 结果
        for r in llm_risks:
            all_risks.append({
                'risk_id': r.get('risk_id', f'LLM_{len(all_risks)+1:03d}'),
                'risk_type': r.get('risk_type', '其他风险'),
                'severity': r.get('severity', '中等'),
                'title': r.get('title', ''),
                'description': r.get('description', ''),
                'suggestion': r.get('suggestion', ''),
                'legal_basis': r.get('legal_basis', ''),
                'text_snippet': r.get('text_snippet', ''),
                'clause_ref': r.get('clause_ref', ''),
                'template': r.get('template', ''),
            })
        
        # 去重（基于风险类型和条款引用）
        seen = set()
        unique_risks = []
        for r in all_risks:
            key = f"{r.get('risk_type', '')}_{r.get('clause_ref', '')}_{r.get('title', '')}"
            if key not in seen:
                seen.add(key)
                unique_risks.append(r)
        
        print_progress("汇总去重", f"去重后 {len(unique_risks)} 个风险点", done=True)
        
        # 6. 生成报告
        print_progress("生成审查报告")
        
        from generate_report import ReportGenerator
        
        contract_info = {
            'title': structure.title,
            'contract_type': structure.contract_type,
            'party_role': args.role,
            'parties': [{'role': p.role, 'name': p.name} for p in structure.parties],
            'total_amount': structure.total_amount,
            'currency': structure.currency,
            'missing_clauses': missing_clauses,
            'special_notes': special_notes,
        }
        
        generator = ReportGenerator()
        report = generator.generate(unique_risks, contract_info, args.format)
        
        print_progress("生成审查报告", done=True)
        
        # 7. 输出
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print_progress("保存报告", f"路径={args.output}", done=True)
        
        elapsed = time.time() - start_time
        
        print("", flush=True)
        print("=" * 50, flush=True)
        print(f"✅ 审查完成！耗时 {elapsed:.1f} 秒", flush=True)
        print("=" * 50, flush=True)
        print("", flush=True)
        
        print(report)
        
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        sys.exit(1)
    except ImportError as e:
        logger.error(f"依赖缺失: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"审查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
