#!/usr/bin/env python3
"""
多格式文本提取模块
支持 PDF（文字版/扫描版）、Word、图片、纯文本
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TextExtractor:
    """多格式文本提取器"""
    
    # 类级别的 OCR 实例缓存，避免重复初始化
    _ocr_instance = None
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._extract_pdf,
            '.docx': self._extract_docx,
            '.doc': self._extract_docx,
            '.txt': self._extract_txt,
            '.md': self._extract_txt,
            '.jpg': self._extract_image,
            '.jpeg': self._extract_image,
            '.png': self._extract_image,
            '.bmp': self._extract_image,
            '.tiff': self._extract_image,
        }
    
    @classmethod
    def _get_ocr(cls):
        """获取或创建 OCR 实例（单例模式，避免重复初始化）"""
        if cls._ocr_instance is None:
            try:
                from paddleocr import PaddleOCR
                print("  ⏳ 初始化 OCR 引擎（首次使用需加载模型）...", flush=True)
                cls._ocr_instance = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
                print("  ✅ OCR 引擎初始化完成", flush=True)
            except ImportError:
                logger.error("paddleocr 未安装，请运行: pip install paddleocr")
                raise
        return cls._ocr_instance
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        提取文件中的文本
        
        Args:
            file_path: 文件路径
            
        Returns:
            {
                'text': str,  # 提取的文本
                'pages': list,  # 按页分割的文本
                'file_type': str,  # 文件类型
                'ocr_confidence': float,  # OCR置信度（仅扫描件）
                'metadata': dict,  # 元信息
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = path.suffix.lower()
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {ext}，支持的格式: {list(self.supported_formats.keys())}")
        
        logger.info(f"正在提取文件: {file_path} (格式: {ext})")
        return self.supported_formats[ext](file_path)
    
    def _extract_pdf(self, file_path: str) -> Dict[str, Any]:
        """提取 PDF 文本"""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber 未安装，请运行: pip install pdfplumber")
            raise
        
        pages_text = []
        
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages_text.append({
                    'page_num': i + 1,
                    'text': text,
                    'words': len(text),
                })
        
        total_pages = len(pages_text)
        
        full_text = '\n'.join([p['text'] for p in pages_text])
        
        # 判断是文字版还是扫描版
        is_scanned = self._is_scanned_pdf(pages_text)
        
        if is_scanned:
            logger.info("检测到扫描版 PDF，切换到 OCR 模式")
            return self._extract_pdf_with_ocr(file_path)
        
        return {
            'text': full_text,
            'pages': pages_text,
            'file_type': 'pdf_text',
            'ocr_confidence': None,
            'metadata': {
                'total_pages': total_pages,
                'total_words': len(full_text),
                'is_scanned': False,
            }
        }
    
    def _is_scanned_pdf(self, pages_text: list) -> bool:
        """判断 PDF 是否为扫描版"""
        if not pages_text:
            return True
        
        # 如果前3页的平均字数少于10页，认为是扫描版
        sample_pages = pages_text[:3]
        avg_words = sum(p['words'] for p in sample_pages) / len(sample_pages)
        return avg_words < 10
    
    def _extract_pdf_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """使用 OCR 提取扫描版 PDF"""
        try:
            from paddleocr import PaddleOCR
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("paddleocr 或 PyMuPDF 未安装，请运行: pip install paddleocr PyMuPDF")
            raise
        
        ocr = self._get_ocr()
        
        pages_text = []
        confidences = []
        
        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            
            # OCR 识别
            result = ocr.ocr(img_data, cls=True)
            
            page_text = ""
            page_confidences = []
            if result and result[0]:
                for line in result[0]:
                    box = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    page_text += text + " "
                    page_confidences.append(confidence)
            
            pages_text.append({
                'page_num': i + 1,
                'text': page_text.strip(),
                'words': len(page_text),
            })
            
            if page_confidences:
                confidences.extend(page_confidences)
        
        doc.close()
        
        full_text = '\n'.join([p['text'] for p in pages_text])
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': full_text,
            'pages': pages_text,
            'file_type': 'pdf_scan',
            'ocr_confidence': round(avg_confidence, 4),
            'metadata': {
                'total_pages': len(pages_text),
                'total_words': len(full_text),
                'is_scanned': True,
            }
        }
    
    def _extract_docx(self, file_path: str) -> Dict[str, Any]:
        """提取 Word 文档文本"""
        try:
            from docx import Document
        except ImportError:
            logger.error("python-docx 未安装，请运行: pip install python-docx")
            raise
        
        doc = Document(file_path)
        paragraphs = []
        
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                paragraphs.append({
                    'index': i,
                    'text': para.text,
                    'style': para.style.name if para.style else 'Normal',
                })
        
        full_text = '\n'.join([p['text'] for p in paragraphs])
        
        return {
            'text': full_text,
            'pages': [{'page_num': 1, 'text': full_text, 'words': len(full_text)}],
            'file_type': 'docx',
            'ocr_confidence': None,
            'metadata': {
                'total_pages': 1,
                'total_words': len(full_text),
                'total_paragraphs': len(paragraphs),
                'is_scanned': False,
            }
        }
    
    def _extract_txt(self, file_path: str) -> Dict[str, Any]:
        """提取纯文本"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            'text': text,
            'pages': [{'page_num': 1, 'text': text, 'words': len(text)}],
            'file_type': 'txt',
            'ocr_confidence': None,
            'metadata': {
                'total_pages': 1,
                'total_words': len(text),
                'is_scanned': False,
            }
        }
    
    def _extract_image(self, file_path: str) -> Dict[str, Any]:
        """使用 OCR 提取图片中的文本"""
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            logger.error("paddleocr 未安装，请运行: pip install paddleocr")
            raise
        
        ocr = self._get_ocr()
        
        result = ocr.ocr(file_path, cls=True)
        
        texts = []
        confidences = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                texts.append(text)
                confidences.append(confidence)
        
        full_text = ' '.join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': full_text,
            'pages': [{'page_num': 1, 'text': full_text, 'words': len(full_text)}],
            'file_type': 'image',
            'ocr_confidence': round(avg_confidence, 4),
            'metadata': {
                'total_pages': 1,
                'total_words': len(full_text),
                'is_scanned': True,
            }
        }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python extract_text.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    extractor = TextExtractor()
    
    try:
        result = extractor.extract(file_path)
        print(f"文件类型: {result['file_type']}")
        print(f"总页数: {result['metadata']['total_pages']}")
        print(f"总字数: {result['metadata']['total_words']}")
        if result['ocr_confidence']:
            print(f"OCR置信度: {result['ocr_confidence']}")
        print(f"\n--- 提取的文本 ---\n{result['text'][:2000]}...")
    except Exception as e:
        logger.error(f"提取失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
