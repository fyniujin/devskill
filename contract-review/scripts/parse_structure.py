#!/usr/bin/env python3
"""
合同结构解析模块
将原始文本解析为结构化合同要素
"""

import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Party:
    """合同主体"""
    role: str  # 甲方/乙方/丙方
    name: str = ""
    credit_code: str = ""  # 统一社会信用代码
    address: str = ""
    legal_representative: str = ""  # 法定代表人
    contact: str = ""


@dataclass
class Clause:
    """合同条款"""
    id: str
    title: str
    content: str
    page: Optional[int] = None
    clause_type: str = ""  # 条款类型：付款/交付/验收/违约/争议解决/保密/其他


@dataclass
class KeyTerm:
    """关键术语"""
    term: str
    value: str
    clause_ref: str = ""


@dataclass
class ContractStructure:
    """合同结构"""
    title: str = ""
    contract_type: str = ""
    parties: List[Party] = field(default_factory=list)
    total_amount: Optional[str] = None
    currency: str = "CNY"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    signing_date: Optional[str] = None
    signing_location: str = ""
    clauses: List[Clause] = field(default_factory=list)
    key_terms: List[KeyTerm] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'contract_type': self.contract_type,
            'parties': [asdict(p) for p in self.parties],
            'total_amount': self.total_amount,
            'currency': self.currency,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'signing_date': self.signing_date,
            'signing_location': self.signing_location,
            'clauses': [asdict(c) for c in self.clauses],
            'key_terms': [asdict(k) for k in self.key_terms],
        }


