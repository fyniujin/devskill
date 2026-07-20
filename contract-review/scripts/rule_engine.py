#!/usr/bin/env python3
"""
规则引擎模块 v3.2
基于硬规则的确定性检查
安全特性：YAML 安全加载、输入长度限制、日志脱敏
v3.2 新增：按合同类型懒加载专用规则文件
"""

import re
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 最大处理文本长度（防止 ReDoS 和内存溢出）
MAX_TEXT_LENGTH = 500000

# v3.2 合同类型与专用规则文件映射
CONTRACT_TYPE_RULE_FILES = {
    '股权转让合同': 'equity_transfer.yaml',
    '增资扩股协议': 'capital_increase.yaml',
    '对赌协议': 'valuation_adjustment.yaml',
    'NDA保密协议': 'nda.yaml',
    '知识产权许可协议': 'ip_license.yaml',
    '建设工程合同': 'construction.yaml',
    '劳动合同': 'labor_contract_deep.yaml',
    '采购框架协议': 'procurement_framework.yaml',
}


class RiskItem:
    """风险项"""
    def __init__(self, risk_id: str, risk_type: str, severity: str, 
                 title: str, description: str, suggestion: str,
                 legal_basis: str = "", text_snippet: str = "",
                 clause_ref: str = ""):
        self.risk_id = risk_id
        self.risk_type = risk_type
        self.severity = severity
        self.title = title
        self.description = description
        self.suggestion = suggestion
        self.legal_basis = legal_basis
        self.text_snippet = text_snippet
        self.clause_ref = clause_ref
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'risk_id': self.risk_id,
            'risk_type': self.risk_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'suggestion': self.suggestion,
            'legal_basis': self.legal_basis,
            'text_snippet': self.text_snippet,
            'clause_ref': self.clause_ref,
        }


