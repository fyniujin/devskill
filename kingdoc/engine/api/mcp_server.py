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

APP_VERSION = "3.3.0"

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


def main():
    # 兼容 setup 传入的 --config 参数（FastMCP 自身不消费，需提前剥离）
    argv = [a for a in sys.argv[1:] if not a.startswith("--config")]
    sys.argv[1:] = argv
    mcp.run()


if __name__ == "__main__":
    main()
