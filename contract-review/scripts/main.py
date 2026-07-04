#!/usr/bin/env python3
"""
合同审查主入口 v2.0
串联完整的工作流程：文本提取 → 结构解析 → 风险审查 → 报告生成
新增：首次使用向导、Ollama 一键安装、更友好的错误提示
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional
import argparse
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_step(step_num: int, total: int, message: str):
    """打印进度步骤"""
    print(f"\n[{step_num}/{total}] {message}", flush=True)


def print_success(message: str):
    """打印成功信息"""
    print(f"  ✅ {message}", flush=True)


def print_warning(message: str):
    """打印警告信息"""
    print(f"  ⚠️  {message}", flush=True)


def print_error(message: str):
    """打印错误信息"""
    print(f"  ❌ {message}", flush=True)


def print_progress(step: str, detail: str = "", done: bool = False):
    """打印实时进度"""
    if done:
        print(f"  ✅ {step} {detail}", flush=True)
    else:
        print(f"  ⏳ {step} {detail}...", flush=True)


def check_ollama_installed() -> bool:
    """检查 Ollama 是否已安装"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def install_ollama():
    """一键安装 Ollama"""
    print("\n" + "=" * 50)
    print("🦙 Ollama 本地模型安装向导")
    print("=" * 50)
    print()
    print("Ollama 允许您在本地运行 AI 模型，无需 API 密钥。")
    print()
    
    if check_ollama_installed():
        print("✅ Ollama 已安装！")
        
        # 检查模型
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if 'qwen' in result.stdout.lower() or 'llama' in result.stdout.lower():
                print("✅ 已检测到本地模型。")
                return True
            else:
                print("⏳ 检测到 Ollama，但未安装中文模型。")
                print()
                install_model = input("是否下载中文模型 qwen2.5:7b（约 4.7GB）？[y/N]: ").strip().lower()
                if install_model in ('y', 'yes', '是'):
                    print("⏳ 正在下载模型（可能需要几分钟）...")
                    subprocess.run(['ollama', 'pull', 'qwen2.5:7b'], check=True)
                    print("✅ 模型下载完成！")
                    return True
                else:
                    print("您可以稍后手动运行: ollama pull qwen2.5:7b")
                    return True
        except Exception:
            pass
        
        return True
    
    print("Ollama 未安装。请选择安装方式：")
    print()
    print("1. macOS / Linux（一键安装）")
    print("   运行: curl -fsSL https://ollama.ai/install.sh | sh")
    print()
    print("2. Windows")
    print("   访问 https://ollama.ai/download 下载 OllamaSetup.exe")
    print()
    
    open_browser = input("是否打开 Ollama 下载页面？[y/N]: ").strip().lower()
    if open_browser in ('y', 'yes', '是'):
        import webbrowser
        webbrowser.open('https://ollama.ai/download')
    
    return False


