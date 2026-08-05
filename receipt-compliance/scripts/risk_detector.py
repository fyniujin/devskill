#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
税务风险预警引擎
检测发票连号、大额整数、频繁开票、品名异常、进销项匹配等风险
输出三级预警：提示/关注/严重
"""

import re
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from unified_invoice import UnifiedInvoice, RECEIPT_TYPES


# === 风险检测默认配置 ===
DEFAULT_CONFIG = {
    "consecutive_number_threshold": 3,       # 连号检测阈值：同一供应商连续 N 张
    "round_amount_threshold": 10000,         # 大额整数阈值：金额 >= 此值且为整数
    "round_amount_min_digits": 5,            # 大额整数最少位数
    "frequent_invoicing_threshold": 10,      # 频繁开票阈值：N 天内开具 M 张
    "frequent_invoicing_days": 30,           # 频繁开票时间窗口（天）
    "scope_anomaly_enabled": True,           # 是否启用品名异常检测
    "input_output_match_enabled": True,      # 是否启用进销项匹配
}


# === 三级预警定义 ===
RISK_LEVELS = {
    "提示": {"priority": 1, "color": "green", "action": "建议关注"},
    "关注": {"priority": 2, "color": "orange", "action": "建议核实"},
    "严重": {"priority": 3, "color": "red", "action": "建议立即处理"},
}


class RiskDetector:
    """
    税务风险预警引擎
    
    检测方法：
    1. 连号检测：同一供应商连续开具多张连号发票
    2. 整数金额检测：大额整数金额（如 100000.00）
    3. 频繁开票检测：短时间内同一供应商开具大量发票
    4. 品名异常检测：品名与经营范围不符
    5. 进销项匹配检测：进项品名与销项品名不匹配
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.findings: List[Dict[str, Any]] = []
        self.invoices: List[UnifiedInvoice] = []
        self.input_invoices: List[UnifiedInvoice] = []
        self.output_invoices: List[UnifiedInvoice] = []
    
    def load_invoices(self, invoices: List[UnifiedInvoice]) -> 'RiskDetector':
        """加载进项发票列表"""
        self.invoices = invoices
        return self
    
    def load_input_invoices(self, invoices: List[UnifiedInvoice]) -> 'RiskDetector':
        """加载进项发票"""
        self.input_invoices = invoices
        return self
    
    def load_output_invoices(self, invoices: List[UnifiedInvoice]) -> 'RiskDetector':
        """加载销项发票"""
        self.output_invoices = invoices
        return self
    
    def detect_all(self) -> Dict[str, Any]:
        """
        运行所有风险检测
        
        Returns:
            dict: 包含所有检测结果和综合评估报告
        """
        self.findings = []
        
        # 1. 连号检测
        self._detect_consecutive_numbers()
        
        # 2. 整数金额检测
        self._detect_round_amounts()
        
        # 3. 频繁开票检测
        self._detect_frequent_invoicing()
        
        # 4. 品名异常检测
        self._detect_scope_anomaly()
        
        # 5. 进销项匹配检测
        self._detect_input_output_match()
        
        # 生成综合报告
        return self._generate_report()
    
    def _detect_consecutive_numbers(self):
        """连号检测：同一供应商连续开具多张连号发票"""
        # 按供应商分组
        supplier_invoices = defaultdict(list)
        for inv in self.invoices:
            if inv.seller_name:
                supplier_invoices[inv.seller_name].append(inv)
        
        threshold = self.config["consecutive_number_threshold"]
        
        for supplier, invs in supplier_invoices.items():
            # 按发票号码排序
            sorted_invs = sorted(invs, key=lambda x: x.invoice_number or "")
            
            # 检测连续号码
            consecutive_groups = []
            current_group = []
            
            for inv in sorted_invs:
                if not inv.invoice_number:
                    continue
                try:
                    num = int(inv.invoice_number)
                except (ValueError, TypeError):
                    continue
                
                if not current_group or num == int(current_group[-1].invoice_number or 0) + 1:
                    current_group.append(inv)
                else:
                    if len(current_group) >= threshold:
                        consecutive_groups.append(current_group)
                    current_group = [inv]
            
            if len(current_group) >= threshold:
                consecutive_groups.append(current_group)
            
            # 记录发现
            for group in consecutive_groups:
                numbers = [inv.invoice_number for inv in group]
                total_amount = sum(inv.total or 0 for inv in group)
                self.findings.append({
                    "type": "consecutive_numbers",
                    "level": "关注",
                    "supplier": supplier,
                    "description": f"检测到 {len(group)} 张连号发票：{numbers[0]} 至 {numbers[-1]}",
                    "details": {
                        "invoice_numbers": numbers,
                        "count": len(group),
                        "total_amount": total_amount,
                        "invoices": [inv.to_dict() for inv in group],
                    },
                    "suggestion": "建议核实是否存在拆分收入风险，确认业务真实性",
                })
    
    def _detect_round_amounts(self):
        """整数金额检测：大额整数金额"""
        threshold = self.config["round_amount_threshold"]
        min_digits = self.config["round_amount_min_digits"]
        
        for inv in self.invoices:
            if inv.total is None:
                continue
            
            # 检查是否为整数
            if inv.total != int(inv.total):
                continue
            
            # 检查是否达到阈值
            if inv.total >= threshold and len(str(int(inv.total))) >= min_digits:
                self.findings.append({
                    "type": "round_amount",
                    "level": "提示",
                    "invoice_number": inv.invoice_number,
                    "description": f"大额整数金额：{inv.total:.2f} 元",
                    "details": {
                        "amount": inv.total,
                        "invoice": inv.to_dict(),
                    },
                    "suggestion": "建议关注大额整数金额发票的业务真实性",
                })
    
    def _detect_frequent_invoicing(self):
        """频繁开票检测：短时间内同一供应商开具大量发票"""
        threshold = self.config["frequent_invoicing_threshold"]
        window_days = self.config["frequent_invoicing_days"]
        
        # 按供应商分组
        supplier_invoices = defaultdict(list)
        for inv in self.invoices:
            if inv.seller_name:
                supplier_invoices[inv.seller_name].append(inv)
        
        now = datetime.now()
        window_start = now - timedelta(days=window_days)
        
        for supplier, invs in supplier_invoices.items():
            # 筛选时间窗口内的发票
            recent_invs = []
            for inv in invs:
                try:
                    date_str = inv.billing_date or inv.travel_date
                    if date_str:
                        inv_date = datetime.strptime(date_str, '%Y-%m-%d')
                        if inv_date >= window_start:
                            recent_invs.append(inv)
                except (ValueError, TypeError):
                    continue
            
            if len(recent_invs) >= threshold:
                total_amount = sum(inv.total or 0 for inv in recent_invs)
                self.findings.append({
                    "type": "frequent_invoicing",
                    "level": "关注",
                    "supplier": supplier,
                    "description": f"近 {window_days} 天内开具 {len(recent_invs)} 张发票，合计 {total_amount:.2f} 元",
                    "details": {
                        "count": len(recent_invs),
                        "window_days": window_days,
                        "total_amount": total_amount,
                        "invoices": [inv.to_dict() for inv in recent_invs],
                    },
                    "suggestion": "建议核实是否存在虚开风险，确认业务真实性",
                })
    
    def _detect_scope_anomaly(self):
        """品名异常检测：品名与经营范围不符"""
        if not self.config.get("scope_anomaly_enabled"):
            return
        
        # 简化的行业关键词表（实际可扩展为完整数据库）
        SCOPE_KEYWORDS = {
            "餐饮": ["餐饮", "饭店", "酒楼", "餐厅", "食品", "小吃"],
            "技术服务": ["技术", "软件", "开发", "咨询", "顾问"],
            "建筑": ["建筑", "工程", "施工", "装修", "建材"],
            "零售": ["百货", "超市", "零售", "商店", "商贸"],
            "运输": ["运输", "物流", "快递", "货运", "客运"],
        }
        
        ANOMALY_RULES = [
            {"scope": "餐饮", "anomaly_keywords": ["技术服务", "软件开发", "建筑"]},
            {"scope": "建筑", "anomaly_keywords": ["餐饮", "零售百货"]},
            {"scope": "零售", "anomaly_keywords": ["建筑", "工程施工"]},
        ]
        
        for inv in self.invoices:
            if not inv.seller_name or not inv.raw_text:
                continue
            
            # 推断供应商行业
            supplier_scope = None
            for scope, keywords in SCOPE_KEYWORDS.items():
                if any(kw in (inv.seller_name or "") for kw in keywords):
                    supplier_scope = scope
                    break
            
            if not supplier_scope:
                continue
            
            # 检查品名是否异常
            for rule in ANOMALY_RULES:
                if rule["scope"] == supplier_scope:
                    for anomaly_kw in rule["anomaly_keywords"]:
                        if anomaly_kw in (inv.raw_text or ""):
                            self.findings.append({
                                "type": "scope_anomaly",
                                "level": "关注",
                                "seller_name": inv.seller_name,
                                "description": f"供应商「{supplier_scope}」行业开具「{anomaly_kw}」品名发票",
                                "details": {
                                    "supplier_scope": supplier_scope,
                                    "anomaly_keyword": anomaly_kw,
                                    "invoice": inv.to_dict(),
                                },
                                "suggestion": "建议核实品名与实际业务是否一致",
                            })
    
    def _detect_input_output_match(self):
        """进销项匹配检测：进项品名与销项品名是否匹配"""
        if not self.config.get("input_output_match_enabled"):
            return
        
        # 简化的品名关键词提取
        def extract_keywords(text: str) -> set:
            """从文本提取关键词"""
            if not text:
                return set()
            # 简单分词（实际可用 jieba 等分词库）
            words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
            return set(words)
        
        # 收集进项品名词汇
        input_keywords = set()
        for inv in self.input_invoices:
            input_keywords.update(extract_keywords(inv.raw_text))
        
        # 收集销项品名词汇
        output_keywords = set()
        for inv in self.output_invoices:
            output_keywords.update(extract_keywords(inv.raw_text))
        
        # 计算匹配度（简单 Jaccard 系数）
        if input_keywords and output_keywords:
            intersection = input_keywords & output_keywords
            union = input_keywords | output_keywords
            similarity = len(intersection) / len(union) if union else 0
            
            if similarity < 0.1:  # 匹配度低于 10%
                self.findings.append({
                    "type": "input_output_mismatch",
                    "level": "严重",
                    "description": f"进销项品名匹配度过低（{similarity:.1%}）",
                    "details": {
                        "input_keywords": list(input_keywords)[:20],
                        "output_keywords": list(output_keywords)[:20],
                        "similarity": similarity,
                    },
                    "suggestion": "建议重点核实进销项业务一致性，防范虚开风险",
                })
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成综合风险报告"""
        # 按预警级别分组
        findings_by_level = defaultdict(list)
        for finding in self.findings:
            findings_by_level[finding["level"]].append(finding)
        
        # 确定综合风险等级
        if findings_by_level.get("严重"):
            overall_level = "严重"
        elif findings_by_level.get("关注"):
            overall_level = "关注"
        elif findings_by_level.get("提示"):
            overall_level = "提示"
        else:
            overall_level = "无风险"
        
        return {
            "report_date": datetime.now().isoformat(),
            "total_invoices_checked": len(self.invoices),
            "total_findings": len(self.findings),
            "overall_risk_level": overall_level,
            "findings_by_level": {
                level: findings_by_level.get(level, [])
                for level in ["提示", "关注", "严重"]
            },
            "all_findings": self.findings,
            "config_used": self.config,
        }


def detect_risks(invoices: List[UnifiedInvoice], config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    便捷函数：检测发票风险
    
    Args:
        invoices: 发票列表
        config: 自定义检测配置（可选）
    
    Returns:
        dict: 风险检测报告
    """
    detector = RiskDetector(config)
    detector.load_invoices(invoices)
    return detector.detect_all()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python risk_detector.py <path_to_invoices_json>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        invoices = [UnifiedInvoice(**item) for item in data]
        report = detect_risks(invoices)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"检测失败: {e}", file=sys.stderr)
        sys.exit(1)
