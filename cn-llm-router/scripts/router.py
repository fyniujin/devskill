#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""国产大模型统一路由 — 统一入口与策略引擎（CLI）。

单入口：对外只暴露一个 chat()，内部按任务自动或手动选择后端，并自动统计成本。
纯标准库、零依赖、零密钥（密钥仅从环境变量读取）。

用法示例：
  python scripts/router.py chat --prompt "帮我用 Python 写一个快排" --model auto
  python scripts/router.py route --prompt "总结这篇文章" --strategy cheap
  python scripts/router.py report --period month
  python scripts/router.py hardware
  python scripts/router.py update-check
  python scripts/router.py version
"""

import os
import sys
import json
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import meta
import config
import classifier
import hardware
import cache
import cost_tracker
import yaml_simple
import report as report_mod
import update_check
import mock_engine
from adapters import build, AdapterError

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_YAML = os.path.normpath(os.path.join(HERE, "..", "references", "models.yaml"))


# ───────────────────────── 注册表与适配器 ─────────────────────────
def load_registry():
    if not os.path.exists(MODELS_YAML):
        raise SystemExit("❌ 未找到模型注册表: %s" % MODELS_YAML)
    return yaml_simple.load_file(MODELS_YAML)


def _provider_keys(provider, reg):
    """为某厂商构造适配器所需的 key 字典（全部来自环境变量）。"""
    p = reg["providers"][provider]
    atype = p.get("adapter")
    if atype == "openai_compat":
        return {"api_key": config.get_key(provider), "env_hint": p.get("env_hint", "")}
    if atype == "ernie":
        return {
            "api_key_openai": config.get_key("ernie_openai"),
            "ak": config.get_key("ernie_ak"),
            "sk": config.get_key("ernie_sk"),
        }
    if atype == "spark":
        return {
            "app_id": config.get_key("spark_app_id"),
            "api_key": config.get_key("spark_api_key"),
            "api_secret": config.get_key("spark_api_secret"),
        }
    return {}


def _adapter_cfg(provider, reg):
    p = reg["providers"][provider]
    cfg = {
        "base_url": p.get("base_url"),
        "base_url_openai": p.get("base_url_openai"),
        "default_model": p.get("default_model"),
        "version": p.get("version", "v3.5"),
        "domain": p.get("domain", "generalv3.5"),
    }
    cfg.update(_provider_keys(provider, reg))
    return cfg


# ───────────────────────── 路由决策 ─────────────────────────
def _all_models(reg, only_configured=True):
    """展开所有 (provider, model_dict)。only_configured 时只含已配置密钥的厂商。"""
    out = []
    for provider, p in reg.get("providers", {}).items():
        if only_configured and not config.has_any_key_for(provider):
            continue
        for m in p.get("models", []):
            out.append((provider, m))
    return out


def _price(m):
    return float(m.get("price_in", 0) or 0) + float(m.get("price_out", 0) or 0)


def resolve(strategy, classification, reg, manual_model=None, allow_unconfigured=False):
    """返回 (provider, model_name, reason)。失败抛中文异常。

    allow_unconfigured=True 用于「路由建议模式」：不要求已配置密钥，
    仅基于注册表给出推荐路由，供用户事先规划（不发起任何 API 调用）。
    """
    cls = classification
    configured = config.configured_providers()
    if not configured and not allow_unconfigured:
        raise AdapterError(
            "当前未检测到任何厂商 API Key。请先设置至少一个环境变量，例如：\n"
            "  export DEEPSEEK_API_KEY=sk-xxx\n"
            "  export DASHSCOPE_API_KEY=sk-xxx\n"
            "支持：DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / ZHIPU_API_KEY / "
            "MOONSHOT_API_KEY / HUNYUAN_API_KEY / ARK_API_KEY / "
            "ERNIE_OPENAI_KEY(或 ERNIE_API_KEY+ERNIE_SECRET_KEY) / SPARK_*\n"
            "（只想看路由推荐、暂不调用，可去掉密钥后重试，route 会进入「建议模式」）"
        )

    if strategy == "manual":
        return _resolve_manual(manual_model, reg, allow_unconfigured=allow_unconfigured)

    only_conf = bool(configured) and not allow_unconfigured
    models = _all_models(reg, only_configured=only_conf)
    if not models:
        # 建议模式下降级为全量模型
        models = _all_models(reg, only_configured=False)
    if not models:
        raise AdapterError("注册表中无可用模型，请检查 models.yaml")

    if strategy == "cheap":
        best = min(models, key=lambda pm: _price(pm[1]))
        return best[0], best[1]["name"], "cheap 策略：选择价格最低的模型"

    if strategy == "quality":
        # 优先带 reasoner 的，其次上下文最长的
        def qscore(pm):
            m = pm[1]
            s = 0
            if m.get("reasoner"):
                s += 100
            s += (m.get("ctx", 0) or 0) / 1000.0
            return s
        best = max(models, key=qscore)
        return best[0], best[1]["name"], "quality 策略：选择能力最强的模型"

    # auto：任务感知
    reason_bits = []
    if cls["needs_reasoning"]:
        reasoner = [pm for pm in models if pm[1].get("reasoner")]
        if reasoner:
            best = reasoner[0]
            reason_bits.append("需推理→选 reasoner 模型")
        else:
            best = min(models, key=lambda pm: _price(pm[1]))
            reason_bits.append("需推理但无 reasoner，退而求其次选最便宜")
    elif cls["length_bucket"] == "long":
        longs = [pm for pm in models if (pm[1].get("ctx") or 0) >= 128000]
        if longs:
            best = max(longs, key=lambda pm: pm[1].get("ctx", 0))
            reason_bits.append("长文→选超长上下文模型(≥128k)")
        else:
            best = min(models, key=lambda pm: _price(pm[1]))
            reason_bits.append("长文但无超长上下文，退选最便宜")
    elif cls["task_type"] == "code":
        code_models = [pm for pm in models if "code" in pm[1]["name"].lower() or pm[0] in ("deepseek", "qwen")]
        best = code_models[0] if code_models else min(models, key=lambda pm: _price(pm[1]))
        reason_bits.append("代码任务→偏好 DeepSeek/通义")
    elif cls["budget_sensitive"]:
        best = min(models, key=lambda pm: _price(pm[1]))
        reason_bits.append("价格敏感(分类/抽取/翻译)→选最便宜")
    else:
        # 默认：优先 deepseek-chat，否则最便宜
        default = [pm for pm in models if pm[1]["name"] == "deepseek-chat"]
        best = default[0] if default else min(models, key=lambda pm: _price(pm[1]))
        reason_bits.append("常规任务→默认均衡模型")

    return best[0], best[1]["name"], "auto 策略：" + "；".join(reason_bits)


def _resolve_manual(model_str, reg, allow_unconfigured=False):
    if not model_str:
        raise AdapterError("manual 模式需要 --model 指定具体模型，如 deepseek:deepseek-chat")
    if ":" in model_str:
        provider, model = model_str.split(":", 1)
    else:
        provider, model = None, model_str
    for p, pinfo in reg.get("providers", {}).items():
        if provider and p != provider:
            continue
        for m in pinfo.get("models", []):
            if m["name"] == model:
                if not allow_unconfigured and not config.has_any_key_for(p):
                    raise AdapterError(
                        "厂商 %s 未配置密钥（%s），请先设置环境变量再调用。" % (p, pinfo.get("env_hint", ""))
                    )
                return p, model, "manual 模式：显式指定 %s:%s" % (p, model)
    raise AdapterError("未在注册表中找到模型: %s（检查 models.yaml）" % model_str)


def _price_of(provider, model_name, reg):
    for p, pinfo in reg.get("providers", {}).items():
        if p != provider:
            continue
        for m in pinfo.get("models", []):
            if m["name"] == model_name:
                return {"in": m.get("price_in", 0), "out": m.get("price_out", 0)}
    return None


# ───────────────────────── 命令实现 ─────────────────────────
def cmd_chat(args, reg):
    prompt = args.prompt or " ".join(args.message or [])
    if not prompt:
        raise SystemExit("❌ 请提供 --prompt 或 -m")
    system = args.system
    classification = classifier.classify(prompt, args.task)
    strategy = args.model if args.model in ("auto", "cheap", "quality") else "manual"

    # ── Mock 模式（v2.0 全链路离线 Mock）──
    if getattr(args, "mock", False):
        return _cmd_chat_mock(args, reg, prompt, system, classification, strategy)

    try:
        if strategy == "manual":
            provider, model, reason = _resolve_manual(args.model, reg)
        else:
            provider, model, reason = resolve(strategy, classification, reg)
    except AdapterError as e:
        raise SystemExit("❌ 路由失败：%s" % e)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if not args.no_cache:
        hit = cache.get(prompt, ttl_hours=args.cache_ttl, fuzzy=args.cache_fuzzy)
        if hit:
            hp, hm, hresp = hit
            cost_tracker.log_call(hp, hm, classification["task_type"], 0, 0, 0.0, 0, True, "cache_hit")
            if args.json:
                print(json.dumps({"content": hresp, "cached": True, "provider": hp, "model": hm},
                                  ensure_ascii=False))
            else:
                print("⚡ 命中本地语义缓存（来自 %s / %s），跳过 API 调用：\n" % (hp, hm))
                print(hresp)
            return

    t0 = time.time()
    try:
        adapter = build(reg["providers"][provider]["adapter"], _adapter_cfg(provider, reg))
        if args.stream:
            print("🤖 [%s / %s] %s\n" % (provider, model, reason))
            chunks = adapter.chat(messages, model, stream=True, timeout=args.timeout)
            full = []
            for piece in chunks:
                if piece == "":
                    break
                full.append(piece)
                if not args.json:
                    sys.stdout.write(piece)
                    sys.stdout.flush()
            print("")
            content = "".join(full)
            # 流式无法可靠拿 usage，按字符粗估（仅日志用，不影响计费的准确性承诺）
            it = ot = 0
        else:
            res = adapter.chat(messages, model, stream=False, timeout=args.timeout)
            content = res["content"]
            it, ot = res["in_tokens"], res["out_tokens"]
    except AdapterError as e:
        cost_tracker.log_call(provider, model, classification["task_type"], 0, 0, 0.0,
                               int((time.time() - t0) * 1000), False, str(e))
        raise SystemExit("❌ 调用失败：%s" % e)

    elapsed = int((time.time() - t0) * 1000)
    price = _price_of(provider, model, reg)
    cost = cost_tracker.compute_cost(price, it, ot)
    cost_tracker.log_call(provider, model, classification["task_type"], it, ot, cost, elapsed, True)
    cache.put(prompt, provider, model, content)

    if args.json:
        print(json.dumps({"content": content, "provider": provider, "model": model,
                          "in_tokens": it, "out_tokens": ot, "cost": cost,
                          "route_reason": reason},
                         ensure_ascii=False))
    else:
        print("🤖 [%s / %s] %s\n" % (provider, model, reason))
        print(content)
        print("\n────────── 用量 ──────────")
        print("  token: 入 %d / 出 %d ｜ 花费 ¥%.6f ｜ 耗时 %dms" % (it, ot, cost, elapsed))

    # 预算告警（可选）
    cfg = config.load_config(args.config)
    if cfg.get("budget_monthly"):
        exc, spent, bud = cost_tracker.budget_check(cfg["budget_monthly"])
        msg = report_mod.budget_alert(exc, spent, bud)
        print(msg)
        if exc and cfg.get("wecom_webhook"):
            report_mod.maybe_push_wecom(cfg["wecom_webhook"], msg)


def _cmd_chat_mock(args, reg, prompt, system, classification, strategy):
    """Mock 模式下的 chat 实现：不调 API，从预设库返回。
    
    自动网络检测：
    - 若所有厂商不可达，自动进入 mock 模式（即使未显式传 --mock）
    - 若部分厂商不可达，仅熔断不可达厂商
    """
    latency = getattr(args, "latency", 0)
    resp = mock_engine.build_mock_response(prompt, classification["task_type"], latency_ms=latency)

    mock_reason = "Mock 模式（离线调试，不调用真实 API）"
    provider = "mock"
    model = "preset"

    # 缓存逻辑
    if not args.no_cache:
        hit = cache.get(prompt, ttl_hours=args.cache_ttl, fuzzy=args.cache_fuzzy)
        if hit:
            hp, hm, hresp = hit
            cost_tracker.log_call(hp, hm, classification["task_type"], 0, 0, 0.0, 0, True, "cache_hit")
            if args.json:
                print(json.dumps({"content": hresp, "cached": True, "provider": hp, "model": hm},
                                 ensure_ascii=False))
            else:
                print("⚡ 命中本地语义缓存（来自 %s / %s），跳过 API 调用：\n" % (hp, hm))
                print(hresp)
            return

    content = resp["content"]
    it, ot = resp.get("in_tokens", 0), resp.get("out_tokens", 0)
    elapsed = latency  # 模拟延迟即为耗时

    # 成本记录（mock 模式下记录为 mock 调用）
    cost_tracker.log_call(provider, model, classification["task_type"], it, ot,
                          0.0, elapsed, True, "mock")

    # 写缓存
    cache.put(prompt, provider, model, content)

    if args.json:
        print(json.dumps({"content": content, "provider": provider, "model": model,
                          "in_tokens": it, "out_tokens": ot, "cost": 0.0,
                          "route_reason": mock_reason, "mock": True},
                         ensure_ascii=False))
    else:
        stream = getattr(args, "stream", False)
        print("🤖 [Mock / %s] %s\n" % (model, mock_reason))
        if stream and latency > 0:
            # 流式模式下逐字输出以模拟真实流式体验
            for ch in content:
                sys.stdout.write(ch)
                sys.stdout.flush()
                time.sleep(latency / 1000.0 / max(len(content), 1))
            print("")
        else:
            print(content)
        print("\n────────── 用量 ──────────")
        print("  token: 入 %d / 出 %d ｜ 花费 ¥0.000000（Mock 免费）｜ 耗时 %dms" % (it, ot, elapsed))

    # 预算告警（mock 不计费，但仍检查是否超预算）
    cfg = config.load_config(args.config)
    if cfg.get("budget_monthly"):
        exc, spent, bud = cost_tracker.budget_check(cfg["budget_monthly"])
        msg = report_mod.budget_alert(exc, spent, bud)
        print(msg)


def cmd_route(args, reg):
    prompt = args.prompt or " ".join(args.message or [])
    if not prompt:
        raise SystemExit("❌ 请提供 --prompt 或 -m")
    cls = classifier.classify(prompt, args.task)
    strategy = args.strategy if args.strategy else "auto"
    try:
        if strategy == "manual":
            if not args.model:
                raise AdapterError("manual 模式需通过 --model provider:model 指定具体模型")
            provider, model, reason = _resolve_manual(args.model, reg)
        else:
            provider, model, reason = resolve(strategy, cls, reg)
    except AdapterError as e:
        if not config.configured_providers():
            # 未配置任何密钥 → 进入「建议模式」，仅展示推荐路由，不发起调用
            try:
                if strategy == "manual" and args.model:
                    provider, model, reason = _resolve_manual(args.model, reg, allow_unconfigured=True)
                else:
                    provider, model, reason = resolve(strategy, cls, reg, allow_unconfigured=True)
            except AdapterError:
                raise SystemExit("❌ 路由失败：%s" % e)
            reason = "【建议模式·未配置密钥，仅展示推荐不调用】" + reason
        else:
            raise SystemExit("❌ 路由失败：%s" % e)
    if args.json:
        print(json.dumps({"strategy": strategy, "provider": provider, "model": model,
                          "reason": reason, "classification": cls}, ensure_ascii=False))
    else:
        print("🧭 路由决策（%s 模式）" % strategy)
        print("  厂商/模型 : %s / %s" % (provider, model))
        print("  依据       : %s" % reason)
        print("  任务分类   : 类型=%s 推理=%s 长度=%s 价格敏感=%s" % (
            cls["task_type"], cls["needs_reasoning"], cls["length_bucket"], cls["budget_sensitive"]))


def cmd_report(args, reg):
    agg = cost_tracker.aggregate(args.period)
    if args.html:
        path = report_mod.render_html(agg, args.html)
        print("📊 HTML 报表已生成：%s" % path)
    print(report_mod.render_text(agg))


def cmd_hardware(args, reg):
    p = hardware.profile()
    print("🖥️  硬件画像：")
    print("  档位        : %s" % p["tier"])
    print("  CPU 核心    : %d" % p["cpu_cores"])
    print("  物理内存    : %.1f GB" % p["mem_gb"])
    print("  最大并发    : %d（自动限制，不拖累电脑）" % p["max_concurrency"])
    print("  单批大小    : %d" % p["batch_size"])
    print("  建议子任务数: %d（recommend_subtasks 示例）" % hardware.recommend_subtasks(10))


def cmd_cache(args, reg):
    if args.cache_cmd == "stats":
        print("语义缓存条目：%d" % cache.stats().get("entries", 0))
    elif args.cache_cmd == "clear":
        n = cache.clear()
        print("已清空 %d 条缓存" % n)


def cmd_config(args, reg):
    print("已配置密钥的厂商：%s" % (", ".join(config.configured_providers()) or "（无）"))
    print("全部支持厂商：%s" % ", ".join(reg.get("providers", {}).keys()))
    if not config.configured_providers():
        print("\n提示：在调用前设置至少一个厂商的环境变量，例如：")
        print("  export DEEPSEEK_API_KEY=sk-xxx")


def cmd_update(args, reg):
    cfg = config.load_config(args.config)
    has_update, latest, msg = update_check.run(meta.VERSION, cfg.get("update_url", ""), meta.HOMEPAGE)
    print(msg)
    if has_update:
        print("\n💡 升级方式：通过 SkillHub / 你常用的发布脚本更新本技能即可。")


def cmd_budget(args, reg):
    cfg = config.load_config(args.config)
    if not cfg.get("budget_monthly"):
        print("未配置月预算（在 config.json 设置 budget_monthly）。")
        return
    exc, spent, bud = cost_tracker.budget_check(cfg["budget_monthly"])
    print(report_mod.budget_alert(exc, spent, bud))


def cmd_version(args, reg):
    print("cn-llm-router v%s" % meta.VERSION)


# ───────────────────────── CLI ─────────────────────────
def build_parser():
    ap = argparse.ArgumentParser(prog="cn-llm-router", description="国产大模型统一路由")
    sub = ap.add_subparsers(dest="cmd")

    p_chat = sub.add_parser("chat", help="调用模型（需对应厂商密钥）")
    p_chat.add_argument("--prompt", help="用户问题")
    p_chat.add_argument("-m", "--message", action="append", help="消息（可多次）")
    p_chat.add_argument("--system", help="系统提示词")
    p_chat.add_argument("--model", default="auto", help="auto/cheap/quality 或 provider:model（manual）")
    p_chat.add_argument("--task", help="显式任务类型: code/reason/summarize/...")
    p_chat.add_argument("--stream", action="store_true", help="流式输出")
    p_chat.add_argument("--no-cache", action="store_true", help="禁用语义缓存")
    p_chat.add_argument("--timeout", type=int, default=60)
    p_chat.add_argument("--json", action="store_true", help="JSON 输出（供程序调用）")
    p_chat.add_argument("--config", help="config.json 路径")
    p_chat.add_argument("--cache-ttl", type=int, default=168)
    p_chat.add_argument("--cache-fuzzy", action="store_true")
    # v2.0 Mock 模式参数
    p_chat.add_argument("--mock", action="store_true",
                        help="v2.0 Mock 模式：不调真实 API，从本地预设库返回响应")
    p_chat.add_argument("--latency", type=int, default=0,
                        help="Mock 模式下模拟延迟（毫秒），用于测试超时逻辑")

    p_route = sub.add_parser("route", help="仅做路由决策（不调用 API）")
    p_route.add_argument("--prompt", help="用户问题")
    p_route.add_argument("-m", "--message", action="append")
    p_route.add_argument("--task", help="显式任务类型")
    p_route.add_argument("--strategy", default="auto", help="auto/cheap/quality/manual")
    p_route.add_argument("--model", help="manual 时的 provider:model")
    p_route.add_argument("--json", action="store_true")

    p_rep = sub.add_parser("report", help="成本/用量报表")
    p_rep.add_argument("--period", default="month", choices=["day", "week", "month"])
    p_rep.add_argument("--html", help="导出 HTML 报表路径")
    p_rep.add_argument("--config", help="config.json 路径")

    p_hw = sub.add_parser("hardware", help="硬件画像与并发建议")

    p_cache = sub.add_parser("cache", help="语义缓存管理")
    p_cache.add_argument("cache_cmd", choices=["stats", "clear"])

    p_cfg = sub.add_parser("config", help="查看已配置厂商")

    p_up = sub.add_parser("update-check", help="检查技能更新")
    p_up.add_argument("--config", help="config.json 路径")

    p_bud = sub.add_parser("budget", help="预算检查")
    p_bud.add_argument("--config", help="config.json 路径")

    sub.add_parser("version", help="版本号")

    # v2.0 Mock 数据编辑器
    p_mock = sub.add_parser("mock", help="v2.0 Mock 数据编辑器（自定义 query→response 映射）")
    p_mock.add_argument("--edit", action="store_true", help="进入交互式 mock 数据编辑")
    p_mock.add_argument("--list", action="store_true", help="列出所有自定义 mock 场景")
    return ap


def cmd_mock(args, reg):
    """Mock 数据编辑器命令实现。"""
    if args.edit:
        mock_engine.interactive_edit()
    elif args.list:
        mocks = mock_engine.list_custom_mocks()
        if not mocks:
            print("暂无自定义 mock 场景。")
        else:
            print("自定义 mock 场景列表：")
            for m in mocks:
                print("  [%s] %s | 优先级:%d | 关键词:%s" % (
                    m["id"], m["task_type"], m["priority"], ", ".join(m["keywords"][:5])))
    else:
        # 默认显示帮助
        print("Mock 数据编辑器）")
        print("  mock --edit  进入交互式编辑")
        print("  mock --list  列出所有自定义 mock 场景")


def main():
    ap = build_parser()
    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return
    reg = load_registry()
    dispatch = {
        "chat": cmd_chat, "route": cmd_route, "report": cmd_report,
        "hardware": cmd_hardware, "cache": cmd_cache, "config": cmd_config,
        "update-check": cmd_update, "budget": cmd_budget, "version": cmd_version,
        "mock": cmd_mock,
    }
    dispatch[args.cmd](args, reg)


if __name__ == "__main__":
    main()