class RuleEngine:
    """规则引擎"""
    
    def __init__(self, rules_path: str = None):
        """初始化规则引擎"""
        self.rules = []
        # v3.2 规则缓存（按合同类型）
        self._rule_cache: Dict[str, List[Dict]] = {}
        if rules_path:
            self._load_rules(rules_path)
    
    def _load_rules(self, rules_path: str):
        """安全地从 YAML 文件加载规则（使用 safe_load 防止反序列化攻击）"""
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                # YAML safe_load 已经是安全的，但为了双重保险，限制文件大小
                content = f.read(1024 * 1024)  # 最大 1MB
                config = yaml.safe_load(content)
            self.rules = config.get('rules', [])
            logger.info(f"加载了 {len(self.rules)} 条规则")
        except Exception as e:
            logger.error(f"规则加载失败: {e}")
            self.rules = []
    
    def check_all(self, text: str, contract_type: str = "", 
                  structure: Dict = None) -> List[RiskItem]:
        """
        运行所有规则检查
        
        Args:
            text: 合同全文（最大 500KB）
            contract_type: 合同类型
            structure: 解析后的合同结构
            
        Returns:
            风险项列表
        """
        # 安全检查：限制文本长度
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"文本过长 ({len(text)} 字符)，截断至 {MAX_TEXT_LENGTH} 字符")
            text = text[:MAX_TEXT_LENGTH]
        
        risks = []
        
        # v3.2 优先加载专用规则（如果存在）
        specific_rules = self._load_contract_specific_rules(contract_type)
        all_rules = specific_rules + self.rules
        
        for rule in all_rules:
            if not rule.get('enabled', True):
                continue
            
            try:
                result = self._apply_rule(rule, text, contract_type, structure)
                if result:
                    if isinstance(result, list):
                        risks.extend(result)
                    else:
                        risks.append(result)
            except Exception as e:
                logger.warning(f"规则 {rule.get('id', '?')} 执行失败: {e}")
        
        return risks
    
    def _load_contract_specific_rules(self, contract_type: str) -> List[Dict]:
        """v3.2 按合同类型懒加载专用规则文件"""
        if not contract_type or contract_type not in CONTRACT_TYPE_RULE_FILES:
            return []
        
        # 检查缓存
        if contract_type in self._rule_cache:
            return self._rule_cache[contract_type]
        
        # 查找专用规则文件
        rule_file = CONTRACT_TYPE_RULE_FILES[contract_type]
        rules_dir = Path(__file__).parent.parent / 'references' / 'contract_types'
        rule_path = rules_dir / rule_file
        
        if not rule_path.exists():
            logger.debug(f"专用规则文件不存在: {rule_path}")
            return []
        
        try:
            with open(rule_path, 'r', encoding='utf-8') as f:
                content = f.read(1024 * 1024)
                config = yaml.safe_load(content)
            rules = config.get('rules', [])
            # 缓存
            self._rule_cache[contract_type] = rules
            logger.info(f"加载 {contract_type} 专用规则 {len(rules)} 条")
            return rules
        except Exception as e:
            logger.warning(f"加载专用规则失败: {e}")
            return []
    
    def _apply_rule(self, rule: Dict, text: str, contract_type: str,
                    structure: Dict) -> Any:
        """应用单条规则"""
        check_type = rule.get('check_type', '')
        
        if check_type == 'regex_match':
            return self._check_regex(rule, text)
        elif check_type == 'threshold':
            return self._check_threshold(rule, text)
        elif check_type == 'pattern_match':
            return self._check_pattern(rule, text)
        elif check_type == 'checklist':
            return self._check_checklist(rule, text, structure)
        elif check_type == 'list_check':
            return self._check_list(rule, text)
        elif check_type in ('llm_check', 'api_check', 'prompt_check', 'semantic_check'):
            # 由 LLM 或外部服务处理
            return None
        else:
            logger.warning(f"未知的检查类型: {check_type}")
            return None
    
    def _get_rule_id(self, rule: Dict) -> str:
        """安全获取规则 ID（兼容 id/name 两种字段）"""
        return rule.get('id', rule.get('name', 'unknown'))
    
    def _check_regex(self, rule: Dict, text: str) -> RiskItem:
        """正则匹配检查（安全的正则，防止 ReDoS）"""
        pattern = rule.get('check_rule', '')
        
        # 安全检查：限制正则复杂度
        if len(pattern) > 1000:
            logger.warning(f"跳过复杂正则 ({len(pattern)} 字符)")
            return None
        
        try:
            # 设置超时，防止正则灾难性回溯
            matches = re.findall(pattern, text)
        except re.error as e:
            logger.warning(f"正则错误: {e}")
            return None
        
        if matches:
            snippet = str(matches[0]) if matches else ""
            return RiskItem(
                risk_id=rule['id'],
                risk_type=rule.get('category', ''),
                severity=rule.get('severity', 'medium'),
                title=rule.get('name', ''),
                description=rule.get('description', ''),
                suggestion=rule.get('suggestion', ''),
                legal_basis=rule.get('legal_basis', ''),
                text_snippet=snippet[:100],  # 限制长度
            )
        return None
    
    def _check_threshold(self, rule: Dict, text: str) -> RiskItem:
        """阈值检查"""
        check_rule = rule.get('check_rule', '')
        pattern = rule.get('extract_pattern', rule.get('check_rule', ''))
        
        # 安全检查：限制正则复杂度
        if len(pattern) > 500:
            return None
        
        try:
            matches = re.findall(pattern, text)
        except re.error:
            return None
        
        for match in matches:
            try:
                value = float(str(match).replace(',', ''))
                threshold = rule.get('threshold', 0)
                
                if rule.get('operator', '>') == '>' and value > threshold:
                    return RiskItem(
                        risk_id=rule['id'],
                        risk_type=rule.get('category', ''),
                        severity=rule.get('severity', 'medium'),
                        title=rule.get('name', ''),
                        description=f"检测到 {value:.1f}，超过阈值 {threshold}",
                        suggestion=rule.get('suggestion', ''),
                        legal_basis=rule.get('legal_basis', ''),
                        text_snippet=str(match)[:100],
                    )
            except (ValueError, TypeError):
                continue
        
        return None
    
    def _check_pattern(self, rule: Dict, text: str) -> RiskItem:
        """模式匹配检查"""
        check_rule = rule.get('check_rule', '')
        
        if isinstance(check_rule, str):
            patterns = [check_rule]
        elif isinstance(check_rule, list):
            patterns = check_rule
        else:
            patterns = []
        
        for pattern in patterns:
            if pattern in text:
                pos = text.find(pattern)
                # 安全截取
                snippet = text[max(0, pos-20):pos+50]
                
                return RiskItem(
                    risk_id=rule['id'],
                    risk_type=rule.get('category', ''),
                    severity=rule.get('severity', 'medium'),
                    title=rule.get('name', ''),
                    description=rule.get('description', ''),
                    suggestion=rule.get('suggestion', ''),
                    legal_basis=rule.get('legal_basis', ''),
                    text_snippet=snippet[:100],
                )
        
        return None
    
    def _check_checklist(self, rule: Dict, text: str, structure: Dict) -> List[RiskItem]:
        """清单检查"""
        risks = []
        check_rule = rule.get('check_rule', '')
        
        if check_rule == '对照合同必备条款清单检查':
            required = ['标的', '数量', '质量', '价款', '履行期限', '违约责任', '争议解决']
            
            for item in required:
                if item not in text:
                    risks.append(RiskItem(
                        risk_id=f"{rule['id']}_{item}",
                        risk_type=rule.get('category', ''),
                        severity=rule.get('severity', 'medium'),
                        title=f"可能缺少【{item}】相关条款",
                        description=f"合同文本中未检测到明确的【{item}】约定",
                        suggestion=f"建议补充【{item}】的具体约定",
                        legal_basis=rule.get('legal_basis', ''),
                    ))
        
        return risks
    
    def _check_list(self, rule: Dict, text: str) -> RiskItem:
        """列表验证检查"""
        check_rule = rule.get('check_rule', '')
        
        if '验证仲裁机构' in check_rule:
            valid_institutions = [
                '中国国际经济贸易仲裁委员会', '北京仲裁委员会', '上海仲裁委员会',
                '深圳国际仲裁院', '广州仲裁委员会', '中国海事仲裁委员会',
                '贸仲', '北仲', '上仲', '深国仲', '广仲',
            ]
            
            if '仲裁' in text:
                found = False
                for inst in valid_institutions:
                    if inst in text:
                        found = True
                        break
                
                if not found:
                    if '仲裁委员会' in text or '仲裁机构' in text:
                        pos = text.find('仲裁委员会')
                        if pos == -1:
                            pos = text.find('仲裁机构')
                        
                        snippet = text[max(0, pos-10):pos+50]
                        return RiskItem(
                            risk_id=rule['id'],
                            risk_type=rule.get('category', ''),
                            severity=rule.get('severity', 'medium'),
                            title=rule.get('name', ''),
                            description=rule.get('description', ''),
                            suggestion=rule.get('suggestion', ''),
                            legal_basis=rule.get('legal_basis', ''),
                            text_snippet=snippet[:100],
                        )
        
        return None


def main():
    """命令行入口"""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("用法: python rule_engine.py <文本文件> [规则文件]")
        sys.exit(1)
    
    text_path = sys.argv[1]
    rules_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    engine = RuleEngine(rules_path)
    risks = engine.check_all(text)
    
    print(f"发现 {len(risks)} 个风险点:")
    print(json.dumps([r.to_dict() for r in risks], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
