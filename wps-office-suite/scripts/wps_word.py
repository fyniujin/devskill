"""
WPS Word CLI v4.4 - 四引擎自动调用（含长文档排版）
"""
import subprocess
import json
import sys
from pathlib import Path

WORKER = Path(__file__).parent / "wps_worker.py"


def call_worker(cmd: str, args: dict) -> dict:
    req = json.dumps({"cmd": cmd, "args": args}, ensure_ascii=False)
    proc = subprocess.Popen(
        [sys.executable, str(WORKER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).parent.parent),
    )
    stdout, stderr = proc.communicate(input=req.encode("utf-8"), timeout=60)
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8") if stderr else "未知错误"
        return {"ok": False, "error": f"WPS Worker 异常: {err_msg[:200]}"}
    try:
        return json.loads(stdout.decode("utf-8"))
    except json.JSONDecodeError:
        return {"ok": False, "error": f"Worker 输出解析失败"}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="WPS Word")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="创建文档")
    p.add_argument("--title", required=True)
    p.add_argument("--filepath", default="")

    p = sub.add_parser("edit", help="编辑")
    p.add_argument("--file", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--position", choices=["start", "end", "replace"], default="end")

    p = sub.add_parser("format", help="格式")
    p.add_argument("--file", required=True)
    p.add_argument("--align", default="")
    p.add_argument("--font", default="")
    p.add_argument("--size", type=int, default=0)
    p.add_argument("--bold", action="store_true")
    p.add_argument("--color", default="")
    p.add_argument("--space-after", type=float, default=0)
    p.add_argument("--first-indent", type=float, default=0)

    p = sub.add_parser("export", help="导出")
    p.add_argument("--file", required=True)
    p.add_argument("--format", default="pdf")

    p = sub.add_parser("info", help="信息")
    p.add_argument("--file", required=True)

    p = sub.add_parser("engine-info", help="引擎信息")

    p = sub.add_parser("review", help="合同条款审查")
    p.add_argument("--file", required=True, help="合同 .docx 文件路径")
    p.add_argument("--output", default="", help="输出审查版 .docx 路径")

    p = sub.add_parser("long-doc", help="长文档排版（目录/页眉页脚/编号/图表索引/格式统一）")
    p.add_argument("--file", required=True, help="Word 文件路径")
    p.add_argument("--task", default="analyze",
                   choices=["analyze", "toc", "header", "numbering", "fig-index", "xref", "format", "all", "preview"],
                   help="排版任务类型")
    p.add_argument("--max-level", type=int, default=3, help="目录/编号层级")
    p.add_argument("--field", action="store_true", help="目录使用域代码")
    p.add_argument("--insert", action="store_true", help="插入到文档")
    p.add_argument("--odd-even", action="store_true", help="奇偶页不同页眉")
    p.add_argument("--odd-header", default="", help="奇数页页眉")
    p.add_argument("--even-header", default="", help="偶数页页眉")
    p.add_argument("--chapter-in-header", action="store_true", help="章节标题同步到页眉")
    p.add_argument("--page-number", action="store_true", help="添加页码")
    p.add_argument("--page-format", default="arabic", help="页码格式")
    p.add_argument("--page-start", type=int, default=1, help="起始页码")
    p.add_argument("--style", default="arabic", help="编号样式: chinese/arabic/roman")
    p.add_argument("--preset", default="thesis", help="格式预设: thesis/bid/report")
    p.add_argument("--numbering-style", default="arabic", help="标题编号样式")
    p.add_argument("--output", default="", help="输出路径（不指定则覆盖原文件）")

    args = parser.parse_args()

    if args.command == "create":
        r = call_worker("create_word", {"title": args.title, "filepath": args.filepath})
    elif args.command == "edit":
        r = call_worker("edit_word", {"filepath": args.file, "text": args.text, "position": args.position})
    elif args.command == "format":
        r = call_worker("format_word", {"filepath": args.file, "align": args.align, "font": args.font, "size": args.size, "bold": args.bold, "color": args.color, "space_after": args.space_after, "first_line_indent": args.first_indent})
    elif args.command == "export":
        r = call_worker("export_word", {"filepath": args.file, "format": args.format})
    elif args.command == "info":
        r = call_worker("info_word", {"filepath": args.file})
    elif args.command == "engine-info":
        r = call_worker("engine_info", {})
    elif args.command == "review":
        r = call_worker("contract_review", {"file": args.file, "output": args.output})
    elif args.command == "long-doc":
        r = call_worker("long_document", {
            "file": args.file,
            "task": args.task,
            "max_level": args.max_level,
            "field": args.field,
            "insert": args.insert,
            "odd_even": args.odd_even,
            "odd_header": args.odd_header,
            "even_header": args.even_header,
            "chapter_in_header": args.chapter_in_header,
            "page_number": args.page_number,
            "page_format": args.page_format,
            "page_start": args.page_start,
            "style": args.style,
            "preset": args.preset,
            "numbering_style": args.numbering_style,
            "output": args.output,
        })
    else:
        r = {"ok": False, "error": "未知命令"}

    print(json.dumps(r, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
