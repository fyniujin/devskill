"""CLI entry point for CN Model Gateway.

v1.6.0: Added 4 new subcommands (embed, rerank, transcribe, video)
        via shared llm_core kernel.
"""
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

    try:
        resp = router.chat(msgs, provider=args.provider)
        print(f"\n[{resp.provider}/{resp.model}] ({resp.duration_ms}ms)")
        print("-" * 40)
        print(resp.content)
        print("-" * 40)
        print(f"Tokens: prompt={resp.usage.get('prompt_tokens', '?')}, "
              f"completion={resp.usage.get('completion_tokens', '?')}")
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


# --- v1.6.0: 4 new CLI subcommands ---

def cmd_embed(args: argparse.Namespace) -> None:
    """Generate text embeddings."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    router.register_all(config)

    texts = args.texts or []
    if not texts:
        # Read from stdin if not provided
        texts = [input("请输入要嵌入的文本: ")]

    adapter = None
    if args.provider:
        adapter = router.get_adapter(args.provider)
    else:
        for p in router.list_available():
            a = router.get_adapter(p)
            if a and hasattr(a, 'embed_text'):
                from src.adapters.base import BaseAdapter
                if a.embed_text.__func__ is not BaseAdapter.embed_text:
                    adapter = a
                    break
        if not adapter:
            available = router.list_available()
            if available:
                adapter = router.get_adapter(available[0])

    if not adapter:
        print("没有可用的模型提供商。", file=sys.stderr)
        sys.exit(1)

    try:
        result = adapter.embed_text(texts, model=args.model)
        print(f"\n[{result.provider}/{result.model}] ({result.duration_ms}ms)")
        print(f"嵌入数量: {len(result.embeddings)}")
        print(f"嵌入维度: {len(result.embeddings[0]) if result.embeddings else 0}")
        print(f"Token: {result.usage}")
        if args.verbose and result.embeddings:
            print(f"\n嵌入向量 (前3个前5维):")
            for i, emb in enumerate(result.embeddings[:3]):
                print(f"  [{i}]: {emb[:5]}...")
    except NotImplementedError as e:
        print(f"不支持: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_rerank(args: argparse.Namespace) -> None:
    """Rerank documents by relevance to query."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    router.register_all(config)

    query = args.query or input("请输入查询: ")
    documents = args.documents or []
    if not documents:
        print("请输入文档（每行一个，空行结束）:")
        while True:
            line = input()
            if not line:
                break
            documents.append(line)

    adapter = None
    if args.provider:
        adapter = router.get_adapter(args.provider)
    else:
        for p in router.list_available():
            a = router.get_adapter(p)
            if a and hasattr(a, 'rerank'):
                from src.adapters.base import BaseAdapter
                if a.rerank.__func__ is not BaseAdapter.rerank:
                    adapter = a
                    break
        if not adapter:
            available = router.list_available()
            if available:
                adapter = router.get_adapter(available[0])

    if not adapter:
        print("没有可用的模型提供商。", file=sys.stderr)
        sys.exit(1)

    try:
        result = adapter.rerank(query, documents, model=args.model)
        print(f"\n[{result.provider}/{result.model}] ({result.duration_ms}ms)")
        print(f"Token: {result.usage}\n")
        for i, score in enumerate(result.scores):
            doc_preview = documents[i][:60] + "..." if len(documents[i]) > 60 else documents[i]
            print(f"  [{i+1}] {score:.4f} | {doc_preview}")
    except NotImplementedError as e:
        print(f"不支持: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_transcribe(args: argparse.Namespace) -> None:
    """Transcribe audio to text."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    router.register_all(config)

    audio = args.audio or input("请输入音频文件路径/URL: ")

    adapter = None
    if args.provider:
        adapter = router.get_adapter(args.provider)
    else:
        for p in router.list_available():
            a = router.get_adapter(p)
            if a and hasattr(a, 'audio_transcribe'):
                from src.adapters.base import BaseAdapter
                if a.audio_transcribe.__func__ is not BaseAdapter.audio_transcribe:
                    adapter = a
                    break
        if not adapter:
            available = router.list_available()
            if available:
                adapter = router.get_adapter(available[0])

    if not adapter:
        print("没有可用的模型提供商。", file=sys.stderr)
        sys.exit(1)

    try:
        kwargs = {}
        if args.language:
            kwargs["language"] = args.language
        result = adapter.audio_transcribe(audio, model=args.model, **kwargs)
        print(f"\n[{result.provider}/{result.model}] ({result.duration_ms}ms)")
        print(f"语言: {result.language}\n")
        print(f"识别文本:\n{result.text}")
    except NotImplementedError as e:
        print(f"不支持: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_video(args: argparse.Namespace) -> None:
    """Understand video content."""
    config_path = args.config or get_default_config_path()
    config = load_config(config_path)
    router = ModelRouter(timeout=args.timeout, failover=not args.no_failover)
    router.register_all(config)

    video = args.video or input("请输入视频文件路径/URL: ")
    prompt = args.prompt or "请描述这个视频的内容"

    adapter = None
    if args.provider:
        adapter = router.get_adapter(args.provider)
    else:
        for p in router.list_available():
            a = router.get_adapter(p)
            if a and hasattr(a, 'video_understand'):
                from src.adapters.base import BaseAdapter
                if a.video_understand.__func__ is not BaseAdapter.video_understand:
                    adapter = a
                    break
        if not adapter:
            available = router.list_available()
            if available:
                adapter = router.get_adapter(available[0])

    if not adapter:
        print("没有可用的模型提供商。", file=sys.stderr)
        sys.exit(1)

    try:
        result = adapter.video_understand(video, prompt, model=args.model)
        print(f"\n[{result.provider}/{result.model}] ({result.duration_ms}ms)")
        print(f"关键帧数: {result.keyframe_count}\n")
        print(f"视频描述:\n{result.description}")
    except NotImplementedError as e:
        print(f"不支持: {e}", file=sys.stderr)
        sys.exit(1)
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
        print("请指定提供商: price-history -p <provider>")
        return
    print(tracker.generate_trend_chart(args.provider))


def cmd_cost_predict(args: argparse.Namespace) -> None:
    """Predict monthly cost based on usage."""
    tracker = PriceTracker()
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

    # v1.6.0: embed - text embeddings
    embed_parser = subparsers.add_parser("embed", help="生成文本向量嵌入")
    embed_parser.add_argument("texts", nargs="*", help="要嵌入的文本（不指定则交互输入）")
    embed_parser.add_argument("-p", "--provider", help="指定提供商")
    embed_parser.add_argument("--model", help="嵌入模型 ID")
    embed_parser.add_argument("-v", "--verbose", action="store_true", help="显示完整嵌入向量")
    embed_parser.set_defaults(func=cmd_embed)

    # v1.6.0: rerank - document reranking
    rerank_parser = subparsers.add_parser("rerank", help="按查询相关性重排序文档")
    rerank_parser.add_argument("-q", "--query", help="查询文本")
    rerank_parser.add_argument("-d", "--documents", nargs="*", help="待排序文档")
    rerank_parser.add_argument("-p", "--provider", help="指定提供商")
    rerank_parser.add_argument("--model", help="重排序模型 ID")
    rerank_parser.set_defaults(func=cmd_rerank)

    # v1.6.0: transcribe - audio transcription
    transcribe_parser = subparsers.add_parser("transcribe", help="语音转文字")
    transcribe_parser.add_argument("audio", nargs="?", help="音频文件路径/URL")
    transcribe_parser.add_argument("-p", "--provider", help="指定提供商")
    transcribe_parser.add_argument("--model", help="语音识别模型 ID")
    transcribe_parser.add_argument("--language", help="音频语言（默认自动检测）")
    transcribe_parser.set_defaults(func=cmd_transcribe)

    # v1.6.0: video - video understanding
    video_parser = subparsers.add_parser("video", help="理解视频内容（关键帧+视觉描述）")
    video_parser.add_argument("video", nargs="?", help="视频文件路径/URL")
    video_parser.add_argument("--prompt", help="描述提示（默认：请描述这个视频的内容）")
    video_parser.add_argument("-p", "--provider", help="指定提供商")
    video_parser.add_argument("--model", help="视觉模型 ID")
    video_parser.set_defaults(func=cmd_video)

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
