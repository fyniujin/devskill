# -*- coding: utf-8 -*-
"""
zwjh-skill v2.0.0 统一命令行入口。

把「长期记忆 + 知识图谱 + 自动沉淀 + 检索 + 健康度 + 备份」串成一条命令。
所有功能纯本地、零密钥、按硬件自适应，不拖累电脑。

用法示例：
  python cli.py deposit --text "客户张三的对接人是李四" --source conversation
  python cli.py deposit --file notes.md
  python cli.py query "发布失败的根因"
  python cli.py ask "我最近在忙什么项目"
  python cli.py timeline --from 2026-07-01 --to 2026-07-31 --keyword 发布
  python cli.py graph list
  python cli.py graph show
  python cli.py health
  python cli.py compact --apply
  python cli.py backup
  python cli.py diary --text "今天想清楚了一件事"
  python cli.py analyze
  python cli.py setup
  python cli.py update-check
  python cli.py autopilot
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# ── 让本文件既能 `python cli.py` 也能 `python -m scripts.cli` 运行 ──────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

from scripts import (config, store, embeddings, retrieval, graph, deposit,
                     health, backup, legacy, setup, update_check, hardware, version)


# ── 子命令实现 ────────────────────────────────────────────────────────────
def cmd_deposit(args):
    if args.file:
        r = deposit.ingest_file(args.file, day=args.day)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.text:
        if args.conversation:
            r = deposit.deposit_conversation(args.text, day=args.day)
        else:
            r = deposit.deposit_text(args.text, source=args.source or "conversation",
                                     day=args.day)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        # 从 stdin 读取（便于管道）
        data = sys.stdin.read()
        r = deposit.deposit_conversation(data, day=args.day)
        print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_query(args):
    hits = retrieval.semantic_search(args.query, top_k=args.top)
    if not hits:
        print("（未找到相关记忆）")
        return
    for h in hits:
        print(f"[{h['day']} · {h['source']} · {h['score']}] {h['snippet']}")


def cmd_ask(args):
    print(retrieval.ask(args.query, top_k=args.top))


def cmd_timeline(args):
    hits = retrieval.timeline_search(args.frm, args.to, keyword=args.keyword,
                                     limit=args.limit)
    if not hits:
        print("（该时间线内没有记忆）")
        return
    for h in hits:
        print(f"[{h['day']} · {h['source']}] {h['snippet']}")


def cmd_graph(args):
    if args.gaction == "add-entity":
        eid = store.upsert_entity(args.type, args.name, importance=float(args.importance))
        print("entity_id:", eid)
    elif args.gaction == "relate":
        f = store.find_entity(None, args.frm)
        t = store.find_entity(None, args.to)
        if not f or not t:
            print("实体不存在，请先用 add-entity 创建")
            return
        rid = store.add_relation(f["id"], t["id"], args.relation,
                                 weight=0.6, confidence=0.7)
        print("relation_id:", rid)
    elif args.gaction == "list":
        for e in store.list_entities(limit=args.limit):
            print(f"  [{e['type']}] {e['name']} (id={e['id']}, 重要度={e['importance']})")
    elif args.gaction == "show":
        print(graph.render_mermaid())
    elif args.gaction == "mention":
        for m in graph.mention_link(args.text):
            print(f"  命中实体: {m['name']} ({m['type']})")


def cmd_health(args):
    h = health.audit()
    print(json.dumps(h, ensure_ascii=False, indent=2))


def cmd_compact(args):
    r = health.compact(dry_run=not args.apply)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if args.apply:
        print("✅ 已执行压缩（生成摘要 + 清理索引）")
    else:
        print("⚠️ 这是预览（dry-run）。加 --apply 真正执行。")


def cmd_snapshot(args):
    p = health.snapshot(args.path)
    print("快照已保存:", p)


def cmd_backup(args):
    if args.target == "baidunetdisk":
        r = backup.backup_baidunetdisk(args.path)
    else:
        r = backup.export_local(args.path)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_restore(args):
    r = backup.restore_local(args.path, include_logs=not args.no_logs)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_diary(args):
    mid = store.add_diary(config.today_str(), args.text, mood=args.mood)
    print("diary_id:", mid)


def cmd_analyze(args):
    legacy.analyze_memory(day=args.day)


def cmd_predict(args):
    legacy.predict_risks()


def cmd_report(args):
    legacy.generate_report(days=args.days)


def cmd_demo(args):
    legacy.demo()


def cmd_setup(args):
    r = setup.setup_daily(hour=args.hour, minute=args.minute)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r.get("ok"):
        print("✅ 定时任务已创建（每日 %02d:%02d 自动进化）" % (args.hour, args.minute))
    else:
        print("❌ 创建失败：", r.get("error") or r.get("output"))


def cmd_remove(args):
    r = setup.remove()
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_status(args):
    r = setup.status()
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_update(args):
    r = update_check.check(remote=args.remote)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r["update_available"]:
        print(r["reminder"])
    update_check.mark_seen()


def cmd_hardware(args):
    print(hardware.describe())
    print("示例：5000 条知识点建议子任务数 =", hardware.recommend_subtasks(5000))


def cmd_status_overview(args):
    h = health.audit()
    print("═══════════════════════════════════════════")
    print(f"  🧠 {version.DISPLAY_NAME} v{version.VERSION}")
    print("═══════════════════════════════════════════")
    print(f"  记忆条目 : {h['memories']}")
    print(f"  实体     : {h['entities']}")
    print(f"  关系     : {h['relations']}")
    print(f"  健康度   : {h['score']} / 100")
    print(f"  DB 体积  : {h['db_size_mb']} MB")
    print(f"  硬件档位 : {h['tier']}")
    print("═══════════════════════════════════════════")


def cmd_autopilot(args):
    print("🤖 自动进化开始 ...")
    r = deposit.index_daily_logs()
    print(f"  · 每日日志补录：{r['added']} 条新增")
    legacy.analyze_memory()
    legacy.predict_risks()
    legacy.generate_report()
    h = health.audit()
    print(f"  · 健康度：{h['score']} / 100（陈旧 {h['stale_memories']} · "
          f"孤儿实体 {h['orphan_entities']} · 冲突事实 {h['conflicting_facts']}）")
    cfg = config.load_config()
    if cfg.get("auto_backup"):
        b = backup.export_local()
        print(f"  · 自动备份：{b['backup_path']}")
    upd = update_check.check()
    if upd["update_available"]:
        print(upd["reminder"])
    update_check.mark_seen()
    print("✅ 自动进化完成。")


# ── 参数解析 ──────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="zwjh-skill",
        description=f"{version.DISPLAY_NAME} v{version.VERSION} 命令行",
    )
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("deposit", help="沉淀知识点（对话/文件）")
    d.add_argument("--text", help="直接传入文本")
    d.add_argument("--file", help="读取纯文本文件并沉淀")
    d.add_argument("--conversation", action="store_true", help="按段落拆分沉淀")
    d.add_argument("--source", default="conversation")
    d.add_argument("--day", default=None)
    d.set_defaults(func=cmd_deposit)

    q = sub.add_parser("query", help="语义检索")
    q.add_argument("query")
    q.add_argument("--top", type=int, default=8)
    q.set_defaults(func=cmd_query)

    a = sub.add_parser("ask", help="记忆问答（拼接相关记忆）")
    a.add_argument("query")
    a.add_argument("--top", type=int, default=5)
    a.set_defaults(func=cmd_ask)

    t = sub.add_parser("timeline", help="时间线检索")
    t.add_argument("--from", dest="frm", default=None)
    t.add_argument("--to", default=None)
    t.add_argument("--keyword", default=None)
    t.add_argument("--limit", type=int, default=100)
    t.set_defaults(func=cmd_timeline)

    g = sub.add_parser("graph", help="知识图谱")
    g.add_argument("gaction", choices=["add-entity", "relate", "list", "show", "mention"])
    g.add_argument("--type", default="concept")
    g.add_argument("--name", default=None)
    g.add_argument("--from", dest="frm", default=None)
    g.add_argument("--to", default=None)
    g.add_argument("--relation", default="关联")
    g.add_argument("--importance", default="0.5")
    g.add_argument("--text", default=None)
    g.add_argument("--limit", type=int, default=50)
    g.set_defaults(func=cmd_graph)

    hh = sub.add_parser("health", help="健康度审计")
    hh.set_defaults(func=cmd_health)

    c = sub.add_parser("compact", help="压缩（去重 + 摘要）")
    c.add_argument("--apply", action="store_true")
    c.set_defaults(func=cmd_compact)

    sn = sub.add_parser("snapshot", help="导出快照")
    sn.add_argument("--path", default=None)
    sn.set_defaults(func=cmd_snapshot)

    b = sub.add_parser("backup", help="备份")
    b.add_argument("--target", default="local", choices=["local", "baidunetdisk"])
    b.add_argument("--path", default=None)
    b.set_defaults(func=cmd_backup)

    rs = sub.add_parser("restore", help="恢复")
    rs.add_argument("path")
    rs.add_argument("--no-logs", action="store_true")
    rs.set_defaults(func=cmd_restore)

    di = sub.add_parser("diary", help="写日记")
    di.add_argument("--text", required=True)
    di.add_argument("--mood", default=None)
    di.set_defaults(func=cmd_diary)

    an = sub.add_parser("analyze", help="v1.7 记忆分析")
    an.add_argument("--day", default=None)
    an.set_defaults(func=cmd_analyze)

    pr = sub.add_parser("predict", help="v1.7 预测性维护")
    pr.set_defaults(func=cmd_predict)

    rp = sub.add_parser("report", help="v1.7 进化报告")
    rp.add_argument("--days", type=int, default=30)
    rp.set_defaults(func=cmd_report)

    dm = sub.add_parser("demo", help="模拟演示")
    dm.set_defaults(func=cmd_demo)

    st = sub.add_parser("setup", help="配置硬件感知定时任务")
    st.add_argument("--hour", type=int, default=23)
    st.add_argument("--minute", type=int, default=0)
    st.set_defaults(func=cmd_setup)

    rm = sub.add_parser("remove", help="删除定时任务")
    rm.set_defaults(func=cmd_remove)

    ss = sub.add_parser("task-status", help="查看定时任务状态")
    ss.set_defaults(func=cmd_status)

    uc = sub.add_parser("update-check", help="检查更新")
    uc.add_argument("--remote", action="store_true")
    uc.set_defaults(func=cmd_update)

    hw = sub.add_parser("hardware", help="查看硬件自适应计划")
    hw.set_defaults(func=cmd_hardware)

    ov = sub.add_parser("status", help="总览")
    ov.set_defaults(func=cmd_status_overview)

    ap = sub.add_parser("autopilot", help="每日自动进化")
    ap.set_defaults(func=cmd_autopilot)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        # 默认进入总览
        cmd_status_overview(args)
        return 0
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