def first_time_setup():
    """首次使用向导"""
    config_path = Path.home() / '.contract-review' / 'config.json'
    
    if config_path.exists():
        return True
    
    print("\n" + "=" * 50)
    print("🎉 欢迎使用合同智能审查！")
    print("=" * 50)
    print()
    print("本工具支持以下运行模式：")
    print()
    print("  🥇 最佳体验：安装 Ollama（免费本地模型）")
    print("     - 完全本地运行，保护隐私")
    print("     - 无需 API 密钥")
    print("     - 首次下载模型约 4-8GB")
    print()
    print("  🥈 高级体验：配置 OpenAI API")
    print("     - 设置环境变量 OPENAI_API_KEY")
    print("     - 需要付费，但效果最佳")
    print()
    print("  🥉 基础体验：仅规则引擎")
    print("     - 开箱即用，无需额外配置")
    print("     - 覆盖常见风险点")
    print()
    
    choice = input("请选择 [1/2/3，默认 3]: ").strip() or "3"
    
    if choice == "1":
        install_ollama()
    elif choice == "2":
        print()
        print("请设置环境变量：")
        print("  Windows: set OPENAI_API_KEY=sk-xxx")
        print("  macOS/Linux: export OPENAI_API_KEY=sk-xxx")
    else:
        print("已选择基础模式。您可以随时通过安装 Ollama 升级到完整体验。")
    
    # 保存配置
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        'setup_completed': True,
        'mode': 'ollama' if choice == '1' else 'openai' if choice == '2' else 'basic'
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='合同智能审查工具 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/main.py 合同.pdf                    # 基础审查
  python scripts/main.py 合同.pdf --role 甲方        # 从甲方视角审查
  python scripts/main.py 合同.pdf --install-ollama   # 安装本地模型
  python scripts/main.py 合同.pdf --first-time       # 首次使用向导
        """
    )
    parser.add_argument('file', nargs='?', help='合同文件路径（PDF/Word/图片/纯文本）')
    parser.add_argument('--type', '-t', default='', help='合同类型（如不指定则自动识别）')
    parser.add_argument('--role', '-r', default='双方', choices=['甲方', '乙方', '双方'],
                        help='审查视角（默认：双方）')
    parser.add_argument('--output', '-o', default='', help='输出文件路径（默认：report.md）')
    parser.add_argument('--format', '-f', default='markdown', choices=['markdown', 'json'],
                        help='输出格式（默认：markdown）')
    parser.add_argument('--scope', default='全面审查', choices=['全面审查', '重点审查', '快速审查'],
                        help='审查范围（默认：全面审查）')
    parser.add_argument('--no-llm', action='store_true',
                        help='跳过 LLM 审查（仅使用规则引擎）')
    parser.add_argument('--text', '-x', default='', help='直接传入合同文本（而非文件路径）')
    parser.add_argument('--install-ollama', action='store_true',
                        help='一键安装 Ollama 本地模型')
    parser.add_argument('--first-time', action='store_true',
                        help='首次使用向导')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    # 特殊命令
    if args.first_time:
        first_time_setup()
        if not args.file:
            return
    
    if args.install_ollama:
        install_ollama()
        if not args.file:
            return
    
    try:
        print("\n" + "=" * 50, flush=True)
        print("📋 合同智能审查 v2.0", flush=True)
        print("=" * 50, flush=True)
        
        total_steps = 5
        
        # Step 1: 获取合同文件
        print_step(1, total_steps, "接收合同文件")
        
        if args.text:
            contract_text = args.text
            file_type = "txt"
            metadata = {}
            print_success(f"收到文本输入（{len(contract_text)} 字符）")
        elif args.file:
            from extract_text import TextExtractor
            extractor = TextExtractor(enable_security=True)
            result = extractor.extract(args.file)
            contract_text = result['text']
            file_type = result['file_type']
            metadata = result.get('metadata', {})
            warnings = result.get('warnings', [])
            
            print_success(
                f"文件类型={file_type}, "
                f"页数={metadata.get('total_pages', '?')}, "
                f"字数={metadata.get('total_words', '?')}"
            )
            
            if result.get('ocr_confidence'):
                conf = result['ocr_confidence']
                if conf >= 0.95:
                    print_success(f"OCR 置信度: {conf:.0%}")
                else:
                    print_warning(f"OCR 置信度: {conf:.0%}，建议核对扫描件")
            
            for w in warnings:
                print_warning(w)
        else:
            print_error("请提供合同文件路径或文本内容")
            print("  --file <路径>    上传合同文件")
            print("  --text \"内容\"    直接审查文本")
            print("  --first-time     首次使用向导")
            sys.exit(1)
        
        # Step 2: 结构解析
        print_step(2, total_steps, "结构化解析")
        
        from parse_structure import ContractParser
        parser = ContractParser()
        structure = parser.parse(contract_text)
        
        if args.type:
            structure.contract_type = args.type
        
        print_success(
            f"标题={structure.title[:30] if structure.title else '未知'}, "
            f"类型={structure.contract_type}, "
            f"条款数={len(structure.clauses)}"
        )
        
        # Step 3: 规则引擎检查
        print_step(3, total_steps, "规则引擎检查")
        
        from rule_engine import RuleEngine
        rules_path = Path(__file__).parent.parent / 'references' / 'risk_rules.yaml'
        engine = RuleEngine(str(rules_path))
        rule_risks = engine.check_all(contract_text, structure.contract_type, structure.to_dict())
        
        print_success(f"完成 {len(rule_risks)} 项硬规则检查")
        
        # Step 4: LLM 审查（可选）
        print_step(4, total_steps, "AI 语义审查")
        
        llm_risks = []
        missing_clauses = []
        special_notes = []
        
        if not args.no_llm:
            from llm_review import LLMReviewer
            reviewer = LLMReviewer()
            
            if reviewer.backend != "none":
                print(f"  🤖 使用 {reviewer.backend} / {reviewer.model}")
                llm_result = reviewer.review(
                    contract_text=contract_text,
                    contract_type=structure.contract_type,
                    party_role=args.role,
                )
                llm_risks = llm_result.get('risks', [])
                missing_clauses = llm_result.get('missing_clauses', [])
                special_notes = llm_result.get('special_notes', [])
                
                print_success(f"发现 {len(llm_risks)} 个 AI 识别风险")
                
                for note in special_notes:
                    print_warning(note)
            else:
                print_warning("未检测到 LLM 后端，仅使用规则引擎结果")
                print("  💡 安装 Ollama 后可启用完整 AI 审查功能")
                special_notes.append("LLM 审查未启用（未检测到 OpenAI API 或本地模型）")
        else:
            print("  ⏭️  跳过 LLM 审查（--no-llm）")
        
        # Step 5: 生成报告
        print_step(5, total_steps, "生成审查报告")
        
        all_risks = []
        
        for r in rule_risks:
            all_risks.append(r.to_dict())
        
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
        
        # 去重
        seen = set()
        unique_risks = []
        for r in all_risks:
            key = f"{r.get('risk_type', '')}_{r.get('clause_ref', '')}_{r.get('title', '')}"
            if key not in seen:
                seen.add(key)
                unique_risks.append(r)
        
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
        
        print_success("报告生成完成")
        
        # 输出
        output_path = args.output or 'report.md'
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print_success(f"报告已保存至: {output_path}")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 50, flush=True)
        print(f"🎉 审查完成！耗时 {elapsed:.1f} 秒", flush=True)
        print("=" * 50, flush=True)
        print(flush=True)
        
        print(report)
        
    except FileNotFoundError as e:
        print_error(f"文件不存在: {e}")
        sys.exit(1)
    except ImportError as e:
        print_error(f"依赖缺失: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print_error(f"审查失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
