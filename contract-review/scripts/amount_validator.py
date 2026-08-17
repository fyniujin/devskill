#!/usr/bin/env python3
"""
amount_validator.py v5.1
关键金额校验引擎
功能：金额大小写一致性验证、勾稽关系自动验证、关键金额字段二次校验
v5.1 新增：关键金额字段二次校验（金额大小写一致性+勾稽关系自动验证）
"""

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 中文数字映射 ===
CN_NUMBERS = {
    '零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4,
    '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
    '〇': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
}

CN_UNITS = {
    '个': 1, '十': 10, '拾': 10, '百': 100, '佰': 100,
    '千': 1000, '仟': 1000, '万': 10000, '萬': 10000,
    '亿': 100000000, '億': 100000000,
}

# === 币种符号 ===
CURRENCY_SYMBOLS = {
    '¥': 'CNY', '￥': 'CNY', 'RMB': 'CNY', 'CNY': 'CNY', '元': 'CNY',
    '$': 'USD', 'USD': 'USD', '美元': 'USD',
    '€': 'EUR', 'EUR': 'EUR', '欧元': 'EUR',
    '£': 'GBP', 'GBP': 'GBP', '英镑': 'GBP',
    'JPY': 'JPY', '日元': 'JPY',
    'KRW': 'KRW', '₩': 'KRW', '韩元': 'KRW',
}

# === 金额字段名 ===
AMOUNT_FIELD_PATTERNS = [
    r'合同金额', r'总价', r'合计', r'小计', r'金额', r'价款',
    r'费用', r'报酬', r'租金', r'货款', r'工程款', r'服务费',
    r'违约金', r'赔偿金', r'保证金', r'定金', r'预付款',
    r'首付款', r'尾款', r'欠款', r'借款', r'贷款',
    r'单价', r'数量', r'总额', r'总计',
]


@dataclass
class AmountField:
    """金额字段"""
    name: str
    value: Decimal
    currency: str = 'CNY'
    raw_text: str = ''
    source: str = ''


@dataclass
class ValidationResult:
    """校验结果"""
    is_valid: bool
    field_name: str
    message: str
    severity: str = 'info'  # info, warning, error
    details: Dict[str, Any] = field(default_factory=dict)


