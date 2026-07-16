"""CLI entry point for CN Model Gateway."""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.adapters.base import ChatMessage
from src.router import ModelRouter
from src.monitor import Monitor
from src.mcp_server import MCPServer
from src.utils import load_config, get_default_config_path, mask_api_key


def cmd_run(args: argparse.Namespace) -> None:
    """Run the MCP server."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter()
    availability = router.register_all(config)
    monitor = Monitor()
    server = MCPServer(router, monitor)

    # Print startup info to stderr (stdout is JSON-RPC)
    available = router.list_available()
    print(f"[cn-model-gateway] 已加载 {len(available)} 个提供商: {available}", file=sys.stderr)
    print(f"[cn-model-gateway] MCP 服务器已启动 (stdio 模式)", file=sys.stderr)
    server.run_stdio()


def cmd_ask(args: argparse.Namespace) -> None:
    """Ask a single question directly."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter()
    router.register_all(config)

    question = args.question or input("请输入问题: ")
    msgs = [ChatMessage(role="user", content=question)]
    try:
        resp = router.chat(msgs, provider=args.provider)
        print(f"\n[{resp.provider}/{resp.model}] ({resp.duration_ms}ms)")
        print("-" * 40)
        print(resp.content)
        print("-" * 40)
        print(f"Tokens: prompt={resp.usage.get('prompt_tokens', '?')}, "
              f"completion={resp.usage.get('completion_tokens', '?')}")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_compare(args: argparse.Namespace) -> None:
    """Compare models."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter()
    router.register_all(config)

    question = args.question or input("请输入问题: ")
    msgs = [ChatMessage(role="user", content=question)]
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


def cmd_status(args: argparse.Namespace) -> None:
    """Show status of all providers."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter()
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


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cn-model-gateway",
        description="国产模型 MCP 服务器 - DeepSeek/通义/智谱/Kimi/混元/豆包一站式接入",
    )
    parser.add_argument("-c", "--config", help="config.json 路径")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # run - MCP server
    run_parser = subparsers.add_parser("run", help="启动 MCP 服务器 (stdio 模式)")
    run_parser.set_defaults(func=cmd_run)

    # ask - single question
    ask_parser = subparsers.add_parser("ask", help="直接提问")
    ask_parser.add_argument("question", nargs="?", help="要提问的内容")
    ask_parser.add_argument("-p", "--provider", help="指定提供商")
    ask_parser.set_defaults(func=cmd_ask)

    # compare - multi-model compare
    cmp_parser = subparsers.add_parser("compare", help="对比多个模型回答")
    cmp_parser.add_argument("question", nargs="?", help="要提问的内容")
    cmp_parser.add_argument("-p", "--providers", nargs="+", help="要对比的提供商列表")
    cmp_parser.set_defaults(func=cmd_compare)

    # status - show provider status
    status_parser = subparsers.add_parser("status", help="显示提供商状态")
    status_parser.set_defaults(func=cmd_status)

    # stats - show usage statistics
    stats_parser = subparsers.add_parser("stats", help="显示使用统计")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
