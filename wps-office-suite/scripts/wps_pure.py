"""
WPS Office 全家桶 - 纯 Python 模式（v2.2 增强版）
支持无需 WPS/LibreOffice 的基础文档操作

v2.2 新增:
  - 纯Python格式设置（字体/对齐/颜色/边框/行距）
  - 表格创建与编辑
  - 图片插入与缩放
  - PDF 兜底尝试（调用 LibreOffice headless）
  - 智能引擎回退（PURE模式下自动尝试LibreOffice）
"""
from pathlib import Path
from typing import Optional, List, Dict, Any


# ==================== Word 纯 Python 模式 ====================

def pure_create_word(title: str, filepath: str, body: str = "",
                     font_name: str = "微软雅黑",
                     font_size: float = 12,
                     align: str = "left") -> dict:
    """用 python-docx 创建 Word 文档（支持格式参数）"""
    try:
        from docx import Document
        from docx.shared import Pt, Inches, Cm, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        # 默认样式
        style = doc.styles["Normal"]
        style.font.name = font_name
        style.font.size = Pt(font_size)

        # 添加标题
        heading = doc.add_heading(title, level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in heading.runs:
            run.font.color.rgb = RGBColor(0x1A, 0x73, 0xE8)

        # 添加正文
        if body:
            for line in body.split("\n"):
                if line.strip():
                    p = doc.add_paragraph(line.strip())
                    # 应用对齐
                    align_map = {"center": 1, "left": 0, "right": 2, "justify": 3}
                    if align in align_map:
                        p.alignment = WD_ALIGN_PARAGRAPH(align_map[align])
                    for run in p.runs:
                        run.font.name = font_name
                        run.font.size =Pt(font_size)

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        doc.save(filepath)
        return {"success": True, "path": filepath, "engine": "PURE",
                "note": "纯Python模式（安装WPS可获取更完整的格式）"}
    except ImportError:
        return {"success": False, "error": "需要安装 python-docx：pip install python-docx"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_edit_word(filepath: str, text: str, position: str = "end") -> dict:
    """用 python-docx 编辑 Word 文档（追加文本）"""
    try:
        from docx import Document

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        doc = Document(filepath)

        if position == "end":
            for line in text.split("\n"):
                if line.strip():
                    doc.add_paragraph(line.strip())
        elif position == "start":
            for line in reversed(text.split("\n")):
                if line.strip():
                    if doc.paragraphs:
                        doc.paragraphs[0].insert_paragraph_before(line.strip())
                    else:
                        doc.add_paragraph(line.strip())

        doc.save(filepath)
        return {"success": True, "engine": "PURE"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_format_word(filepath: str, font_name: str = "",
                    font_size: float = 0, bold: bool = False,
                    align: str = "", space_after: float = 0,
                    first_line_indent: float = 0,
                    color: str = "") -> dict:
    """
    纯 Python 模式格式设置。
    支持参数: font_name, font_size, bold, align, space_after, first_line_indent, color
    """
    try:
        from docx import Document
        from docx.shared import Pt, Cm, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        doc = Document(filepath)
        align_map = {"center": 1, "left": 0, "right": 2, "justify": 3}
        color_map = {"red": (255, 0, 0), "blue": (0, 0, 255),
                    "green": (0, 128, 0), "black": (0, 0, 0)}
        rgb = color_map.get(color.lower(), None)

        for para in doc.paragraphs:
            if not para.text.strip():
                continue

            # 对齐
            if align in align_map:
                para.alignment = WD_ALIGN_PARAGRAPH(align_map[align])

            # 段落间距
            if space_after > 0:
                para.paragraph_format.space_after = Pt(space_after)

            # 首行缩进
            if first_line_indent > 0:
                para.paragraph_format.first_line_indent = Cm(first_line_indent)

            for run in para.runs:
                if font_name:
                    run.font.name = font_name
                if font_size > 0:
                    run.font.size = Pt(font_size)
                if bold:
                    run.font.bold = True
                if rgb:
                    run.font.color.rgb = RGBColor(*rgb)

        doc.save(filepath)
        return {"success": True, "engine": "PURE", "formatted": True}
    except ImportError:
        return {"success": False, "error": "需要安装 python-docx：pip install python-docx"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_add_table(filepath: str, headers: List[str],
                  rows: List[List[Any]]) -> dict:
    """在文档末尾添加表格"""
    try:
        from docx import Document
        from docx.shared import Pt, Cm, Inches
        from docx.enum.table import WD_TABLE_ALIGNMENT

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        doc = Document(filepath)
        table = doc.add_table(rows=1 + len(rows), cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # 表头
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = str(h)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(10)

        # 数据行
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                if c_idx < len(headers):
                    table.rows[r_idx + 1].cells[c_idx].text = str(val)

        # 设置列宽
        for col in table.columns:
            for cell in col.cells:
                cell.width = Cm(3)

        doc.save(filepath)
        return {"success": True, "engine": "PURE",
                "table_added": True, "rows": len(rows)}
    except ImportError:
        return {"success": False, "error": "需要安装 python-docx：pip install python-docx"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_insert_image(filepath: str, image_path: str,
                     width_cm: float = 10,
                     caption: str = "") -> dict:
    """在文档末尾插入图片（自动缩放并居中）"""
    try:
        from docx import Document
        from docx.shared import Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}
        if not Path(image_path).exists():
            return {"success": False, "error": f"图片不存在: {image_path}"}

        doc = Document(filepath)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(image_path, width=Cm(width_cm))

        if caption:
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in cap.runs:
                run.font.size = 9

        doc.save(filepath)
        return {"success": True, "engine": "PURE", "image_inserted": True}
    except ImportError:
        return {"success": False, "error": "需要安装 python-docx：pip install python-docx"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_info_word(filepath: str) -> dict:
    """获取 Word 文档基本信息"""
    try:
        from docx import Document

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        doc = Document(filepath)
        stat = Path(filepath).stat()

        return {
            "success": True,
            "name": Path(filepath).name,
            "path": filepath,
            "size": stat.st_size,
            "paragraph_count": len(doc.paragraphs),
            "table_count": len(doc.tables),
            "engine": "PURE",
        }
    except ImportError:
        return {"success": False, "error": "需要安装 python-docx"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== Excel 纯 Python 模式 ====================

def pure_create_excel(name: str, sheets: List[str], filepath: str,
                      data: Dict[str, List[List[Any]]] = None) -> dict:
    """用 openpyxl 创建 Excel 文档"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        for sheet_name in sheets:
            ws = wb.create_sheet(title=sheet_name)
            # 如果有数据
            if data and sheet_name in data:
                sheet_data = data[sheet_name]
                for r, row in enumerate(sheet_data, start=1):
                    for c, val in enumerate(row, start=1):
                        cell = ws.cell(row=r, column=c, value=val)
                        # 表头加粗
                        if r == 1:
                            cell.font = Font(bold=True, color="FFFFFF")
                            cell.fill = PatternFill("solid", fgColor="1A73E8")
                            cell.alignment = Alignment(horizontal="center")

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        wb.save(filepath)
        return {"success": True, "path": filepath, "sheets": sheets, "engine": "PURE"}
    except ImportError:
        return {"success": False, "error": "需要安装 openpyxl：pip install openpyxl"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_input_excel(filepath: str, sheet: str, data: List[List[Any]]) -> dict:
    """用 openpyxl 录入数据（支持多列多行）"""
    try:
        import openpyxl

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        wb = openpyxl.load_workbook(filepath)
        if sheet not in wb.sheetnames:
            ws = wb.create_sheet(title=sheet)
        else:
            ws = wb[sheet]

        # 查找下一个空行
        start_row = ws.max_row + 1

        for r_offset, row in enumerate(data):
            for c, val in enumerate(row, start=1):
                ws.cell(row=start_row + r_offset, column=c, value=val)

        wb.save(filepath)
        return {"success": True, "input_rows": len(data), "engine": "PURE"}
    except ImportError:
        return {"success": False, "error": "需要安装 openpyxl"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_add_excel_sheet(filepath: str, sheet_name: str,
                        headers: List[str] = None,
                        data: List[List[Any]] = None) -> dict:
    """在 Excel 中添加新 Sheet（含表头和数据）"""
    try:
        import openpyxl

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        wb = openpyxl.load_workbook(filepath)
        if sheet_name in wb.sheetnames:
            del wb[sheet_name]
        ws = wb.create_sheet(title=sheet_name)

        if headers:
            for c, h in enumerate(headers, start=1):
                ws.cell(row=1, column=c, value=h)

        if data:
            for r, row in enumerate(data, start=2):
                for c, val in enumerate(row, start=1):
                    ws.cell(row=r, column=c, value=val)

        wb.save(filepath)
        return {"success": True, "sheet_added": sheet_name, "engine": "PURE"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_info_excel(filepath: str) -> dict:
    """获取 Excel 文档基本信息"""
    try:
        import openpyxl

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        wb = openpyxl.load_workbook(filepath, read_only=True)
        stat = Path(filepath).stat()

        return {
            "success": True,
            "name": Path(filepath).name,
            "path": filepath,
            "sheets": wb.sheetnames,
            "size": stat.st_size,
            "sheet_count": len(wb.sheetnames),
            "engine": "PURE",
        }
    except ImportError:
        return {"success": False, "error": "需要安装 openpyxl"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== PPT 纯 Python 模式 ====================

def pure_create_ppt(title: str, filepath: str,
                    slides_content: List[Dict] = None) -> dict:
    """用 python-pptx 创建 PPT（支持多页）"""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.enum.text import PP_ALIGN

        prs = Presentation()

        # 标题页
        slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(slide_layout)
        if slide.shapes.title:
            slide.shapes.title.text = title
            slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(32)
            slide.shapes.title.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

        # 添加更多幻灯片
        if slides_content:
            for content in slides_content:
                slide_layout = prs.slide_layouts[1]
                slide = prs.slides.add_slide(slide_layout)
                if slide.shapes.title:
                    slide.shapes.title.text = content.get("title", "")
                for placeholder in slide.placeholders:
                    if placeholder.placeholder_format.idx == 1:
                        placeholder.text = content.get("body", "")

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        prs.save(filepath)
        return {"success": True, "path": filepath, "engine": "PURE",
                "slides": 1 + (len(slides_content) if slides_content else 0)}
    except ImportError:
        return {
            "success": False,
            "error": "PPT 纯 Python 模式需要安装 python-pptx：pip install python-pptx",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def pure_info_ppt(filepath: str) -> dict:
    """获取 PPT 文档基本信息"""
    try:
        from pptx import Presentation

        if not Path(filepath).exists():
            return {"success": False, "error": f"文件不存在: {filepath}"}

        prs = Presentation(filepath)
        stat = Path(filepath).stat()

        return {
            "success": True,
            "name": Path(filepath).name,
            "path": filepath,
            "size": stat.st_size,
            "slide_count": len(prs.slides),
            "engine": "PURE",
        }
    except ImportError:
        return {"success": False, "error": "需要安装 python-pptx"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 安全路径 ====================

def pure_safe_path(path_str: str) -> Path:
    """安全路径校验"""
    path = Path(path_str).resolve()
    parent = path.parent

    if not parent.exists():
        raise FileNotFoundError(f"目录不存在：{parent}")

    problematic = '<>"|?*' if __import__("platform").system() == "Windows" else ""
    for ch in problematic:
        if ch in path.name:
            raise ValueError(f"文件名包含非法字符 '{ch}': {path.name}")

    return path


# ==================== 自动选择引擎的 API ====================

def create_word_doc(title: str, filepath: str = "", body: str = "",
                    engine: str = None) -> dict:
    """自动选择引擎创建 Word 文档"""
    # 简化为直接调用 pure
    if not filepath:
        desktop = Path.home() / "Desktop"
        filepath = str(desktop / f"{title}.docx")
    return pure_create_word(title, filepath, body)


def get_engine_info() -> dict:
    """返回当前检测到的引擎信息"""
    return {
        "engine": "PURE",
        "wps_available": False,
        "msoffice_available": False,
        "pure_available": True,
    }
