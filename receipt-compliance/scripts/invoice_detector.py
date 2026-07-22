#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
票种自动识别模块
根据文件类型、内容特征自动判断是传统发票还是全电发票
并路由到对应的解析器
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple

from unified_invoice import UnifiedInvoice
from xml_parser import FullElectronicInvoiceParser
from ofd_parser import OFDParser


class InvoiceDetector:
    """
    票种识别器 + 路由器
    
    支持的文件扩展名：
    - 传统发票：.png, .jpg, .jpeg, .tiff, .pdf, .bmp
    - 全电发票 XML：.xml
    - 全电发票 OFD：.ofd
    """
    
    TRADITIONAL_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.pdf', '.bmp'}
    FULL_ELECTRONIC_XML_EXTENSIONS = {'.xml'}
    FULL_ELECTRONIC_OFD_EXTENSIONS = {'.ofd'}
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        self.extension = self.file_path.suffix.lower()
        self.size = self.file_path.stat().st_size
    
    def detect(self) -> str:
        """
        检测票种类型
        
        Returns:
            "traditional" | "full_electronic_xml" | "full_electronic_ofd"
        """
        if self.extension in self.TRADITIONAL_EXTENSIONS:
            return "traditional"
        
        if self.extension in self.FULL_ELECTRONIC_XML_EXTENSIONS:
            # 进一步判断：可能是传统发票PDF转XML？全电？
            return self._detect_xml_type()
        
        if self.extension in self.FULL_ELECTRONIC_OFD_EXTENSIONS:
            return "full_electronic_ofd"
        
        # 未知类型，尝试读取文件头判断
        return self._detect_by_content()
    
    def _detect_xml_type(self) -> str:
        """对于XML文件，需要进一步判断是全电还是其他XML"""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                head = f.read(2000)
            
            # 全电发票特征：包含税务相关命名空间或关键标签
            full_electronic_indicators = [
                'InvoiceNumber', 'Fphm', 'FPHM',
                'chinatax.gov.cn',
                'SellerName', 'BuyerName',
                'SpecificBusinessInfo',
            ]
            
            for indicator in full_electronic_indicators:
                if indicator in head:
                    return "full_electronic_xml"
            
            # 无法确定时默认传统（实际可能需要用户指定）
            return "traditional"
            
        except Exception:
            return "traditional"
    
    def _detect_by_content(self) -> str:
        """通过文件内容特征判断（文件头魔数）"""
        try:
            with open(self.file_path, 'rb') as f:
                header = f.read(16)
            
            # OFD 文件头标识（PK ZIP格式）
            if header[:4] == b'PK\x03\x04':
                # 可能是OFD（因为OFD是ZIP格式）
                return "full_electronic_ofd"
            
            # XML 文件（以 <?xml 开头）
            if header[:5] == b'<?xml':
                return self._detect_xml_type()
            
            # 默认传统格式
            return "traditional"
            
        except Exception:
            return "traditional"
    
    def get_route(self) -> Tuple[str, callable]:
        """
        获取路由信息和处理函数
        
        Returns:
            (type_str, handler_function)
        """
        invoice_type = self.detect()
        
        if invoice_type == "traditional":
            return ("traditional", self._handle_traditional)
        elif invoice_type == "full_electronic_xml":
            return ("full_electronic_xml", self._handle_full_electronic_xml)
        elif invoice_type == "full_electronic_ofd":
            return ("full_electronic_ofd", self._handle_full_electronic_ofd)
        else:
            return ("unknown", self._handle_unknown)
    
    def _handle_traditional(self) -> Dict[str, Any]:
        """传统发票处理入口"""
        return {
            "type": "traditional",
            "message": "检测到传统发票格式，请将图片/PDF输入OCR引擎进行识别",
            "next_step": "使用 ocr_engine.py 进行识别",
            "supported": True,
            "engine": "ocr_engine.py"
        }
    
    def _handle_full_electronic_xml(self) -> Dict[str, Any]:
        """全电发票XML处理入口"""
        try:
            parser = FullElectronicInvoiceParser(str(self.file_path))
            parser.load()
            invoice = parser.parse()
            
            return {
                "type": "full_electronic_xml",
                "message": "检测到全电发票XML格式",
                "next_step": "提取结构化数据",
                "supported": True,
                "data": invoice.to_dict(),
                "validation_errors": invoice.validate(),
            }
            
        except Exception as e:
            return {
                "type": "full_electronic_xml",
                "message": f"解析失败: {e}",
                "supported": True,
                "error": str(e),
            }
    
    def _handle_full_electronic_ofd(self) -> Dict[str, Any]:
        """全电发票OFD处理入口"""
        parser = OFDParser(str(self.file_path))
        result = parser.parse()
        
        if result.get('extractable'):
            return {
                "type": "full_electronic_ofd",
                "message": "检测到全电发票OFD格式",
                "next_step": "文字提取成功",
                "supported": True,
                "data": result,
            }
        else:
            return {
                "type": "full_electronic_ofd",
                "message": "检测到全电发票OFD格式，但文字提取能力有限",
                "next_step": "建议使用 ofdparser 库或转换为PDF后OCR",
                "supported": False,
                "data": result,
                "alternatives": result.get('install_hint', ''),
            }
    
    def _handle_unknown(self) -> Dict[str, Any]:
        """未知类型处理"""
        return {
            "type": "unknown",
            "message": f"无法识别的文件格式: {self.extension}",
            "supported": False,
            "supported_formats": {
                "traditional": list(self.TRADITIONAL_EXTENSIONS),
                "full_electronic_xml": list(self.FULL_ELECTRONIC_XML_EXTENSIONS),
                "full_electronic_ofd": list(self.FULL_ELECTRONIC_OFD_EXTENSIONS),
            }
        }
    
    def process(self) -> Dict[str, Any]:
        """
        一键处理入口
        检测票种并自动调用对应解析器
        """
        invoice_type, handler = self.get_route()
        result = handler()
        result['file'] = str(self.file_path)
        result['file_size'] = self.size
        return result


def detect_and_process(file_path: str) -> Dict[str, Any]:
    """
    便捷函数：识别票种并自动处理
    
    Args:
        file_path: 发票文件路径
    
    Returns:
        dict: 处理结果
    """
    detector = InvoiceDetector(file_path)
    return detector.process()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python invoice_detector.py <path_to_invoice>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        result = detect_and_process(file_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"处理失败: {e}", file=sys.stderr)
        sys.exit(1)
