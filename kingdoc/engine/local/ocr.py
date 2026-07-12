"""KingDoc 本地 OCR 模块（尽量不依赖任何外部付费 key）

设计目标（来自评测意见「部分高级功能需要安装额外软件」）：
- 默认走**本地 Tesseract OCR**：免费、离线、零密钥，是首选方案。
- 若本机未安装 Tesseract，自动降级为「云端正版 OCR」（需已配置的金山 App Key，可选）。
- 若两者都不可用，给出清晰的安装指引，而不是静默失败。

不引入任何付费 OCR API Key；Tesseract 与金山开放平台均为免费额度。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


# 内置默认语言：中英文。用户可在调用时覆盖。
DEFAULT_LANG = "chi_sim+eng"


def tesseract_available() -> bool:
    """检测本机是否已安装 Tesseract 命令行。"""
    return shutil.which("tesseract") is not None


def extract_text(
    image_path: str,
    lang: str = DEFAULT_LANG,
    use_cloud_fallback: bool = True,
    config_path: Optional[str] = None,
) -> Dict:
    """提取图片文字。

    Returns:
        {
          "source": "tesseract" | "cloud" | "none",
          "text": str,
          "confidence": float | None,
          "engine": str,    # 人类可读说明
          "hint": str       # 当失败时给用户的建议
        }
    """
    path = Path(image_path)
    if not path.exists():
        return _fail(f"文件不存在：{image_path}")

    # 方案 1：本地 Tesseract（免费、无需 key，首选）
    if tesseract_available():
        try:
            result = _run_tesseract(image_path, lang)
            if result.get("text", "").strip():
                return {
                    "source": "tesseract",
                    "text": result["text"],
                    "confidence": result.get("confidence"),
                    "engine": f"本地 Tesseract OCR（lang={lang}）",
                    "hint": "",
                }
            # Tesseract 跑通但没识别到文字（可能是纯图/手写体）
            return _fail(
                "Tesseract 已运行但未识别到文字（图片可能为手写体或清晰度不足）。",
                engine=f"本地 Tesseract OCR（lang={lang}）",
            )
        except Exception as e:  # 仅 Tesseract 调用异常才继续降级
            pass

    # 方案 2：云端正版 OCR（需要金山 App Key，可选）
    if use_cloud_fallback:
        try:
            from engine.api.tools import KingDocMcpServer
            backend = KingDocMcpServer(config_path) if config_path else KingDocMcpServer("config.json")
            resp = backend.kdoc_office_extract(image_path)
            text = (resp.get("data", {}) or {}).get("text") or resp.get("text") or ""
            if text.strip():
                return {
                    "source": "cloud",
                    "text": text,
                    "confidence": None,
                    "engine": "金山开放平台 OCR（云端，需 App Key）",
                    "hint": "",
                }
        except Exception:
            pass

    # 方案 3：全部不可用，给出友好指引（不抛异常、不崩溃）
    return _fail(
        "当前环境未配置任何 OCR 引擎。推荐免费方案：本地安装 Tesseract（无需任何 key）。",
        engine="未配置",
    )


def _run_tesseract(image_path: str, lang: str) -> Dict:
    """调用本地 tesseract 命令行，返回文字与平均置信度。"""
    cmd = ["tesseract", image_path, "stdout", "-l", lang]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    text = proc.stdout or ""
    confidence = None
    # 尝试用 tsv 模式拿置信度
    try:
        tsv = subprocess.run(
            ["tesseract", image_path, "stdout", "-l", lang, "tsv"],
            capture_output=True, text=True, timeout=120,
        )
        confs = []
        for line in tsv.stdout.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) > 10:
                try:
                    c = float(parts[10])
                    if c >= 0:
                        confs.append(c)
                except ValueError:
                    pass
        if confs:
            confidence = round(sum(confs) / len(confs), 1)
    except Exception:
        confidence = None
    return {"text": text, "confidence": confidence}


def _fail(msg: str, engine: str = "未配置") -> Dict:
    hint = (
        "免费安装 Tesseract（无需任何 API Key）：\n"
        "  Windows : winget install UB-Mannheim.TesseractOCR\n"
        "  macOS   : brew install tesseract tesseract-lang\n"
        "  Linux   : sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim\n"
        "安装后重启终端即可。也可在金山开放平台配置 App Key 使用云端 OCR。"
    )
    return {"source": "none", "text": "", "confidence": None, "engine": engine, "hint": f"{msg}\n{hint}"}


def image_to_table(image_path: str, lang: str = DEFAULT_LANG) -> Dict:
    """图片→表格：先做 OCR，再尝试把识别结果解析为二维表。

    轻量启发式：按空行/制表符/多空格切分行列，结果供后续写入电子表格。
    """
    ocr = extract_text(image_path, lang=lang)
    if ocr["source"] == "none":
        return ocr
    rows = []
    for raw_line in ocr["text"].splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # 以制表符或 2+ 空格作为列分隔
        cells = [c.strip() for c in line.replace("\t", "  ").split("  ") if c.strip()]
        if cells:
            rows.append(cells)
    return {
        **ocr,
        "rows": rows,
        "note": "表格为 OCR 启发式解析结果，复杂表格请在金山电子表格中二次校正。",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m engine.local.ocr <image_path> [lang]")
        sys.exit(1)
    out = extract_text(sys.argv[1], lang=sys.argv[2] if len(sys.argv) > 2 else DEFAULT_LANG)
    print(json.dumps(out, ensure_ascii=False, indent=2) if "json" in dir() else out)
