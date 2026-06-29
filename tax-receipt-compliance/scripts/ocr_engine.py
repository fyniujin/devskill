#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票OCR识别引擎 - 基于Tesseract的本地化处理方案
企业自主配置，数据本地处理，不依赖第三方API
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime
import tempfile

# 尝试导入PIL
try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    print("ERROR: PIL未安装。请运行: pip install Pillow")
    sys.exit(1)

# 尝试导入pytesseract
try:
    import pytesseract
except ImportError:
    print("ERROR: pytesseract未安装。请运行: pip install pytesseract")
    sys.exit(1)

# 尝试导入pdf2image（PDF支持）
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class OCREngine:
    """发票OCR识别引擎"""

    def __init__(self, tesseract_cmd=None, lang='chi_sim+eng'):
        """
        初始化OCR引擎

        Args:
            tesseract_cmd: Tesseract可执行文件路径（可选，默认系统PATH）
            lang: 识别语言（默认中文简体+英文）
        """
        self.lang = lang
        self.tesseract_cmd = tesseract_cmd

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # 验证Tesseract是否可用
        self._verify_tesseract()

    def _verify_tesseract(self):
        """验证Tesseract OCR是否已安装"""
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise RuntimeError(
                f"Tesseract OCR未安装或无法访问: {e}\n"
                "请运行安装脚本 install_tesseract.sh 或 install_tesseract.ps1\n"
                "或手动安装: https://github.com/UB-Mannheim/tesseract/wiki"
            )

    def preprocess_image(self, image_path):
        """
        图像预处理：灰度化 → 去噪 → 二值化 → 纠偏

        Args:
            image_path: 图片文件路径

        Returns:
            预处理后的PIL Image对象
        """
        try:
            img = Image.open(image_path)
        except Exception as e:
            raise ValueError(f"无法打开图片文件: {image_path}, 错误: {e}")

        # 转换为灰度图
        if img.mode != 'L':
            img = img.convert('L')

        # 对比度增强
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # 锐化
        img = img.filter(ImageFilter.SHARPEN)

        # 二值化（自适应阈值）
        # 使用简单的全局阈值，生产环境可考虑自适应阈值
        threshold = 128
        img = img.point(lambda x: 0 if x < threshold else 255, '1')

        return img

    def extract_text(self, image_path):
        """
        从图片中提取文字

        Args:
            image_path: 图片文件路径

        Returns:
            识别到的文字内容
        """
        # 预处理
        processed_img = self.preprocess_image(image_path)

        # OCR识别
        try:
            text = pytesseract.image_to_string(
                processed_img,
                lang=self.lang,
                config='--psm 6'  # 假设为统一文本块
            )
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"OCR识别失败: {e}")

    def extract_structured_data(self, image_path):
        """
        从发票图片中提取结构化数据

        Args:
            image_path: 发票图片路径

        Returns:
            dict: 结构化发票数据
        """
        # 提取原始文本
        raw_text = self.extract_text(image_path)

        if not raw_text:
            return {
                'success': False,
                'error': '未识别到任何文字',
                'raw_text': ''
            }

        # 解析发票字段
        structured_data = self._parse_invoice_fields(raw_text)
        structured_data['raw_text'] = raw_text
        structured_data['success'] = True
        structured_data['timestamp'] = datetime.now().isoformat()
        structured_data['image_path'] = str(image_path)

        return structured_data

    def _parse_invoice_fields(self, text):
        """
        解析发票文字，提取关键字段

        Args:
            text: OCR识别到的原始文字

        Returns:
            dict: 解析后的字段
        """
        data = {
            'invoice_type': self._extract_invoice_type(text),
            'invoice_code': self._extract_field(text, ['发票代码', '代码'], r'\d{10,12}'),
            'invoice_number': self._extract_field(text, ['发票号码', '号码'], r'\d{8,20}'),
            'invoice_date': self._extract_date(text),
            'seller_name': self._extract_seller(text),
            'buyer_name': self._extract_buyer(text),
            'amount': self._extract_amount(text, ['金额', '不含税', '合计金额']),
            'tax_rate': self._extract_tax_rate(text),
            'tax_amount': self._extract_amount(text, ['税额', '税金']),
            'total': self._extract_amount(text, ['价税合计', '合计', '大写']),
            'remark': self._extract_remark(text)
        }

        # 估算置信度（简化版）
        data['confidence'] = self._calculate_confidence(data)

        return data

    def _extract_invoice_type(self, text):
        """提取发票类型"""
        patterns = {
            '增值税专用发票': ['增值税专用发票', '专票', '发票联'],
            '增值税电子发票': ['增值税电子发票', '电子发票', '电子'],
            '增值税普通发票': ['增值税普通发票', '普票', '普通发票'],
        }

        for invoice_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text:
                    return invoice_type
        return '未知类型'

    def _extract_field(self, text, field_names, pattern):
        """通用字段提取"""
        lines = text.split('\n')
        for line in lines:
            for name in field_names:
                if name in line:
                    # 尝试在行中查找匹配模式
                    match = re.search(pattern, line)
                    if match:
                        return match.group()
        return ''

    def _extract_date(self, text):
        """提取日期"""
        # 匹配格式：2026年06月28日 或 2026-06-28 或 2026/06/28
        patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"{match.group(1)}年{int(match.group(2)):02d}月{int(match.group(3)):02d}日"
        return ''

    def _extract_seller(self, text):
        """提取销售方名称"""
        lines = text.split('\n')
        for line in lines:
            if '销售方' in line or '销方' in line:
                # 提取公司名称（通常在"名称："之后）
                match = re.search(r'名称[：:]\s*([^\s]+)', line)
                if match:
                    return match.group(1)
        return ''

    def _extract_buyer(self, text):
        """提取购买方名称"""
        lines = text.split('\n')
        for line in lines:
            if '购买方' in line or '买方' in line:
                match = re.search(r'名称[：:]\s*([^\s]+)', line)
                if match:
                    return match.group(1)
        return ''

    def _extract_amount(self, text, field_names):
        """提取金额"""
        lines = text.split('\n')
        for line in lines:
            for name in field_names:
                if name in line:
                    # 匹配金额格式：¥10000.00 或 10000.00 或 10,000.00
                    match = re.search(r'[¥￥]?\s*([\d,]+\.?\d*)', line)
                    if match:
                        amount = match.group(1).replace(',', '')
                        try:
                            return float(amount)
                        except ValueError:
                            pass
        return 0.0

    def _extract_tax_rate(self, text):
        """提取税率"""
        match = re.search(r'(\d+)%', text)
        if match:
            return int(match.group(1)) / 100
        # 常见税率
        if '13%' in text:
            return 0.13
        elif '9%' in text:
            return 0.09
        elif '6%' in text:
            return 0.06
        return 0.0

    def _extract_remark(self, text):
        """提取备注或附注"""
        lines = text.split('\n')
        for line in lines:
            if '备注' in line or '附注' in line:
                match = re.search(r'[备注附注][：:]\s*(.+)', line)
                if match:
                    return match.group(1)
        return ''

    def _calculate_confidence(self, data):
        """计算识别置信度（简化版）"""
        # 排除 confidence 本身和 raw_text、image_path 等非字段信息
        exclude_keys = {'confidence', 'raw_text', 'image_path', 'success', 'timestamp'}
        field_data = {k: v for k, v in data.items() if k not in exclude_keys}
        filled_fields = sum(1 for v in field_data.values() if v and v != 0.0)
        total_fields = len(field_data)
        return round(filled_fields / total_fields, 2) if total_fields > 0 else 0.0


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='发票OCR识别引擎')
    parser.add_argument('--input', required=True, help='输入图片路径或目录')
    parser.add_argument('--output', help='输出JSON文件路径（可选）')
    parser.add_argument('--tesseract', help='Tesseract可执行文件路径')
    parser.add_argument('--lang', default='chi_sim+eng', help='识别语言')

    args = parser.parse_args()

    # 初始化OCR引擎
    try:
        engine = OCREngine(tesseract_cmd=args.tesseract, lang=args.lang)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # 处理单个文件或目录
    input_path = Path(args.input)

    if input_path.is_file():
        # 单文件模式
        if input_path.suffix.lower() == '.pdf':
            if not PDF_SUPPORT:
                print("ERROR: PDF支持未启用，请安装pdf2image: pip install pdf2image")
                sys.exit(1)
            # PDF处理
            images = convert_from_path(input_path)
            results = []
            temp_dir = Path(tempfile.gettempdir()) / "tax_receipt_temp"
            temp_dir.mkdir(exist_ok=True)
            try:
                for i, img in enumerate(images):
                    temp_path = temp_dir / f"pdf_page_{i}.png"
                    img.save(temp_path, 'PNG')
                    result = engine.extract_structured_data(temp_path)
                    result['page'] = i + 1
                    results.append(result)
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass  # 清理失败不影响主流程
            finally:
                # 清理临时目录
                try:
                    if not any(temp_dir.iterdir()):
                        temp_dir.rmdir()
                except OSError:
                    pass
            output_data = results
        else:
            output_data = engine.extract_structured_data(input_path)

    elif input_path.is_dir():
        # 目录模式
        results = []
        supported_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        if PDF_SUPPORT:
            supported_extensions.add('.pdf')

        for file_path in input_path.iterdir():
            if file_path.suffix.lower() in supported_extensions:
                print(f"正在识别: {file_path.name}...")
                try:
                    result = engine.extract_structured_data(file_path)
                    results.append(result)
                except Exception as e:
                    print(f"  失败: {e}")
                    results.append({
                        'file': str(file_path),
                        'success': False,
                        'error': str(e)
                    })

        output_data = {
            'total_files': len(files),
            'processed': len(results),
            'results': results
        }
    else:
        print(f"ERROR: 路径不存在: {args.input}")
        sys.exit(1)

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")
    else:
        print(json.dumps(output_data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
