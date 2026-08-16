"""CLI entry point for CN Model Gateway."""
from __future__ import annotations

import argparse
import sys
import os
import time
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.adapters.base import ChatMessage
from src.router import ModelRouter
from src.monitor import Monitor
from src.mcp_server import MCPServer
from src.utils import load_config, get_default_config_path, mask_api_key
from src.benchmark import BenchmarkSuite
from src.price_tracker import PriceTracker


def cmd_run(args: argparse.Namespace) -> None:
    """Run the MCP server."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    availability = router.register_all(config)
    monitor = Monitor()
    server = MCPServer(router, monitor)

    # Print startup info to stderr (stdout is JSON-RPC)
    available = router.list_available()
    print(f"[cn-model-gateway] 已加载 {len(available)} 个提供商: {available}", file=sys.stderr)
    print(f"[cn-model-gateway] MCP 服务器已启动 (stdio 模式)", file=sys.stderr)
    print(f"[cn-model-gateway] 故障转移: {'开启' if not args.no_failover else '关闭'}, 超时: {args.timeout}s", file=sys.stderr)
    server.run_stdio()


def cmd_ask(args: argparse.Namespace) -> None:
    """Ask a single question (single provider or multi-provider compare)."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    router.register_all(config)

    question = args.question or input("请输入问题: ")
    msgs = [ChatMessage(role="user", content=question)]

    # v1.5.0: Support --providers for multi-provider compare
    if hasattr(args, 'providers') and args.providers and len(args.providers) >= 2:
        try:
            results = router.compare_models(msgs, providers=args.providers)
            for provider, info in results.items():
                print(f"\n### {provider}")
                if "error" in info:
                    print(f"  ❌ {info['error']}")
                else:
                    print(f"  [{info['model']}] ({info['duration_ms']}ms)")
                    print(f"  {info['content'][:150]}...")
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Single provider mode
    try:
        resp = router.chat(msgs, provider=args.provider)
        print(f"\n[{resp.provider}/{resp.model}] ({resp.duration_ms}ms)")
        print("-" * 40)
        print(resp.content)
        print("-" * 40)
        print(f"Tokens: prompt={resp.usage.get('prompt_tokens', '?')}, "
              f"completion={resp.usage.get('completion_tokens', '?')}")
        # v1.5.0: Show tool_calls if present
        if resp.tool_calls:
            print(f"\nTool Calls:")
            for tc in resp.tool_calls:
                print(f"  - {tc.name}({tc.arguments})")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_describe_image(args: argparse.Namespace) -> None:
    """Describe an image using vision models."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    router.register_all(config)

    image = args.image or input("请输入图片 URL/路径: ")
    prompt = args.prompt or "请描述这张图片"

    # Find adapter
    adapter = None
    if args.provider:
        adapter = router.get_adapter(args.provider)
    else:
        available = router.list_available()
        if available:
            adapter = router.get_adapter(available[0])

    if not adapter:
        print("没有可用的模型提供商。", file=sys.stderr)
        sys.exit(1)

    try:
        resp = adapter.describe_image(image, prompt, model=args.model)
        print(f"\n[{resp.provider}/{resp.model}] ({resp.duration_ms}ms)")
        print("-" * 40)
        print(resp.content)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    """Show status of all providers."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    availability = router.register_all(config)
    print("\n📋 模型提供商状态")
    print("-" * 40)
    for provider, available in availability.items():
        status = "✅ 可用" if available else "❌ 不可用 / 未配置"
        print(f"  {provider}: {status}")
    print()


def cmd_stats(args: argparse.Namespace) -> None:
    """Show usage statistics."""
    monitor = Monitor()
    stats = monitor.get_stats()
    print("\n📊 使用统计")
    print("-" * 40)
    print(f"今日调用: {stats['today'].get('total_calls', 0)} 次")
    print(f"总调用: {stats['total']['calls']} 次")
    print(f"按提供商: {stats.get('by_provider', {})}")
    print(f"硬件: {stats['hardware']}")
    print(f"并发限制: {stats['concurrency_limit']}")
    print()


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Run model performance benchmark."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    router.register_all(config)

    suite = BenchmarkSuite()
    dimensions = args.dimensions.split(",") if args.dimensions else None
    max_questions = args.max_questions or None

    try:
        results = suite.run_benchmark(
            router,
            providers=args.providers,
            dimensions=dimensions,
            max_questions=max_questions,
        )
        print("\n" + suite.generate_radar_chart(results))
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_benchmark_history(args: argparse.Namespace) -> None:
    """Show benchmark history."""
    suite = BenchmarkSuite()
    history = suite.get_history(limit=args.limit or 10)
    if not history:
        print("暂无跑分历史")
        return

    print("\n📊 跑分历史")
    print("-" * 60)
    for run in history:
        print(f"  Run ID: {run['run_id']}")
        print(f"  时间: {time.strftime('%Y-%m-%d %H:%M', time.localtime(run['timestamp']))}")
        print(f"  提供商: {run['providers_tested']}")
        print(f"  维度: {run['dimensions_tested']}")
        print()