class AmountValidator:
    """金额校验引擎 — 大小写一致性 + 勾稽关系"""

    def __init__(self):
        self._errors: List[ValidationResult] = []
        self._warnings: List[ValidationResult] = []

    # ========== 金额解析 ==========

    def parse_amount(self, text: str) -> Optional[Tuple[Decimal, str]]:
        """从文本中提取金额数值和币种"""
        if not text:
            return None
        text = str(text).strip()

        # 识别币种
        currency = self._detect_currency(text)

        # 提取数值
        value = self._extract_number(text)
        if value is None:
            return None

        return (value, currency)

    def _detect_currency(self, text: str) -> str:
        """检测币种"""
        text_upper = text.upper()
        # 优先匹配代码
        for code in ['CNY', 'USD', 'EUR', 'GBP', 'JPY', 'KRW', 'RMB']:
            if code in text_upper:
                return code if code != 'RMB' else 'CNY'
        # 匹配符号
        for sym, cur in CURRENCY_SYMBOLS.items():
            if sym in text:
                return cur
        return 'CNY'  # 默认人民币

    def _extract_number(self, text: str) -> Optional[Decimal]:
        """从文本中提取数值"""
        # 移除币种符号
        cleaned = text
        for sym in CURRENCY_SYMBOLS:
            cleaned = cleaned.replace(sym, '')
        cleaned = cleaned.strip()

        # 尝试直接解析阿拉伯数字
        num_pattern = r'[\d,]+(?:\.\d+)?|\d+(?:,\d+)*'
        matches = re.findall(num_pattern, cleaned)
        if matches:
            num_str = matches[0]
            if ',' in num_str:
                if '.' in num_str:
                    last_comma = num_str.rfind(',')
                    last_dot = num_str.rfind('.')
                    if last_comma < last_dot:
                        num_str = num_str.replace(',', '')
                    else:
                        num_str = num_str.replace('.', '').replace(',', '.')
                else:
                    parts = num_str.split(',')
                    if len(parts[-1]) == 3:
                        num_str = num_str.replace(',', '')
                    else:
                        num_str = num_str.replace(',', '.')
            try:
                return Decimal(num_str)
            except InvalidOperation:
                pass

        # 尝试解析中文大写金额
        cn_value = self._parse_chinese_amount(cleaned)
        if cn_value is not None:
            return cn_value

        return None

    def _parse_chinese_amount(self, text: str) -> Optional[Decimal]:
        """解析中文大写金额（如：壹拾贰万叁仟肆佰伍拾陆元柒角捌分）"""
        if not text:
            return None

        has_cn = any(c in CN_NUMBERS for c in text)
        if not has_cn:
            return None

        text = text.replace('整', '').replace('圆', '元')

        # 分离角分
        yuan_part = text
        jiao_digit = None
        fen_digit = None

        if '角' in text:
            idx = text.index('角')
            before_jiao = text[:idx]
            after_jiao = text[idx+1:]
            # 角金额是 before_jiao 的最后一位
            if before_jiao and before_jiao[-1] in CN_NUMBERS:
                jiao_digit = CN_NUMBERS[before_jiao[-1]]
                yuan_part = before_jiao[:-1]
            else:
                yuan_part = before_jiao
            # 分
            if '分' in after_jiao:
                idx_fen = after_jiao.index('分')
                before_fen = after_jiao[:idx_fen]
                if before_fen and before_fen[-1] in CN_NUMBERS:
                    fen_digit = CN_NUMBERS[before_fen[-1]]
        elif '分' in text:
            idx = text.index('分')
            before_fen = text[:idx]
            # 分金额是 before_fen 的最后一位
            if before_fen and before_fen[-1] in CN_NUMBERS:
                fen_digit = CN_NUMBERS[before_fen[-1]]
                yuan_part = before_fen[:-1]
            else:
                yuan_part = before_fen

        # 解析元部分
        yuan_value = self._parse_chinese_yuan(yuan_part)
        if yuan_value is None:
            return None

        result = yuan_value

        if jiao_digit is not None:
            result += Decimal(jiao_digit) / Decimal('10')

        if fen_digit is not None:
            result += Decimal(fen_digit) / Decimal('100')

        return result

    def _parse_chinese_yuan(self, text: str) -> Optional[Decimal]:
        """解析元部分的中文数字"""
        if not text:
            return Decimal('0')

        text = text.replace('元', '').replace('圆', '')

        if text.isdigit():
            return Decimal(text)

        total = Decimal('0')
        remaining = text

        if '亿' in remaining or '億' in remaining:
            parts = re.split(r'[亿億]', remaining)
            yi_part = parts[0]
            remaining = parts[1] if len(parts) > 1 else ''
            yi_value = self._parse_chinese_below_wan(yi_part)
            if yi_value is not None:
                total += yi_value * Decimal('100000000')

        if '万' in remaining or '萬' in remaining:
            parts = re.split(r'[万萬]', remaining)
            wan_part = parts[0]
            remaining = parts[1] if len(parts) > 1 else ''
            wan_value = self._parse_chinese_below_wan(wan_part)
            if wan_value is not None:
                total += wan_value * Decimal('10000')

        if remaining:
            below_value = self._parse_chinese_below_wan(remaining)
            if below_value is not None:
                total += below_value

        return total

    def _parse_chinese_below_wan(self, text: str) -> Optional[Decimal]:
        """解析万以下的中文数字"""
        if not text:
            return Decimal('0')

        result = Decimal('0')
        current = Decimal('0')

        for char in text:
            if char in CN_NUMBERS:
                current = Decimal(CN_NUMBERS[char])
            elif char in CN_UNITS:
                unit = CN_UNITS[char]
                if unit >= 10:
                    if current == 0:
                        current = Decimal('1')
                    result += current * Decimal(unit)
                    current = Decimal('0')

        result += current
        return result

    # ========== 大写金额转换 ==========

    def to_chinese_upper(self, amount: Decimal) -> str:
        """将阿拉伯数字金额转为中文大写"""
        if amount == 0:
            return '零元整'

        if amount < 0:
            return '负' + self.to_chinese_upper(-amount)

        amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        int_part = int(amount)
        frac_part = int((amount - int_part) * 100)

        int_str = self._int_to_chinese(int_part) + '元'

        jiao = frac_part // 10
        fen = frac_part % 10

        if jiao == 0 and fen == 0:
            frac_str = '整'
        elif jiao == 0:
            frac_str = '零' + self._digit_to_chinese(fen) + '分'
        elif fen == 0:
            frac_str = self._digit_to_chinese(jiao) + '角'
        else:
            frac_str = self._digit_to_chinese(jiao) + '角' + self._digit_to_chinese(fen) + '分'

        return int_str + frac_str

    def _int_to_chinese(self, n: int) -> str:
        """整数转中文大写"""
        if n == 0:
            return '零'

        # 按万、亿分节处理
        result = ''
        
        # 处理亿以上
        if n >= 100000000:
            yi_part = n // 100000000
            result += self._int_to_chinese_below_wan(yi_part) + '亿'
            n %= 100000000
            if n > 0 and n < 10000000:
                result += '零'
        
        # 处理万以上
        if n >= 10000:
            wan_part = n // 10000
            result += self._int_to_chinese_below_wan(wan_part) + '万'
            n %= 10000
            if n > 0 and n < 1000:
                result += '零'
        
        # 处理万以下
        if n > 0:
            result += self._int_to_chinese_below_wan(n)
        
        return result

    def _int_to_chinese_below_wan(self, n: int) -> str:
        """转换万以下的数字（0-9999）"""
        if n == 0:
            return '零'

        digits = '零壹贰叁肆伍陆柒捌玖'
        units = ['', '拾', '佰', '仟']

        result = ''
        n_str = str(n)
        length = len(n_str)

        for i, ch in enumerate(n_str):
            digit = int(ch)
            pos = length - i - 1

            if digit == 0:
                if result and not result.endswith('零'):
                    result += '零'
            else:
                result += digits[digit] + units[pos]

        return result.rstrip('零')

    def _digit_to_chinese(self, d: int) -> str:
        """单个数字转中文大写"""
        digits = '零壹贰叁肆伍陆柒捌玖'
        return digits[d] if 0 <= d <= 9 else ''

    # ========== 大小写一致性校验 ==========

    def validate_case_consistency(self, amount: Decimal, chinese_text: str) -> ValidationResult:
        """校验大小写金额是否一致"""
        parsed = self._parse_chinese_amount(chinese_text)
        if parsed is None:
            return ValidationResult(
                is_valid=False,
                field_name='金额',
                message='无法从中文文本中解析大写金额',
                severity='warning',
            )

        diff = abs(amount - parsed)
        if diff <= Decimal('0.01'):
            return ValidationResult(
                is_valid=True,
                field_name='金额',
                message=f'大小写金额一致（{amount} 元）',
                severity='info',
            )
        else:
            return ValidationResult(
                is_valid=False,
                field_name='金额',
                message=f'大小写金额不一致：阿拉伯数字 {amount} 元，中文大写对应 {parsed} 元，差额 {diff} 元',
                severity='error',
                details={'arabic': str(amount), 'chinese_parsed': str(parsed), 'diff': str(diff)},
            )

    # ========== 勾稽关系校验 ==========

    def validate_cross_reference(
        self,
        fields: Dict[str, Decimal],
        rules: List[Dict[str, Any]],
    ) -> List[ValidationResult]:
        """校验勾稽关系（如：单价 × 数量 = 总价）"""
        results = []

        for rule in rules:
            rule_name = rule.get('name', '未知规则')
            expression = rule.get('expression', '')
            tolerance = Decimal(str(rule.get('tolerance', '0.01')))

            try:
                result = self._safe_eval(expression, fields)
                if result is not None:
                    expected = Decimal(str(result))
                    actual_field = rule.get('actual_field', '')
                    actual = fields.get(actual_field, Decimal('0'))

                    diff = abs(expected - actual)
                    if diff <= tolerance:
                        results.append(ValidationResult(
                            is_valid=True,
                            field_name=rule_name,
                            message=f'勾稽关系校验通过：{expression} = {expected}，实际 {actual}',
                            severity='info',
                        ))
                    else:
                        results.append(ValidationResult(
                            is_valid=False,
                            field_name=rule_name,
                            message=f'勾稽关系不匹配：{expression} 计算值 {expected}，实际 {actual}，差额 {diff}',
                            severity='error',
                            details={'expected': str(expected), 'actual': str(actual), 'diff': str(diff)},
                        ))
            except Exception as e:
                results.append(ValidationResult(
                    is_valid=False,
                    field_name=rule_name,
                    message=f'勾稽关系校验异常：{e}',
                    severity='warning',
                ))

        return results

    def _safe_eval(self, expression: str, variables: Dict[str, Decimal]) -> Optional[float]:
        """安全求值简单数学表达式"""
        expr = expression
        for name, value in variables.items():
            expr = expr.replace(name, str(value))

        if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expr):
            return None

        try:
            result = eval(expr, {'__builtins__': {}}, {})
            return float(result)
        except Exception:
            return None

    # ========== 自动勾稽规则生成 ==========

    def auto_detect_cross_rules(self, fields: Dict[str, Decimal]) -> List[Dict[str, Any]]:
        """自动检测并生成勾稽关系规则"""
        rules = []

        patterns = [
            {
                'name': '单价×数量=总价',
                'required': ['单价', '数量', '总价'],
                'expression': '单价 * 数量',
                'actual_field': '总价',
            },
            {
                'name': '小计合计',
                'required': ['小计', '合计'],
                'expression': '小计',
                'actual_field': '合计',
            },
            {
                'name': '首付款+尾款=总价',
                'required': ['首付款', '尾款', '总价'],
                'expression': '首付款 + 尾款',
                'actual_field': '总价',
            },
            {
                'name': '本金+利息=还款总额',
                'required': ['本金', '利息', '还款总额'],
                'expression': '本金 + 利息',
                'actual_field': '还款总额',
            },
        ]

        field_names = set(fields.keys())
        for pattern in patterns:
            if all(req in field_names for req in pattern['required']):
                rules.append(pattern)

        return rules

    # ========== 综合校验入口 ==========

    def validate(
        self,
        fields: Dict[str, Tuple[Decimal, Optional[str]]],
        cross_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        综合校验入口
        :param fields: {字段名: (阿拉伯数字金额, 中文大写金额文本)}
        :param cross_rules: 勾稽关系规则列表
        :return: 校验结果汇总
        """
        self._errors = []
        self._warnings = []
        info_results = []

        pure_fields = {}
        for name, (amount, cn_text) in fields.items():
            pure_fields[name] = amount
            if cn_text:
                result = self.validate_case_consistency(amount, cn_text)
                if result.severity == 'error':
                    self._errors.append(result)
                elif result.severity == 'warning':
                    self._warnings.append(result)
                else:
                    info_results.append(result)

        if cross_rules is None:
            cross_rules = self.auto_detect_cross_rules(pure_fields)

        cross_results = self.validate_cross_reference(pure_fields, cross_rules)
        for r in cross_results:
            if r.severity == 'error':
                self._errors.append(r)
            elif r.severity == 'warning':
                self._warnings.append(r)
            else:
                info_results.append(r)

        total_checks = len(info_results) + len(self._warnings) + len(self._errors)
        passed = len(info_results)
        failed = len(self._errors)
        warned = len(self._warnings)

        return {
            'is_valid': len(self._errors) == 0,
            'total_checks': total_checks,
            'passed': passed,
            'failed': failed,
            'warnings': warned,
            'errors': [{'field': e.field_name, 'message': e.message} for e in self._errors],
            'warning_list': [{'field': w.field_name, 'message': w.message} for w in self._warnings],
            'info': [{'field': i.field_name, 'message': i.message} for i in info_results],
        }

    # ========== 从合同文本提取金额字段 ==========

    def extract_amount_fields(self, text: str) -> Dict[str, Decimal]:
        """从合同文本中提取金额字段"""
        fields = {}

        for pattern in AMOUNT_FIELD_PATTERNS:
            regex = rf'{pattern}[：:]\s*([¥￥$€£]?\s*[\d,]+(?:\.\d+)?|[零壹贰叁肆伍陆柒捌玖拾佰仟万亿元角分整]+元)'
            matches = re.finditer(regex, text)
            for m in matches:
                amount_text = m.group(1)
                parsed = self.parse_amount(amount_text)
                if parsed:
                    fields[pattern] = parsed[0]

        return fields


# ========== 便捷函数 ==========

_default_validator: Optional[AmountValidator] = None


def get_validator() -> AmountValidator:
    """获取全局单例"""
    global _default_validator
    if _default_validator is None:
        _default_validator = AmountValidator()
    return _default_validator


def validate_amounts(
    fields: Dict[str, Tuple[Decimal, Optional[str]]],
    cross_rules: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """便捷函数：校验金额"""
    return get_validator().validate(fields, cross_rules)


def to_chinese_upper(amount: Decimal) -> str:
    """便捷函数：金额转中文大写"""
    return get_validator().to_chinese_upper(amount)


if __name__ == "__main__":
    validator = AmountValidator()

    # 测试1：大小写一致性
    print("=== 测试1：大小写一致性 ===")
    result = validator.validate_case_consistency(
        Decimal('1234567.89'),
        '壹佰贰拾叁万肆仟伍佰陆拾柒元捌角玖分'
    )
    print(f"  结果: {result.message} (valid={result.is_valid})")

    # 测试2：不一致的情况
    result2 = validator.validate_case_consistency(
        Decimal('1000000'),
        '壹佰伍拾万元整'
    )
    print(f"  结果: {result2.message} (valid={result2.is_valid})")

    # 测试3：勾稽关系
    print("\n=== 测试2：勾稽关系 ===")
    fields = {
        '单价': (Decimal('100.00'), None),
        '数量': (Decimal('50'), None),
        '总价': (Decimal('5000.00'), None),
    }
    rules = [
        {'name': '单价×数量=总价', 'expression': '单价 * 数量', 'actual_field': '总价'},
    ]
    result3 = validator.validate(fields, rules)
    print(f"  校验结果: {'通过' if result3['is_valid'] else '失败'}")
    print(f"  通过: {result3['passed']}, 失败: {result3['failed']}")
    for e in result3['errors']:
        print(f"  错误: {e['message']}")

    # 测试4：勾稽关系不匹配
    print("\n=== 测试3：勾稽关系不匹配 ===")
    fields_bad = {
        '单价': (Decimal('100.00'), None),
        '数量': (Decimal('50'), None),
        '总价': (Decimal('5500.00'), None),
    }
    result4 = validator.validate(fields_bad, rules)
    print(f"  校验结果: {'通过' if result4['is_valid'] else '失败'}")
    for e in result4['errors']:
        print(f"  错误: {e['message']}")

    # 测试5：中文大写转换
    print("\n=== 测试4：中文大写转换 ===")
    print(f"  1234567.89 → {validator.to_chinese_upper(Decimal('1234567.89'))}")
    print(f"  1000000 → {validator.to_chinese_upper(Decimal('1000000'))}")
    print(f"  0 → {validator.to_chinese_upper(Decimal('0'))}")
    print(f"  15.5 → {validator.to_chinese_upper(Decimal('15.5'))}")
