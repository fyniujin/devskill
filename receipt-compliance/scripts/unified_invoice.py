#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一发票数据结构
兼容传统纸质/电子发票和全电发票（数电票）
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class UnifiedInvoice:
    """统一发票数据结构 - 兼容传统发票和全电发票"""
    
    # === 票种标识 ===
    invoice_type: str = "traditional"  # "traditional" | "full_electronic"
    
    # === 传统发票字段 ===
    invoice_code: Optional[str] = None        # 发票代码（10-12位，全电可能为空）
    invoice_number: Optional[str] = None      # 发票号码（传统8-20位；全电20位）
    
    # === 共有字段 ===
    billing_date: Optional[str] = None        # 开票日期
    amount: Optional[float] = None            # 不含税金额
    tax_amount: Optional[float] = None        # 税额
    total: Optional[float] = None             # 价税合计
    seller_name: Optional[str] = None         # 销售方名称
    seller_tax_id: Optional[str] = None       # 销售方税号
    buyer_name: Optional[str] = None          # 购买方名称
    buyer_tax_id: Optional[str] = None        # 购买方税号
    
    # === 全电发票特有字段 ===
    check_code: Optional[str] = None          # 校验码/二维码数据
    digital_account_id: Optional[str] = None  # 税务数字账户ID
    specific_business_info: Optional[str] = None  # 特定业务信息
    
    # === 附加元数据 ===
    confidence: Optional[float] = None        # 识别置信度（OCR用）
    raw_text: Optional[str] = None            # 原始文本/数据（调试用）
    source_format: Optional[str] = None       # 来源格式: pdf|png|xml|ofd
    extracted_at: Optional[str] = None        # 提取时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，便于JSON序列化"""
        result = asdict(self)
        # 添加计算字段
        if self.amount is not None and self.tax_amount is not None:
            result['calculated_total'] = round(self.amount + self.tax_amount, 2)
        return result
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def validate(self) -> List[str]:
        """返回验证错误列表，空列表表示通过"""
        errors = []
        if not self.invoice_number:
            errors.append("发票号码为空")
        if self.invoice_type == "traditional":
            if self.invoice_code and len(self.invoice_code) not in (10, 11, 12):
                errors.append(f"传统发票代码长度异常：{len(self.invoice_code)}")
        elif self.invoice_type == "full_electronic":
            # 全电发票号码20位
            if self.invoice_number and len(self.invoice_number) != 20:
                errors.append(f"全电发票号码长度异常：{len(self.invoice_number)}，应为20位")
        return errors