def cmd_price(args: argparse.Namespace) -> None:
    """Show current model prices."""
    tracker = PriceTracker()
    print(tracker.generate_price_table())


def cmd_price_history(args: argparse.Namespace) -> None:
    """Show price history for a provider."""
    tracker = PriceTracker()
    if not args.provider:
        print("请指定提供商: price history -p <provider>")
        return
    print(tracker.generate_trend_chart(args.provider))


def cmd_cost_predict(args: argparse.Namespace) -> None:
    """Predict monthly cost based on usage."""
    tracker = PriceTracker()
    # Example usage: 1M tokens per provider
    usage = {}
    for provider in ["deepseek", "tongyi", "zhipu", "kimi", "hunyuan", "doubao"]:
        usage[provider] = args.tokens or 1000000
    result = tracker.predict_cost(usage)
    print("\n💰 月度成本预测")
    print("-" * 40)
    for provider, pred in result["predictions"].items():
        print(f"  {provider}: ¥{pred['estimated_cost']} ({pred['tokens']} tokens)")
    print(f"\n总计: ¥{result['total_estimated_cost']}")
    print(f"备注: {result['note']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cn-model-gateway",
        description="国产模型 MCP 服务器 - DeepSeek/通义/智谱/Kimi/混元/豆包一站式接入",
    )
    parser.add_argument("-c", "--config", help="config.json 路径")
    parser.add_argument("-t", "--timeout", type=int, default=30,
                        help="API 调用超时秒数 (默认 30)")
    parser.add_argument("--no-failover", action="store_true",
                        help="关闭故障转移（auto 模式只试一家，不自动切备用）")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # run - MCP server
    run_parser = subparsers.add_parser("run", help="启动 MCP 服务器 (stdio 模式)")
    run_parser.set_defaults(func=cmd_run)

    # ask - single question or multi-provider compare
    ask_parser = subparsers.add_parser("ask", help="直接提问（--providers 指定多家时对比）")
    ask_parser.add_argument("question", nargs="?", help="要提问的内容")
    ask_parser.add_argument("-p", "--provider", help="指定提供商（单家模式）")
    ask_parser.add_argument("--providers", nargs="+", help="对比多家提供商（指定 2 家及以上）")
    ask_parser.set_defaults(func=cmd_ask)

    # describe_image - vision model
    img_parser = subparsers.add_parser("describe_image", help="描述图片/回答图片问题")
    img_parser.add_argument("image", nargs="?", help="图片 URL/base64/文件路径")
    img_parser.add_argument("--prompt", help="关于图片的问题（默认：请描述这张图片）")
    img_parser.add_argument("-p", "--provider", help="指定提供商")
    img_parser.add_argument("--model", help="具体模型 ID")
    img_parser.set_defaults(func=cmd_describe_image)

    # status - show provider status
    status_parser = subparsers.add_parser("status", help="显示提供商状态")
    status_parser.set_defaults(func=cmd_status)

    # stats - show usage statistics
    stats_parser = subparsers.add_parser("stats", help="显示使用统计")
    stats_parser.set_defaults(func=cmd_stats)

    # benchmark - run performance benchmark
    bench_parser = subparsers.add_parser("benchmark", help="运行模型性能基准测试")
    bench_parser.add_argument("-p", "--providers", nargs="+", help="要测试的提供商列表")
    bench_parser.add_argument("-d", "--dimensions", help="要测试的维度（逗号分隔）")
    bench_parser.add_argument("-q", "--max-questions", type=int, help="每个维度最大题目数")
    bench_parser.set_defaults(func=cmd_benchmark)

    # benchmark history
    bench_hist_parser = subparsers.add_parser("benchmark-history", help="显示跑分历史")
    bench_hist_parser.add_argument("-l", "--limit", type=int, help="显示条数")
    bench_hist_parser.set_defaults(func=cmd_benchmark_history)

    # price - show current prices
    price_parser = subparsers.add_parser("price", help="显示当前模型价格")
    price_parser.set_defaults(func=cmd_price)

    # price history
    price_hist_parser = subparsers.add_parser("price-history", help="显示价格趋势")
    price_hist_parser.add_argument("-p", "--provider", help="提供商名称")
    price_hist_parser.set_defaults(func=cmd_price_history)

    # cost predict
    cost_parser = subparsers.add_parser("cost-predict", help="预测月度成本")
    cost_parser.add_argument("-t", "--tokens", type=int, help="每月 token 数")
    cost_parser.set_defaults(func=cmd_cost_predict)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
