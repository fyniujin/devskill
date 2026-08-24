"""KingDoc MCP Server — 真实接入金山文档（WPS）开放平台

深度绑定在线文档能力：
- 云端 40+ 工具直连 open.kdocs.cn 开放 API（文件/表格/多维表/收集表/回收站/版本/权限/空间/通知/用户）
- 本地免密钥工具：DOCX/PPTX 生成、思维导图/流程图 SVG 渲染、本地 OCR、硬件画像
- 自动按本机硬件分配并发子进程数，避免拖累用户电脑
- 每日自动更新提醒（不自动安装）

运行：python -m engine.api.mcp_server --config ./config.json
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any

# 把 skill 根目录加入 path，便于 import engine.*
SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SKILL_ROOT))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:  # 缺少 mcp 依赖时给出清晰指引
    sys.stderr.write(
        "KingDoc 需要 mcp 依赖：pip install mcp\n"
        "（若已通过 setup.sh/setup.ps1 安装仍报错，请确认 venv 已激活）\n"
        f"import error: {e}\n"
    )
    raise

from engine.hardware import get_recommended_settings
from engine.update_check import build_reminder, FEEDBACK_EMAIL
from engine.exceptions import KingDocError

APP_VERSION = "3.9.0"

# 配置路径：环境变量优先，其次 skill 根目录 config.json
CONFIG_PATH = os.environ.get("KINGDOC_CONFIG", str(SKILL_ROOT / "config.json"))

mcp = FastMCP("kingdoc")


def _backend():
    """惰性创建云端后端（需要 config / App Key）。"""
    from engine.api.tools import KingDocMcpServer
    return KingDocMcpServer(CONFIG_PATH)


def _local_root() -> Path:
    return SKILL_ROOT / "engine" / "local"


def _to_text(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def _wrap(fn_name: str):
    """统一包裹云端调用：捕获鉴权/网络异常，返回友好文本而非崩溃。"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                backend = _backend()
                method = getattr(backend, fn_name)
                result = method(*args, **kwargs)
                return _to_text(result)
            except KingDocError as e:
                return f"[{e.code}] {e.message}"
            except FileNotFoundError as e:
                return ("[KD001] 未找到 config.json，云端功能需要金山开放平台 App Key。\n"
                        "请先运行 setup.sh / setup.ps1 配置，或使用本地免密钥工具"
                        "（kdoc.local.* / kdoc.local.ocr.*）。")
            except Exception as e:
                return f"[KD010] 调用失败：{e}\n{traceback.format_exc()[-300:]}"
        return wrapper
    return decorator


# ===========================================================================
# 一、文件管理（深度绑定金山在线文档）
# ===========================================================================
@mcp.tool()
async def kdoc_file_create(name: str, doc_type: str, folder_id: Optional[str] = None,
                           content: Optional[str] = None) -> str:
    """创建在线文档。doc_type 取值：doc/sheet/ppt/smart_note/mindmap/flowchart/form/attachment。
    返回新文档的 file_id 与访问链接。"""
    return await _wrap("kdoc_file_create")(name, doc_type, folder_id, content)

@mcp.tool()
async def kdoc_file_content(file_id: str) -> str:
    """读取在线文档内容（按品类自动路由）。"""
    return await _wrap("kdoc_file_content")(file_id)

@mcp.tool()
async def kdoc_file_info(file_id: str) -> str:
    """获取文档元信息（类型/版本/权限），编辑前必须先调用以确认品类。"""
    return await _wrap("kdoc_file_info")(file_id)

@mcp.tool()
async def kdoc_file_rename(file_id: str, name: str) -> str:
    """重命名文档。"""
    return await _wrap("kdoc_file_rename")(file_id, name)

@mcp.tool()
async def kdoc_file_move(file_id: str, folder_id: str) -> str:
    """移动文档到目标文件夹。"""
    return await _wrap("kdoc_file_move")(file_id, folder_id)

@mcp.tool()
async def kdoc_file_delete(file_id: str) -> str:
    """⚠️ 危险操作：软删除文档到回收站（可回收）。彻底删除请用 kdoc_trash_destroy（需二次确认）。"""
    return await _wrap("kdoc_file_delete")(file_id)

@mcp.tool()
async def kdoc_file_search(keyword: str, limit: int = 10) -> str:
    """按关键词搜索在线文档。"""
    return await _wrap("kdoc_file_search")(keyword, limit)

@mcp.tool()
async def kdoc_file_upload(file_path: str, folder_id: Optional[str] = None) -> str:
    """上传本地文件到云端（新建文档/附件，二进制安全）。默认拦截禁止类型
    （.exe/.bat/.ps1/.zip 等，详见安全规范）；仅技能内部生成的
    docx/pptx/pdf/svg/png 等可上传。"""
    try:
        from engine.security import assert_upload_safe
        assert_upload_safe(file_path, internal=True)
        backend = _backend()
        return _to_text(backend.kdoc_file_upload(file_path, folder_id))
    except KingDocError as e:
        return f"[{e.code}] {e.message}"
    except FileNotFoundError:
        return "[KD001] 未找到 config.json，云端上传需先配置金山 App Key（本地生成无需 Key）。"
    except Exception as e:
        return f"[KD010] 上传失败：{e}"

@mcp.tool()
async def kdoc_file_download(file_id: str, target_path: str) -> str:
    """导出在线文档内容到本地文件。"""
    return await _wrap("kdoc_file_download")(file_id, target_path)


# ===========================================================================
# 二、文件夹 / 空间
# ===========================================================================
@mcp.tool()
async def kdoc_folder_create(name: str, parent_id: Optional[str] = None) -> str:
    """创建文件夹。"""
    return await _wrap("kdoc_folder_create")(name, parent_id)

@mcp.tool()
async def kdoc_folder_list(folder_id: Optional[str] = None) -> str:
    """列出子文件夹。"""
    return await _wrap("kdoc_folder_list")(folder_id)

@mcp.tool()
async def kdoc_space_quota() -> str:
    """查询空间用量与剩余配额。"""
    return await _wrap("kdoc_space_quota")()


# ===========================================================================
# 三、回收站 / 版本历史（金山独有，对标腾讯无此能力）
# ===========================================================================
@mcp.tool()
async def kdoc_trash_list(limit: int = 20, offset: int = 0) -> str:
    """列出回收站文件。"""
    return await _wrap("kdoc_trash_list")(limit, offset)