class ContractParser:
    """合同结构解析器"""
    
    # 合同类型关键词
    CONTRACT_TYPE_KEYWORDS = {
        '买卖合同': ['买卖', '采购', '供货', '销售', '订货', '供应'],
        '技术开发合同': ['技术开发', '软件开发', '系统开发', '委托开发', '合作开发'],
        '租赁合同': ['租赁', '租房', '出租', '承租', '商铺租赁', '厂房租赁'],
        '劳动合同': ['劳动', '聘用', '雇佣', '劳动合同', '劳务合同'],
        '借款合同': ['借款', '贷款', '借贷', '欠款', '还款'],
        '融资协议': ['融资', '投资', '增资', '股权融资', '股东协议', '投资协议'],
        '服务合同': ['服务', '咨询', '顾问', '代理', '中介'],
        '运输合同': ['运输', '物流', '货运', '托运', '承运'],
        '仓储合同': ['仓储', '保管', '储存', '仓库'],
        '委托合同': ['委托', '代办', '代理', '委托合同'],
    }
    
    # 条款类型关键词
    CLAUSE_TYPE_KEYWORDS = {
        '付款': ['付款', '支付', '价款', '金额', '费用', '报酬', '结算'],
        '交付': ['交付', '交货', '提交', '移交', '过户'],
        '验收': ['验收', '检验', '检测', '测试', '确认'],
        '违约': ['违约', '赔偿', '违约金', '罚款', '责任', '免责'],
        '争议解决': ['争议', '纠纷', '仲裁', '诉讼', '管辖', '法院'],
        '保密': ['保密', '秘密', '机密', '泄露', '披露'],
        '知识产权': ['知识产权', '专利', '商标', '著作权', '版权', '源代码'],
        '终止': ['终止', '解除', '撤销', '失效', '期满'],
        '不可抗力': ['不可抗力', '天灾', '战争', '政府行为'],
    }
    
    def __init__(self):
        pass
    
    def parse(self, text: str, pages: Optional[List[Dict]] = None) -> ContractStructure:
        """
        解析合同文本
        
        Args:
            text: 合同全文
            pages: 按页分割的文本列表
            
        Returns:
            ContractStructure 对象
        """
        structure = ContractStructure()
        
        # 1. 识别合同标题和类型
        structure.title = self._extract_title(text)
        structure.contract_type = self._detect_contract_type(text)
        
        # 2. 提取主体信息
        structure.parties = self._extract_parties(text)
        
        # 3. 提取金额信息
        structure.total_amount, structure.currency = self._extract_amount(text)
        
        # 4. 提取日期信息
        dates = self._extract_dates(text)
        structure.start_date = dates.get('start_date')
        structure.end_date = dates.get('end_date')
        structure.signing_date = dates.get('signing_date')
        structure.signing_location = self._extract_signing_location(text)
        
        # 5. 切分条款
        structure.clauses = self._split_clauses(text, pages)
        
        # 6. 提取关键术语
        structure.key_terms = self._extract_key_terms(text, structure.clauses)
        
        logger.info(f"解析完成: 标题={structure.title}, 类型={structure.contract_type}, "
                    f"主体数={len(structure.parties)}, 条款数={len(structure.clauses)}")
        
        return structure
    
    def _extract_title(self, text: str) -> str:
        """提取合同标题"""
        lines = text.strip().split('\n')
        
        # 通常标题在前几行
        for line in lines[:10]:
            line = line.strip()
            if not line:
                continue
            # 标题通常包含"合同"或"协议"
            if '合同' in line or '协议' in line:
                # 清理标题
                title = re.sub(r'^[\s\d\.\、\-\*]+', '', line).strip()
                if len(title) > 5:
                    return title
        
        # 如果没找到，返回第一行非空行
        for line in lines:
            line = line.strip()
            if line:
                return line[:50]
        
        return "未知合同"
    
    def _detect_contract_type(self, text: str) -> str:
        """自动检测合同类型"""
        text_lower = text.lower()
        
        scores = {}
        for contract_type, keywords in self.CONTRACT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[contract_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "其他"
    
    def _extract_parties(self, text: str) -> List[Party]:
        """提取甲乙双方信息"""
        parties = []
        
        # 匹配甲方/乙方/丙方
        party_patterns = [
            r'(甲方|乙方|丙方)[：:]([^\n]+)',
            r'(甲方|乙方|丙方)\s*[：:]\s*([^\n]+)',
            r'([^\n]+?)(以下简称["「]?(甲方|乙方|丙方)["」]?)',
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    role, name = match
                elif len(match) == 3:
                    name, role = match[0], match[1]
                else:
                    continue
                
                name = name.strip()
                role = role.strip()
                
                # 清理名称
                name = re.sub(r'[，,。.；;：:].*$', '', name).strip()
                
                if name and len(name) > 1:
                    # 检查是否已存在
                    existing = [p for p in parties if p.role == role]
                    if not existing:
                        parties.append(Party(role=role, name=name))
        
        # 提取统一社会信用代码
        credit_codes = re.findall(r'[0-9A-Z]{18}', text)
        if credit_codes and parties:
            for i, code in enumerate(credit_codes):
                if i < len(parties):
                    parties[i].credit_code = code
        
        return parties
    
    def _extract_amount(self, text: str) -> tuple:
        """提取合同金额"""
        # 匹配金额模式
        amount_patterns = [
            r'(?:总价|金额|价款|费用|报酬)[：:]\s*([¥￥]?\s*[\d,]+\.?\d*)\s*(元|人民币|美元|USD|CNY)?',
            r'([¥￥]\s*[\d,]+\.?\d*)\s*(元|人民币|美元|USD|CNY)?',
            r'(?:人民币|¥|￥)\s*([\d,]+\.?\d*)\s*(元)?',
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                amount = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
                currency = matches[0][1] if isinstance(matches[0], tuple) and len(matches[0]) > 1 else '元'
                
                # 标准化货币
                currency_map = {'元': 'CNY', '人民币': 'CNY', '美元': 'USD', 'USD': 'USD', 'CNY': 'CNY'}
                currency = currency_map.get(currency, 'CNY')
                
                return amount, currency
        
        return None, 'CNY'
    
    def _extract_dates(self, text: str) -> Dict[str, str]:
        """提取日期信息"""
        dates = {}
        
        # 匹配日期模式
        date_patterns = [
            r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        ]
        
        all_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    date_str = f"{match[0]}-{match[1].zfill(2)}-{match[2].zfill(2)}"
                else:
                    date_str = match
                all_dates.append(date_str)
        
        # 分类日期
        date_keywords = {
            'start_date': ['起始', '开始', '生效', '签订', '签署'],
            'end_date': ['终止', '结束', '期满', '到期', '截止'],
            'signing_date': ['签订', '签署', '订立'],
        }
        
        for date_str in all_dates:
            # 查找日期附近的关键词
            # 尝试在原文中定位日期
            date_variants = [
                date_str,
                date_str.replace('-', '年', 1).replace('-', '月') + '日',
                date_str.replace('-', '.', 1).replace('-', '.'),
            ]
            
            date_pos = -1
            for variant in date_variants:
                date_pos = text.find(variant)
                if date_pos >= 0:
                    break
            
            if date_pos >= 0:
                context = text[max(0, date_pos-50):date_pos+50]
                
                for date_type, keywords in date_keywords.items():
                    if any(kw in context for kw in keywords):
                        dates[date_type] = date_str
                        break
        
        # 如果没有分类，按顺序分配
        if not dates and all_dates:
            dates['signing_date'] = all_dates[0]
            if len(all_dates) > 1:
                dates['start_date'] = all_dates[0]
                dates['end_date'] = all_dates[-1]
        
        return dates
    
    def _extract_signing_location(self, text: str) -> str:
        """提取签订地点"""
        patterns = [
            r'签订地点[：:]([^\n]+)',
            r'签订地[：:]([^\n]+)',
            r'合同签订地[：:]([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _split_clauses(self, text: str, pages: Optional[List[Dict]] = None) -> List[Clause]:
        """切分合同条款"""
        clauses = []
        
        # 匹配条款编号模式
        clause_patterns = [
            r'(第[一二三四五六七八九十百千]+条[\s\d\.\、\-\*]*[^\n]*)',
            r'(\d+[\.\、][^\n]+)',
            r'(\([一二三四五六七八九十]+\)[^\n]+)',
        ]
        
        # 尝试按"第X条"切分
        matches = re.findall(r'第[一二三四五六七八九十百千]+条', text)
        
        if len(matches) >= 2:
            # 按"第X条"切分
            parts = re.split(r'(第[一二三四五六七八九十百千]+条)', text)
            
            current_title = ""
            current_content = ""
            clause_id = 0
            
            for i, part in enumerate(parts):
                if re.match(r'第[一二三四五六七八九十百千]+条', part):
                    # 保存上一个条款
                    if current_title and current_content:
                        clause_id += 1
                        clauses.append(Clause(
                            id=f"clause_{clause_id:03d}",
                            title=current_title,
                            content=current_content.strip(),
                            clause_type=self._detect_clause_type(current_content),
                        ))
                    current_title = part
                    current_content = ""
                else:
                    current_content += part
            
            # 保存最后一个条款
            if current_title and current_content:
                clause_id += 1
                clauses.append(Clause(
                    id=f"clause_{clause_id:03d}",
                    title=current_title,
                    content=current_content.strip(),
                    clause_type=self._detect_clause_type(current_content),
                ))
        
        # 如果没有切分出条款，按段落切分
        if not clauses:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            for i, para in enumerate(paragraphs):
                clauses.append(Clause(
                    id=f"clause_{i+1:03d}",
                    title=f"第{i+1}段",
                    content=para,
                    clause_type=self._detect_clause_type(para),
                ))
        
        return clauses
    
    def _detect_clause_type(self, text: str) -> str:
        """检测条款类型"""
        text_lower = text.lower()
        
        scores = {}
        for clause_type, keywords in self.CLAUSE_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[clause_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "其他"
    
    def _extract_key_terms(self, text: str, clauses: List[Clause]) -> List[KeyTerm]:
        """提取关键术语"""
        key_terms = []
        
        # 定义要提取的关键术语
        term_patterns = {
            '违约金': r'违约金[：:]([^\n]+)',
            '质保金': r'质保金[：:]([^\n]+)',
            '交付标准': r'交付标准[：:]([^\n]+)',
            '验收标准': r'验收标准[：:]([^\n]+)',
            '付款节点': r'付款[：:]([^\n]+)',
            '保修期': r'保修期[：:]([^\n]+)',
            '竞业限制': r'竞业限制[：:]([^\n]+)',
            '保密期限': r'保密[：:]([^\n]+)',
        }
        
        for term, pattern in term_patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                # 找到对应的条款
                clause_ref = ""
                for clause in clauses:
                    if term in clause.content:
                        clause_ref = clause.id
                        break
                
                key_terms.append(KeyTerm(term=term, value=value, clause_ref=clause_ref))
        
        return key_terms


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python parse_structure.py <文本文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    parser = ContractParser()
    structure = parser.parse(text)
    
    print(json.dumps(structure.to_dict(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
