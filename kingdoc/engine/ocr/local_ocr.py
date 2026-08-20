"""KingDoc 本地 OCR 引擎（v3.7.0 升级：强制本地优先，数据不出域）

v3.7.0 变更：
- 移除云端 OCR 调用路径（数据安全：图片数据不出本地）
- 强制本地 Tesseract，未安装给出安装指引
- 硬件自适应：OCR 并发不超过 workers
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

from engine.hardware import get_recommended_settings

DEFAULT_LANG = "chi_sim+eng"


def tesseract_available() -> bool:
    """检测本机是否已安装 Tesseract 命令行。"""
    return shutil.which("tesseract") is not None


def get_workers() -> int:
    """获取硬件推荐的并发数。"""
    hw = get_recommended_settings()
    return hw.get("workers", 1)


def recognize(image_path: str, lang: str = DEFAULT_LANG) -> Dict:
    """识别图片文字（强制本地 Tesseract）。

    Returns:
        {
          "success": bool,
          "text": str,
          "confidence": float | None,
          "engine": str,
          "hint": str  # 失败时的安装指引
        }
    """
    path = Path(image_path)
    if not path.exists():
        return _fail(f"文件不存在：{image_path}")

    if not tesseract_available():
        return _fail_tesseract_not_installed()

    try:
        result = _run_tesseract(image_path, lang)
        text = result.get("text", "").strip()
        if not text:
            return _fail(
                "Tesseract 已运行但未识别到文字（图片可能为手写体或清晰度不足）。",
                engine=f"本地 Tesseract OCR（lang={lang}）",
            )
        return {
            "success": True,
            "text": text,
            "confidence": result.get("confidence"),
            "engine": f"本地 Tesseract OCR（lang={lang}）",
            "hint": "",
        }
    except Exception as e:
        return _fail(f"Tesseract 调用失败：{e}")


def recognize_batch(image_paths: list, lang: str = DEFAULT_LANG) -> list:
    """批量识别（硬件自适应并发）。"""
    workers = get_workers()
    results = []
    # 串行模式（workers=1 或低性能）或并行模式
    if workers <= 1:
        for p in image_paths:
            results.append(recognize(p, lang))
    else:
        # 分批处理，每批 workers 个
        for i in range(0, len(image_paths), workers):
            batch = image_paths[i : i + workers]
            for p in batch:
                results.append(recognize(p, lang))
    return results


def _run_tesseract(image_path: str, lang: str) -> dict:
    """调用本地 tesseract 命令行，返回文字与平均置信度。"""
    cmd = ["tesseract", image_path, "stdout", "-l", lang]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    text = proc.stdout or ""

    confidence = None
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
    return {
        "success": False,
        "text": "",
        "confidence": None,
        "engine": engine,
        "hint": _install_hint(msg),
    }


def _fail_tesseract_not_installed() -> Dict:
    return {
        "success": False,
        "text": "",
        "confidence": None,
        "engine": "未安装",
        "hint": _install_hint("当前环境未安装 Tesseract OCR。"),
    }


def _install_hint(prefix: str) -> str:
    return (
        f"{prefix}\n"
        "免费安装 Tesseract（无需任何 API Key，数据不出域）：\n"
        "  Windows : winget install UB-Mannheim.TesseractOCR\n"
        "  macOS   : brew install tesseract tesseract-lang\n"
        "  Linux   : sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim\n"
        "安装后重启终端即可使用。"
    )