@mcp.tool()
async def kdoc_trash_recover(file_id: str) -> str:
    """从回收站恢复文件（误删可救回）。"""
    return await _wrap("kdoc_trash_recover")(file_id)

@mcp.tool()
async def kdoc_trash_destroy(file_id: str) -> str:
    """⚠️ 危险操作（不可逆）：彻底删除回收站文件。执行前必须向用户二次确认。"""
    return await _wrap("kdoc_trash_destroy")(file_id)

@mcp.tool()
async def kdoc_version_list(file_id: str) -> str:
    """列出文档历史版本。"""
    return await _wrap("kdoc_version_list")(file_id)

@mcp.tool()
async def kdoc_version_restore(file_id: str, version: int) -> str:
    """回滚文档到指定历史版本。"""
    return await _wrap("kdoc_version_restore")(file_id, version)


# ===========================================================================
# 四、电子表格（et API 精细编辑）
# ===========================================================================
@mcp.tool()
async def kdoc_et_create(name: str) -> str:
    """创建在线电子表格。"""
    return await _wrap("kdoc_et_create")(name)

@mcp.tool()
async def kdoc_et_range_write(sheet_id: str, range: str, values: List[List[Any]]) -> str:
    """批量写入单元格区域（连续 3+ 写入必须用批量接口）。"""
    return await _wrap("kdoc_et_range_write")(sheet_id, range, values)

@mcp.tool()
async def kdoc_et_formula_set(sheet_id: str, cell: str, formula: str) -> str:
    """设置单元格公式。"""
    return await _wrap("kdoc_et_formula_set")(sheet_id, cell, formula)


# ===========================================================================
# 五、多维表格（dbt API 精细编辑）
# ===========================================================================
@mcp.tool()
async def kdoc_dbt_create(name: str) -> str:
    """创建多维表格。"""
    return await _wrap("kdoc_dbt_create")(name)

@mcp.tool()
async def kdoc_dbt_field_add(table_id: str, name: str, field_type: str,
                             options: Optional[List[str]] = None) -> str:
    """添加字段（text/number/select/date 等）。"""
    return await _wrap("kdoc_dbt_field_add")(table_id, name, field_type, options)

@mcp.tool()
async def kdoc_dbt_record_add_batch(table_id: str, records: List[Dict]) -> str:
    """批量添加记录。"""
    return await _wrap("kdoc_dbt_record_add_batch")(table_id, records)

@mcp.tool()
async def kdoc_dbt_record_query(table_id: str, filter: Optional[str] = None,
                                limit: int = 100) -> str:
    """查询记录，filter 为 JSON 字符串。"""
    import json as _json
    fobj = _json.loads(filter) if filter else None
    return await _wrap("kdoc_dbt_record_query")(table_id, fobj, limit)

@mcp.tool()
async def kdoc_dbt_webhook_set(table_id: str, callback_url: str,
                               events: List[str]) -> str:
    """设置多维表格 Webhook 事件监听。"""
    return await _wrap("kdoc_dbt_webhook_set")(table_id, callback_url, events)


# ===========================================================================
# 六、收集表
# ===========================================================================
@mcp.tool()
async def kdoc_form_create(name: str, description: Optional[str] = None) -> str:
    """创建收集表/问卷。"""
    return await _wrap("kdoc_form_create")(name, description)

@mcp.tool()
async def kdoc_form_answers(form_id: str, limit: int = 50) -> str:
    """查询收集表答卷。"""
    return await _wrap("kdoc_form_answers")(form_id, limit)


# ===========================================================================
# 七、格式转换 / 纯文本提取 / 权限 / 通知 / 用户
# ===========================================================================
@mcp.tool()
async def kdoc_office_convert(file_id: str, target_format: str) -> str:
    """格式转换：doc→pdf/word/excel/ppt 等。"""
    return await _wrap("kdoc_office_convert")(file_id, target_format)

@mcp.tool()
async def kdoc_office_extract(file_id: str) -> str:
    """提取文档纯文本。"""
    return await _wrap("kdoc_office_extract")(file_id)

@mcp.tool()
async def kdoc_file_permission(file_id: str, members: List[Dict]) -> str:
    """变更文档权限/分享成员。"""
    return await _wrap("kdoc_file_permission")(file_id, members)

@mcp.tool()
async def kdoc_notification_send(channel: str, webhook_key: str, content: str) -> str:
    """发送通知（企微/钉钉/金山协作机器人）。content 为 JSON 字符串。"""
    import json as _json
    return await _wrap("kdoc_notification_send")(channel, webhook_key, _json.loads(content))

@mcp.tool()
async def kdoc_user_info() -> str:
    """获取当前用户信息。"""
    return await _wrap("kdoc_user_info")()


# ===========================================================================
# 八、本地免密钥工具（无需 App Key，离线可用）
# ===========================================================================
@mcp.tool()
async def kdoc_local_docx_generate(content: str, template: str = "blank",
                                   output_path: Optional[str] = None) -> str:
    """【免密钥】根据 Markdown/文本生成本地 DOCX（会议纪要/周报/合同等），可直接上传覆盖。
    template: blank/weekly_report/meeting_notes。"""
    try:
        from engine.local.generators import DocxGenerator
        out = output_path or str(SKILL_ROOT / "output" / "generated.docx")
        gen = DocxGenerator()
        # 简易 Markdown 段落解析
        for block in content.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            if block.startswith("# "):
                gen.add_heading(block[2:].strip(), 1)
            elif block.startswith("## "):
                gen.add_heading(block[3:].strip(), 2)
            elif block.startswith("- ") or block.startswith("• "):
                gen.add_bullet_list([ln[2:].strip() for ln in block.splitlines()])
            else:
                gen.add_paragraph(block)
        gen.save(out)
        return f"[OK] 已生成本地 DOCX：{out}（可通过 kdoc_file_upload 覆盖上传）"
    except ImportError:
        return "[ERR] 需要 python-docx：pip install python-docx"
    except Exception as e:
        return f"[ERR] 生成失败：{e}"

@mcp.tool()
async def kdoc_local_pptx_generate(title: str, slides: List[Dict], subtitle: str = "",
                                   output_path: Optional[str] = None) -> str:
    """【免密钥】生成本地 PPTX。slides: [{title, bullets:[...]}] 或 [{title, image}]。"""
    try:
        from engine.local.generators import PptxGenerator
        out = output_path or str(SKILL_ROOT / "output" / "generated.pptx")
        gen = PptxGenerator()
        gen.add_title_slide(title, subtitle)
        for s in slides:
            if s.get("image"):
                gen.add_image_slide(s.get("title", ""), s["image"])
            else:
                gen.add_content_slide(s.get("title", ""), s.get("bullets", []))
        gen.save(out)
        return f"[OK] 已生成本地 PPTX：{out}（可通过 kdoc_file_upload 覆盖上传）"
    except ImportError:
        return "[ERR] 需要 python-pptx：pip install python-pptx"
    except Exception as e:
        return f"[ERR] 生成失败：{e}"

@mcp.tool()
async def kdoc_local_mindmap_generate(code: str, output_path: Optional[str] = None) -> str:
    """【免密钥】根据 mermaid graph 代码生成本地思维导图 SVG。"""
    try:
        from engine.local.generators import MindmapGenerator
        out = output_path or str(SKILL_ROOT / "output" / "mindmap.svg")
        gen = MindmapGenerator()
        import re as _re
        for line in code.splitlines():
            line = line.strip()
            if not line or line.startswith("graph") or line.startswith("mindmap"):
                continue
            # 形如  A[标签] / A(标签) / A --> B[标签] / A --- B
            m = _re.search(
                r'([A-Za-z0-9_]+)\s*(?:-->|---|->|-)\s*([A-Za-z0-9_]+)\s*(?:\[([^\]]*)\]|\(([^)]*)\))?',
                line,
            )
            if m:
                src, tgt = m.group(1), m.group(2)
                tgt_label = m.group(3) or m.group(4) or tgt
                gen.add_node(src, src)
                gen.add_node(tgt, tgt_label, parent_id=src)
            else:
                m2 = _re.search(r'([A-Za-z0-9_]+)\s*(?:\[([^\]]*)\]|\(([^)]*)\))', line)
                if m2:
                    nid = m2.group(1)
                    lbl = m2.group(2) or m2.group(3) or nid
                    gen.add_node(nid, lbl)
        gen.render_svg(out)
        return f"[OK] 已生成本地思维导图 SVG：{out}（上传后即在线思维导图）"
    except Exception as e:
        return f"[ERR] 生成失败：{e}"

@mcp.tool()
async def kdoc_local_flowchart_generate(code: str, output_path: Optional[str] = None) -> str:
    """【免密钥】根据 mermaid flowchart 代码生成本地流程图 SVG。"""
    try:
        from engine.local.generators import FlowchartGenerator
        out = output_path or str(SKILL_ROOT / "output" / "flowchart.svg")
        gen = FlowchartGenerator()
        import re as _re
        for i, line in enumerate(code.splitlines()):
            line = line.strip()
            if not line or line.startswith("graph") or line.startswith("flowchart"):
                continue
            m = _re.search(
                r'([A-Za-z0-9_]+)\s*(?:\[([^\]]*)\]|\(([^)]*)\)|\{([^}]*)\})',
                line,
            )
            label = (m.group(2) or m.group(3) or m.group(4) or line) if m else line
            stype = "process"
            if line.startswith("start") or ("(" in line and "[" in line):
                stype = "start"
            elif line.startswith("end") or line.endswith("])"):
                stype = "end"
            elif "{" in line:
                stype = "decision"
            gen.add_step(f"step{i}", label or f"步骤{i}", stype)
        gen.render_svg(out)
        return f"[OK] 已生成本地流程图 SVG：{out}（上传后即在线流程图）"
    except Exception as e:
        return f"[ERR] 生成失败：{e}"

@mcp.tool()
async def kdoc_local_ocr_extract(image_path: str, lang: str = "chi_sim+eng") -> str:
    """【免密钥】本地 OCR 提取图片文字：优先本机 Tesseract（免费无 key），
    未安装则降级云端（需 App Key），都不可用给出安装指引。"""
    try:
        from engine.local.ocr import extract_text
        res = extract_text(image_path, lang=lang, config_path=CONFIG_PATH)
        if res["source"] == "none":
            return f"[OCR 未就绪] {res['hint']}"
        return _to_text(res)
    except Exception as e:
        return f"[ERR] OCR 失败：{e}"

@mcp.tool()
async def kdoc_local_hardware_profile() -> str:
    """【免密钥】采集本机硬件并自动给出推荐并发子进程数 / 批量大小（避免拖累电脑）。"""
    try:
        settings = get_recommended_settings()
        return _to_text(settings)
    except Exception as e:
        return f"[ERR] 采集失败：{e}"


# ===========================================================================
# 九、更新提醒 / 反馈
# ===========================================================================
@mcp.tool()
async def kdoc_skill_update_check() -> str:
    """每日首次调用时检查 KingDoc 更新；有新版返回升级提醒（不自动安装）。"""
    try:
        reminder = build_reminder(APP_VERSION)
        if reminder:
            return reminder
        return "[OK] 已是最新版本。"
    except Exception as e:
        return f"[INFO] 更新检查跳过：{e}"

@mcp.tool()
async def kdoc_skill_feedback(message: str) -> str:
    """提交功能建议/问题反馈（仅回显并提示邮箱，不自动发送）。"""
    return (f"感谢反馈！我们会认真评估。\n"
            f"您的建议已记录：{message}\n"
            f"也可直接邮件联系作者：{FEEDBACK_EMAIL}")


# ===========================================================================
# 十、WPS AI 能力（本地降级优先，自研逻辑实现）
# ===========================================================================
@mcp.tool()
async def kdoc_wps_ai_write(text: str, action: str = "polish") -> str:
    """【免密钥】AI 写作辅助：润色/扩写/缩写/续写/改写。

    action: polish(润色) / expand(扩写) / shorten(缩写) /
           continue_write(续写) / rewrite(改写)
    本地降级处理，效果有限但零配置可用。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        result = get_adapter().write(text, action)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 写作辅助失败：{e}"

@mcp.tool()
async def kdoc_wps_ai_analyze(data: str, question: str) -> str:
    """【免密钥】AI 数据分析：自然语言提问，生成公式建议与基础统计。

    data: CSV 文本或表格数据（每行数值用逗号/空格分隔）
    question: 自然语言问题（如"分析趋势"、"计算平均"）
    本地基础统计分析，零配置可用。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        result = get_adapter().analyze(data, question)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 数据分析失败：{e}"

@mcp.tool()
async def kdoc_wps_ai_ppt(outline: str, output_path: str = "") -> str:
    """【免密钥】AI PPT 生成：根据大纲自动生成本地 PPT。

    outline: Markdown 大纲（# 标题 → ## 子标题 → - 要点）
    output_path: 输出路径（默认 output/wps_ai_ppt.pptx）
    本地 python-pptx 生成，零配置可用。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        out = output_path or str(SKILL_ROOT / "output" / "wps_ai_ppt.pptx")
        result = get_adapter().ppt(outline, output_path=out)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] PPT 生成失败：{e}"

@mcp.tool()
async def kdoc_wps_ai_read(content: str, action: str = "summarize",
                           question: str = "") -> str:
    """【免密钥】AI 阅读助手：总结/问答/思维导图。

    action: summarize(总结) / qa(问答，需传 question) / mindmap(思维导图)
    content: 文档全文
    本地 TextRank 摘要 + 关键词提取，零配置可用。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        result = get_adapter().read(content, action, question=question)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 阅读助手失败：{e}"

@mcp.tool()
async def kdoc_wps_ai_detect_intent(user_input: str) -> str:
    """检测用户输入意图，返回匹配的 WPS AI 能力。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        intent = get_adapter().detect_intent(user_input)
        caps = get_adapter().get_capabilities()
        return _to_text({"intent": intent, "capabilities": caps})
    except Exception as e:
        return f"[ERR] 意图检测失败：{e}"


# ===========================================================================
# 十一、协同编辑冲突解决（自研，零外部依赖）
# ===========================================================================
@mcp.tool()
async def kdoc_conflict_detect(base_text: str, version_a: str, version_b: str) -> str:
    """【免密钥】冲突检测：检测多人并发修改的冲突位置与双方内容。

    返回结构化冲突列表与统计。本地 difflib 算法，零配置可用。"""
    try:
        from engine.conflict_resolver import detect_conflicts
        result = detect_conflicts(base_text, version_a, version_b)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 冲突检测失败：{e}"

@mcp.tool()
async def kdoc_conflict_merge(base_text: str, version_a: str, version_b: str) -> str:
    """【免密钥】智能合并：无冲突段自动合并，冲突段标注 VERSION_A/VERSION_B。

    返回合并后文本与冲突统计。本地 difflib 算法，零配置可用。"""
    try:
        from engine.conflict_resolver import merge_versions
        result = merge_versions(base_text, version_a, version_b)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 合并失败：{e}"

@mcp.tool()
async def kdoc_conflict_diff(version_a: str, version_b: str,
                             label_a: str = "版本A", label_b: str = "版本B") -> str:
    """【免密钥】冲突可视化：生成 Git diff 风格的结构化差异数据。

    返回 diff 行列表、统计与可选 HTML。本地 difflib 算法，零配置可用。"""
    try:
        from engine.conflict_resolver import diff_versions
        result = diff_versions(version_a, version_b, label_a, label_b)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] diff 失败：{e}"

@mcp.tool()
async def kdoc_conflict_resolve(base_text: str, version_a: str, version_b: str,
                               strategy: str = "keep_a",
                               manual_text: str = "") -> str:
    """【免密钥】冲突解决：应用合并策略。

    strategy: keep_a(保留A) / keep_b(保留B) / manual(手动合并，需传 manual_text) / auto_merge(自动合并)
    本地 difflib 算法，零配置可用。"""
    try:
        from engine.conflict_resolver import resolve_conflicts
        result = resolve_conflicts(base_text, version_a, version_b, strategy, manual_text)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 冲突解决失败：{e}"


# ===========================================================================
# 十二、文档内容合规检查（v3.4.0 新增，自研正则+规则引擎）
# ===========================================================================
@mcp.tool()
async def kdoc_compliance_sensitive(text: str, custom_words: str = "") -> str:
    """【免密钥】敏感词扫描：内置敏感词库（适配中国监管），标注命中位置。

    custom_words: 逗号分隔的额外敏感词
    本地正则匹配，零配置可用。"""
    try:
        from engine.compliance_check import scan_sensitive
        words = [w.strip() for w in custom_words.split(",") if w.strip()] if custom_words else None
        result = scan_sensitive(text, custom_words=words)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 敏感词扫描失败：{e}"

@mcp.tool()
async def kdoc_compliance_leak(text: str) -> str:
    """【免密钥】数据泄露检测：扫描手机号/身份证号/银行卡号/邮箱等敏感信息。

    返回风险等级+脱敏显示。本地正则匹配，零配置可用。"""
    try:
        from engine.compliance_check import detect_leak
        result = detect_leak(text)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 泄露检测失败：{e}"

@mcp.tool()
async def kdoc_compliance_format(file_path: str) -> str:
    """【免密钥】格式规范检查：按企业文档规范逐项检查，生成不合规清单。

    支持 .docx / .pptx / .txt / .md 格式。本地 XML 解析，零配置可用。"""
    try:
        from engine.compliance_check import check_format
        result = check_format(file_path)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 格式检查失败：{e}"

@mcp.tool()
async def kdoc_compliance_classify(text: str) -> str:
    """【免密钥】密级自动标注：根据内容建议密级（公开/内部/秘密/机密）。

    本地关键词+规则引擎，零配置可用。"""
    try:
        from engine.compliance_check import classify
        result = classify(text)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 密级标注失败：{e}"


# ===========================================================================
# 十三、实时协同编辑（v3.5.0 新增，序列 CRDT 自研实现）
# ===========================================================================
@mcp.tool()
async def kdoc_realtime_create(client_id: str, session_id: str = "") -> str:
    """【免密钥】创建实时协同文档。

    client_id: 当前客户端标识
    session_id: 会话 ID（留空则自动创建）
    本地 CRDT 引擎，零配置可用。"""
    try:
        from engine.realtime_collab import CRDTDocument
        doc = CRDTDocument(client_id)
        return _to_text({"client_id": client_id, "status": "created", "doc_id": id(doc)})
    except Exception as e:
        return f"[ERR] 创建协同文档失败：{e}"

@mcp.tool()
async def kdoc_realtime_insert(client_id: str, pos: int, text: str) -> str:
    """【免密钥】在协同文档中插入文本。

    client_id: 当前客户端标识
    pos: 插入位置
    text: 插入的文本
    本地 CRDT 引擎，零配置可用。"""
    try:
        from engine.realtime_collab import CRDTDocument
        doc = CRDTDocument(client_id)
        ops = doc.local_insert(pos, text)
        return _to_text({"client_id": client_id, "text": doc.get_text(), "ops_count": len(ops)})
    except Exception as e:
        return f"[ERR] 插入失败：{e}"

@mcp.tool()
async def kdoc_realtime_delete(client_id: str, pos: int, length: int = 1) -> str:
    """【免密钥】在协同文档中删除文本。

    client_id: 当前客户端标识
    pos: 删除起始位置
    length: 删除长度
    本地 CRDT 引擎，零配置可用。"""
    try:
        from engine.realtime_collab import CRDTDocument
        doc = CRDTDocument(client_id)
        ops = doc.local_delete(pos, length)
        return _to_text({"client_id": client_id, "text": doc.get_text(), "ops_count": len(ops)})
    except Exception as e:
        return f"[ERR] 删除失败：{e}"

@mcp.tool()
async def kdoc_realtime_get_text(client_id: str) -> str:
    """【免密钥】获取协同文档当前文本。

    client_id: 当前客户端标识
    本地 CRDT 引擎，零配置可用。"""
    try:
        from engine.realtime_collab import CRDTDocument
        doc = CRDTDocument(client_id)
        return _to_text({"client_id": client_id, "text": doc.get_text()})
    except Exception as e:
        return f"[ERR] 获取文本失败：{e}"

@mcp.tool()
async def kdoc_realtime_stats(client_id: str) -> str:
    """【免密钥】获取协同文档统计信息。

    client_id: 当前客户端标识
    本地 CRDT 引擎，零配置可用。"""
    try:
        from engine.realtime_collab import CRDTDocument
        doc = CRDTDocument(client_id)
        return _to_text(doc.get_stats())
    except Exception as e:
        return f"[ERR] 获取统计失败：{e}"


# ===========================================================================
# 十三、WPS AI 深度集成（v3.6.0 新增，段落级 AI 操作）
# ===========================================================================
@mcp.tool()
async def kdoc_wps_ai_rewrite(paragraph: str, style: str = "formal") -> str:
    """【免密钥】AI 段落改写：将指定段落按目标风格改写。

    style: formal(正式) / casual(口语) / concise(简洁) / elaborate(详细)
    本地降级占位，WPS AI API 开放后升级为原生。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        result = get_adapter().rewrite_paragraph(paragraph, style)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 段落改写失败：{e}"

@mcp.tool()
async def kdoc_wps_ai_summarize(paragraph: str, max_length: int = 100) -> str:
    """【免密钥】AI 段落总结：提取段落核心要点。

    max_length: 最大摘要字数
    本地降级占位，WPS AI API 开放后升级为原生。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        result = get_adapter().summarize_paragraph(paragraph, max_length)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 段落总结失败：{e}"

@mcp.tool()
async def kdoc_wps_ai_continue(paragraph: str, direction: str = "") -> str:
    """【免密钥】AI 段落续写：根据方向继续写作。

    direction: 续写方向（如"详细说明"、"举例"、"总结"）
    本地降级占位，WPS AI API 开放后升级为原生。"""
    try:
        from engine.wps_ai.adapter import get_adapter
        result = get_adapter().continue_paragraph(paragraph, direction)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 段落续写失败：{e}"


# ===========================================================================
# 十五、文档模板市场（v3.6.0 新增）
# ===========================================================================
@mcp.tool()
async def kdoc_template_list(category: str = "") -> str:
    """【免密钥】列出所有可用模板。

    category: 按类别筛选（可选）
    本地模板市场，零配置可用。"""
    try:
        from engine.template_marketplace import list_templates
        result = list_templates(category)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 获取模板列表失败：{e}"

@mcp.tool()
async def kdoc_template_search(keyword: str) -> str:
    """【免密钥】搜索模板。

    keyword: 搜索关键词
    本地模板市场，零配置可用。"""
    try:
        from engine.template_marketplace import search_templates
        result = search_templates(keyword)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 搜索模板失败：{e}"

@mcp.tool()
async def kdoc_template_use(name: str, variables: str = "{}") -> str:
    """【免密钥】使用模板（变量替换）。

    name: 模板名称
    variables: JSON 格式变量，如 '{"title": "周报", "author": "张三"}'
    本地模板市场，零配置可用。"""
    try:
        import json
        from engine.template_marketplace import use_template
        vars_dict = json.loads(variables) if variables else {}
        result = use_template(name, vars_dict)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 使用模板失败：{e}"

@mcp.tool()
async def kdoc_template_refresh() -> str:
    """【免密钥】刷新模板仓库（git pull）。

    本地模板市场，零配置可用。"""
    try:
        from engine.template_marketplace import refresh_templates
        result = refresh_templates(force=True)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 刷新模板失败：{e}"


# ===========================================================================
# 十六、文档对比（v3.5.0 新增，复用 difflib 引擎）
# ===========================================================================
@mcp.tool()
async def kdoc_compare_diff(text_a: str, text_b: str,
                            label_a: str = "版本A", label_b: str = "版本B") -> str:
    """【免密钥】文档对比：两版文档差异高亮。

    返回差异行列表+统计+相似度。本地 difflib 算法，零配置可用。"""
    try:
        from engine.doc_comparator import compare_documents
        result = compare_documents(text_a, text_b, label_a, label_b)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 文档对比失败：{e}"

@mcp.tool()
async def kdoc_compare_summary(text_a: str, text_b: str) -> str:
    """【免密钥】变更摘要：两版文档增删改统计+关键变化。

    本地 difflib 算法，零配置可用。"""
    try:
        from engine.doc_comparator import change_summary
        result = change_summary(text_a, text_b)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 变更摘要失败：{e}"

@mcp.tool()
async def kdoc_compare_export(text_a: str, text_b: str,
                              format: str = "markdown") -> str:
    """【免密钥】导出对比报告。

    format: markdown(默认) | html
    本地 difflib 算法，零配置可用。"""
    try:
        from engine.doc_comparator import export_report
        result = export_report(text_a, text_b, format)
        return result
    except Exception as e:
        return f"[ERR] 导出报告失败：{e}"


# ===========================================================================
# 十七、多维表格视图增强（v3.7.0 新增，对标 Airtable）
# ===========================================================================
@mcp.tool()
async def kdoc_view_render(view_type: str, data: str, config: str = "") -> str:
    """【免密钥】多维表格视图渲染：看板/日历/甘特图。

    view_type: kanban / calendar / gantt
    data: JSON 字符串，格式 {"records": [...], "fields": [...]}
    config: JSON 字符串（可选），如 {"mode": "month"}

    本地渲染引擎，零配置可用。"""
    try:
        import json
        from engine.views import render_view
        data_obj = json.loads(data)
        config_obj = json.loads(config) if config else None
        result = render_view(view_type, data_obj, config_obj)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 视图渲染失败：{e}"

@mcp.tool()
async def kdoc_view_list() -> str:
    """【免密钥】列出所有可用的多维表格视图类型。

    本地规则引擎，零配置可用。"""
    return _to_text({
        "views": [
            {"type": "kanban", "name": "看板", "description": "按状态字段分组卡片"},
            {"type": "calendar", "name": "日历", "description": "按日期字段月/周布局"},
            {"type": "gantt", "name": "甘特图", "description": "时间轴+任务依赖箭头"},
        ]
    })


# ===========================================================================
# 十八、手写/公式识别 OCR（v3.7.0 新增，教育场景）
# ===========================================================================
@mcp.tool()
async def kdoc_ocr_formula(image_path: str, output_format: str = "latex") -> str:
    """【免密钥】数学公式识别：图片 → LaTeX/MathML。

    image_path: 公式图片路径
    output_format: latex（默认）| mathml | text

    本地 Tesseract + 符号映射，零配置可用。"""
    try:
        from engine.ocr.formula_recognizer import FormulaRecognizer
        recognizer = FormulaRecognizer()
        result = recognizer.recognize(image_path, output_format)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 公式识别失败：{e}"

@mcp.tool()
async def kdoc_ocr_education(image_path: str, scene: str = "auto") -> str:
    """【免密钥】教育场景 OCR：手写公式/试卷/题目识别。

    image_path: 图片路径
    scene: auto（自动检测）| handwriting | formula | mixed

    自动判断手写体/印刷公式/混合内容，零配置可用。"""
    try:
        from engine.ocr.education import EducationOCR
        ocr = EducationOCR()
        result = ocr.recognize(image_path, scene)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 教育 OCR 失败：{e}"


# ===========================================================================
# 十九、历史管理（v3.7.0 新增，合并回收站+版本历史）
# ===========================================================================
@mcp.tool()
async def kdoc_history_list(source: str = "trash", limit: int = 20, offset: int = 0,
                            file_id: str = "") -> str:
    """列出历史记录：回收站文件 或 文档历史版本。

    source: trash（回收站）| version（版本历史，需传 file_id）
    limit: 数量限制
    offset: 分页偏移（仅 trash）
    file_id: 文档 ID（仅 version 需要）"""
    try:
        from engine.history import HistoryManager
        mgr = HistoryManager(backend=None)
        if source == "version" and file_id:
            result = mgr.list_versions(file_id, limit)
        else:
            result = mgr.list_history(source, limit, offset)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 获取历史列表失败：{e}"

@mcp.tool()
async def kdoc_history_restore(file_id: str, source: str = "trash",
                               version: int = 0) -> str:
    """恢复文件：从回收站还原 或 回滚到指定版本。

    file_id: 文件 ID
    source: trash | version
    version: 版本号（仅 version 需要，≥1）"""
    try:
        from engine.history import HistoryManager
        mgr = HistoryManager(backend=None)
        result = mgr.restore(file_id, source, version)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 恢复失败：{e}"

@mcp.tool()
async def kdoc_history_destroy(file_id: str) -> str:
    """⚠️ 危险操作（不可逆）：彻底删除回收站文件。执行前必须向用户二次确认。"""
    try:
        from engine.history import HistoryManager
        mgr = HistoryManager(backend=None)
        result = mgr.destroy(file_id)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 删除失败：{e}"


# ===========================================================================
# 二十、智能画布元素级编辑（v3.8.0 新增，对标腾讯文档）
# ===========================================================================
@mcp.tool()
async def kdoc_element_read(file_id: str, element_id: str = "") -> str:
    """【免密钥】读取智能画布元素。

    file_id: 文档 ID
    element_id: 元素 ID（空则返回全量结构化数据）
    本地降级模式，零配置可用。"""
    try:
        from engine.element_engine import CanvasElementEditor
        editor = CanvasElementEditor(backend=None)
        result = editor.read_element(file_id, element_id)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 元素读取失败：{e}"

@mcp.tool()
async def kdoc_element_insert(file_id: str, element_type: str, content: str,
                              position: int = -1, attributes: str = "") -> str:
    """【免密钥】在指定位置插入新元素。

    file_id: 文档 ID
    element_type: text / heading / image / table / divider / code / quote
    content: 元素内容
    position: 插入位置（-1 末尾）
    attributes: JSON 字符串（可选，如 {"level": 2}）
    本地降级模式，零配置可用。"""
    try:
        import json
        from engine.element_engine import CanvasElementEditor
        editor = CanvasElementEditor(backend=None)
        attrs = json.loads(attributes) if attributes else None
        result = editor.insert_element(file_id, element_type, content, position, attrs)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 元素插入失败：{e}"

@mcp.tool()
async def kdoc_element_update(file_id: str, element_id: str, content: str,
                              attributes: str = "") -> str:
    """【免密钥】更新指定元素。

    file_id: 文档 ID
    element_id: 元素 ID
    content: 新内容
    attributes: JSON 字符串（可选）
    本地降级模式，零配置可用。"""
    try:
        import json
        from engine.element_engine import CanvasElementEditor
        editor = CanvasElementEditor(backend=None)
        attrs = json.loads(attributes) if attributes else None
        result = editor.update_element(file_id, element_id, content, attrs)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 元素更新失败：{e}"

@mcp.tool()
async def kdoc_element_delete(file_id: str, element_id: str) -> str:
    """【免密钥】删除指定元素。

    file_id: 文档 ID
    element_id: 元素 ID
    本地降级模式，零配置可用。"""
    try:
        from engine.element_engine import CanvasElementEditor
        editor = CanvasElementEditor(backend=None)
        result = editor.delete_element(file_id, element_id)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 元素删除失败：{e}"

@mcp.tool()
async def kdoc_element_append_md(file_id: str, markdown_content: str,
                                 position: int = -1) -> str:
    """【免密钥】向文档末尾追加 Markdown 内容（增量，不改已有内容）。

    file_id: 文档 ID
    markdown_content: Markdown 内容
    position: 插入位置（-1 末尾）
    本地降级模式，零配置可用。"""
    try:
        from engine.element_engine import CanvasElementEditor
        editor = CanvasElementEditor(backend=None)
        result = editor.append_markdown(file_id, markdown_content, position)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] Markdown 追加失败：{e}"


# ===========================================================================
# 二十一、空间节点管理增强（v3.8.0 新增，对标腾讯文档）
# ===========================================================================
@mcp.tool()
async def kdoc_space_tree(folder_id: str = "", depth: int = 3) -> str:
    """【免密钥】列出空间目录树（递归）。

    folder_id: 文件夹 ID（空字符串表示根目录）
    depth: 递归深度（默认 3 层）
    本地降级模式，零配置可用。"""
    try:
        from engine.space_tree import SpaceTreeManager
        mgr = SpaceTreeManager(backend=None)
        result = mgr.list_tree(folder_id, depth=depth)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 目录树查询失败：{e}"

@mcp.tool()
async def kdoc_space_tree_visualize(folder_id: str = "", format: str = "json") -> str:
    """【免密钥】目录可视化（JSON/Markdown 树形）。

    folder_id: 文件夹 ID（空字符串表示根目录）
    format: json | markdown
    本地降级模式，零配置可用。"""
    try:
        from engine.space_tree import SpaceTreeManager
        mgr = SpaceTreeManager(backend=None)
        result = mgr.visualize_tree(folder_id, format=format)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 目录可视化失败：{e}"

@mcp.tool()
async def kdoc_space_node_create(parent_id: str, name: str, target_id: str,
                                 node_type: str = "shortcut") -> str:
    """【免密钥】创建链接节点（快捷方式/引用）。

    parent_id: 父文件夹 ID
    name: 节点名称
    target_id: 目标文件/文件夹 ID
    node_type: shortcut | reference
    本地降级模式，零配置可用。"""
    try:
        from engine.space_tree import SpaceTreeManager
        mgr = SpaceTreeManager(backend=None)
        result = mgr.create_link_node(parent_id, name, target_id, node_type)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 节点创建失败：{e}"

@mcp.tool()
async def kdoc_space_delete_recursive(folder_id: str, dry_run: bool = True) -> str:
    """⚠️ 危险操作：递归删除文件夹及其所有子内容。

    folder_id: 要删除的文件夹 ID
    dry_run: True 时仅预览不执行（默认安全模式）
    本地降级模式，零配置可用。"""
    try:
        from engine.space_tree import SpaceTreeManager
        mgr = SpaceTreeManager(backend=None)
        result = mgr.delete_recursive(folder_id, dry_run)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 递归删除失败：{e}"


# ===========================================================================
# 二十二、文档内容全文搜索（v3.8.0 新增，超越腾讯）
# ===========================================================================
@mcp.tool()
async def kdoc_content_search(query: str, file_id: str = "", limit: int = 20) -> str:
    """【免密钥】全文搜索文档内容（超越腾讯：搜内容+结果定位高亮）。

    query: 搜索关键词
    file_id: 限定搜索范围（空字符串搜索全部文档）
    limit: 返回结果数量限制
    本地降级模式，零配置可用。"""
    try:
        from engine.content_search import ContentSearchEngine
        engine = ContentSearchEngine(backend=None)
        result = engine.search(query, file_id, limit)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 全文搜索失败：{e}"

@mcp.tool()
async def kdoc_content_search_in_document(file_id: str, query: str) -> str:
    """【免密钥】在指定文档内搜索，返回匹配行及上下文。

    file_id: 文档 ID
    query: 搜索关键词
    本地降级模式，零配置可用。"""
    try:
        from engine.content_search import ContentSearchEngine
        engine = ContentSearchEngine(backend=None)
        result = engine.search_in_document(file_id, query)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 文档内搜索失败：{e}"


# ===========================================================================
# 二十三、统一删除（v3.8.0 新增，合并 delete + trash destroy）
# ===========================================================================
@mcp.tool()
async def kdoc_file_delete_unified(file_id: str, force: bool = False,
                                  from_trash: bool = False) -> str:
    """文件删除统一入口（合并软删除/彻底删除/直接删除）。

    file_id: 文件 ID
    force: True 时直接彻底删除（跳过回收站，⚠️ 需二次确认）
    from_trash: True 时从回收站彻底删除；False 时软删除到回收站

    用法：
        delete(file_id)                    → 软删除到回收站
        delete(file_id, from_trash=True)   → 从回收站彻底删除
        delete(file_id, force=True)       → 直接彻底删除（⚠️）
    需配置金山 App Key 后可用。"""
    try:
        from engine.history import HistoryManager
        mgr = HistoryManager(backend=None)
        result = mgr.delete(file_id, force=force, from_trash=from_trash)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 删除失败：{e}"


# ===========================================================================
# 二十四、本地 OCR 升级（v3.7.0 升级提示）
# ===========================================================================
@mcp.tool()
async def kdoc_local_ocr_extract(image_path: str, lang: str = "chi_sim+eng") -> str:
    """【免密钥】本地 OCR 提取图片文字：强制本地 Tesseract（数据不出域）。

    未安装 Tesseract 给出安装指引，不调用任何外部 API。"""
    try:
        from engine.local.ocr import extract_text
        res = extract_text(image_path, lang=lang)
        if res["source"] == "none":
            return f"[OCR 未就绪] {res['hint']}"
        return _to_text(res)
    except Exception as e:
        return f"[ERR] OCR 失败：{e}"


# ===========================================================================
# 十五、品类管理（v3.5.0 新增，9 品类 + 子类型识别）
# ===========================================================================
@mcp.tool()
async def kdoc_category_resolve(user_input: str) -> str:
    """【免密钥】品类识别：根据用户输入自动识别文档品类（9 品类）。

    返回品类 ID、名称、子类型、编辑方式。本地规则引擎，零配置可用。"""
    try:
        from engine.categories import resolve_category
        result = resolve_category(user_input)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 品类识别失败：{e}"

@mcp.tool()
async def kdoc_category_list() -> str:
    """【免密钥】列出所有可用品类（9 品类）。

    本地规则引擎，零配置可用。"""
    try:
        from engine.categories import list_categories
        result = list_categories()
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 获取品类列表失败：{e}"


# ===========================================================================
# 二十五、块级编辑引擎（v3.9.0 新增，段落级在线编辑）
# ===========================================================================
@mcp.tool()
async def kdoc_block_list(file_id: str) -> str:
    """【免密钥】拉取文档块列表（段落级编辑基础）。

    file_id: 文档 ID
    本地降级模式，零配置可用。"""
    try:
        from engine.blocks import BlockEditor
        editor = BlockEditor(backend=None)
        result = editor.blocks_list(file_id)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 拉取块列表失败：{e}"

@mcp.tool()
async def kdoc_block_replace(file_id: str, block_id: str, content: str,
                             block_type: str = "paragraph") -> str:
    """【免密钥】按 block_id 替换块内容。

    file_id: 文档 ID
    block_id: 块 ID
    content: 新内容
    block_type: paragraph / heading / list / table / code / quote / divider
    本地降级模式，零配置可用。"""
    try:
        from engine.blocks import BlockEditor
        editor = BlockEditor(backend=None)
        result = editor.block_replace(file_id, block_id, content, block_type)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 替换块失败：{e}"

@mcp.tool()
async def kdoc_block_insert(file_id: str, block_id: str, content: str,
                            position: str = "after", block_type: str = "paragraph") -> str:
    """【免密钥】按 block_id 插入新块。

    file_id: 文档 ID
    block_id: 参考块 ID
    content: 新块内容
    position: after（之后）/ before（之前）
    block_type: paragraph / heading / list / table / code / quote / divider
    本地降级模式，零配置可用。"""
    try:
        from engine.blocks import BlockEditor
        editor = BlockEditor(backend=None)
        result = editor.block_insert(file_id, block_id, content, position, block_type)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 插入块失败：{e}"

@mcp.tool()
async def kdoc_block_delete(file_id: str, block_id: str) -> str:
    """【免密钥】按 block_id 删除块。

    file_id: 文档 ID
    block_id: 块 ID
    本地降级模式，零配置可用。"""
    try:
        from engine.blocks import BlockEditor
        editor = BlockEditor(backend=None)
        result = editor.block_delete(file_id, block_id)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 删除块失败：{e}"

@mcp.tool()
async def kdoc_block_move(file_id: str, block_id: str,
                          target_block_id: str, position: str = "after") -> str:
    """【免密钥】按 block_id 移动块。

    file_id: 文档 ID
    block_id: 要移动的块 ID
    target_block_id: 目标块 ID
    position: after / before
    本地降级模式，零配置可用。"""
    try:
        from engine.blocks import BlockEditor
        editor = BlockEditor(backend=None)
        result = editor.block_move(file_id, block_id, target_block_id, position)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 移动块失败：{e}"


# ===========================================================================
# 二十六、演示页替换引擎（v3.9.0 新增，双路径自动选择）
# ===========================================================================
@mcp.tool()
async def kdoc_page_swap(file_id: str, source_path: str, page_number: int,
                         title: str = "", bullets: str = "",
                         layout: str = "title_and_content") -> str:
    """【免密钥】替换演示文稿中的指定页（自动选择页级更新或整文件替换）。

    file_id: 在线文档 ID
    source_path: 原始 PPTX 本地路径
    page_number: 页码（从1开始）
    title: 新页面标题
    bullets: 新页面要点（每行一个）
    layout: 页面布局（title_and_content / title_only / blank）
    本地降级模式，零配置可用。"""
    try:
        from engine.page_swap import PptxPageSwapEngine
        page_content = {
            "title": title,
            "bullets": [b.strip() for b in bullets.splitlines() if b.strip()],
            "layout": layout,
        }
        engine = PptxPageSwapEngine(backend=None)
        result = engine.swap_page(file_id, source_path, page_content, page_number)
        return _to_text(result.to_dict())
    except Exception as e:
        return f"[ERR] 页替换失败：{e}"


# ===========================================================================
# 二十七、配额管理器（v3.9.0 新增，API 配额与限流）
# ===========================================================================
@mcp.tool()
async def kdoc_quota_check() -> str:
    """【免密钥】检查当前配额状态（按天计数，500 次/天限制）。

    返回剩余配额、使用率、状态。
    本地模式，零配置可用。"""
    try:
        from engine.quota_manager import check_quota
        result = check_quota()
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 配额检查失败：{e}"

@mcp.tool()
async def kdoc_quota_dashboard() -> str:
    """【免密钥】获取配额看板（配额+令牌桶+硬件+小时分布+建议）。

    本地模式，零配置可用。"""
    try:
        from engine.quota_manager import get_dashboard
        result = get_dashboard()
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 获取看板失败：{e}"

@mcp.tool()
async def kdoc_quota_batch_params(total_items: int) -> str:
    """【免密钥】计算安全的批量任务参数（硬件自适应削峰）。

    total_items: 总任务数
    返回 workers、batch_chunk、预估时间、建议。
    本地模式，零配置可用。"""
    try:
        from engine.quota_manager import get_safe_batch_params
        result = get_safe_batch_params(total_items)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 计算批量参数失败：{e}"


# ===========================================================================
# 二十八、格式转换引擎（v3.9.0 升级，补齐 jpg/png/txt）
# ===========================================================================
@mcp.tool()
async def kdoc_office_convert_enhanced(file_id: str, source_path: str,
                                      target_format: str) -> str:
    """【免密钥】格式转换（云端优先 → 本地兜底）。

    file_id: 在线文档 ID
    source_path: 源文件本地路径
    target_format: pdf / jpg / png / txt / docx / xlsx / pptx / html / md

    v3.9.0 新增：补齐 jpg/png/txt 三类目标格式，全量覆盖参数校验与失败降级链。
    本地降级模式，零配置可用。"""
    try:
        from engine.format_converter import convert_file
        result = convert_file(backend=None, file_id=file_id,
                              source_path=source_path, target_format=target_format)
        return _to_text(result)
    except Exception as e:
        return f"[ERR] 格式转换失败：{e}"


def main():
    # 兼容 setup 传入的 --config 参数（FastMCP 自身不消费，需提前剥离）
    argv = [a for a in sys.argv[1:] if not a.startswith("--config")]
    sys.argv[1:] = argv
    mcp.run()


if __name__ == "__main__":
    main()
