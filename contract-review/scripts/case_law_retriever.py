#!/usr/bin/env python3
"""
case_law_retriever.py v5.2
类案要点库与判决倾向参考引擎
功能：内置公开指导案例与司法解释要点库、按争议条款类型输出法院倾向摘要、支持用户导入自整理类案 JSON
v5.2 新增：类案要点库
数据说明：静态公开案例库，非实时判例；数据截止 2026 年 7 月
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references" / "guiding_cases"
CASE_LAW_DB_FILE = REFERENCES_DIR / "case_law_db.json"
USER_CASE_DIR = Path.home() / ".contract-review" / "user_cases"

# === 风险类型 → 争议条款类型映射 ===
RISK_TO_DISPUTE_TYPE = {
    "违约责任": "违约责任",
    "违约金": "违约金",
    "合同解除": "合同解除",
    "合同无效": "合同效力",
    "合同效力": "合同效力",
    "格式条款": "格式条款",
    "免责条款": "免责条款",
    "质量": "质量标准",
    "交付": "交付义务",
    "付款": "付款义务",
    "价款": "价款支付",
    "利息": "利息利率",
    "担保": "担保责任",
    "保证": "保证责任",
    "抵押": "担保责任",
    "股权": "股权转让",
    "知识产权": "知识产权",
    "保密": "保密义务",
    "竞业": "竞业限制",
    "争议解决": "争议解决",
    "管辖": "管辖",
    "仲裁": "争议解决",
    "诉讼": "争议解决",
    "侵权": "侵权责任",
    "赔偿": "损害赔偿",
    "退货": "退货义务",
    "验收": "验收标准",
    "风险": "风险负担",
    "解除": "合同解除",
    "终止": "合同终止",
    "保理": "保理合同",
    "融资租赁": "融资租赁",
    "建设工程": "建设工程",
    "劳动": "劳动合同",
    "个人信息": "个人信息",
    "隐私": "个人信息",
    "消费者": "消费者保护",
    "垄断": "垄断协议",
    "环境": "环境侵权",
}

# 争议条款类型 → 法院倾向摘要模板
COURT_TENDENCY_TEMPLATES = {
    "违约责任": {
        "tendency": "法院倾向于根据实际损失调整违约金，超过实际损失 30% 的可认定为过高",
        "key_factors": ["实际损失大小", "违约方过错程度", "合同履行情况", "当事人举证能力"],
        "typical_outcome": "违约金调整至实际损失的 1.3 倍以内",
    },
    "违约金": {
        "tendency": "法院对违约金调整持审慎态度，仅在明显过高或过低时予以调整",
        "key_factors": ["实际损失", "合同总金额", "违约情节", "当事人地位"],
        "typical_outcome": "超过实际损失 30% 的部分一般不予支持",
    },
    "合同解除": {
        "tendency": "法院对合同解除条件把握严格，约定解除条件成就时需及时行使解除权",
        "key_factors": ["解除条件是否成就", "解除权行使是否及时", "合同履行程度", "恢复原状可能性"],
        "typical_outcome": "解除条件成就且及时行使的，支持解除；怠于行使的可能驳回",
    },
    "合同效力": {
        "tendency": "法院对合同无效认定持谨慎态度，尽量维持合同效力",
        "key_factors": ["违反法律强制性规定", "损害社会公共利益", "恶意串通", "虚假意思表示"],
        "typical_outcome": "仅在违反效力性强制性规定时认定无效",
    },
    "格式条款": {
        "tendency": "法院对格式条款效力审查严格，未合理提示说明的免责条款无效",
        "key_factors": ["提示说明义务履行", "条款公平性", "对方注意程度", "行业惯例"],
        "typical_outcome": "未合理提示的免责条款对相对方不发生效力",
    },
    "担保责任": {
        "tendency": "公司对外担保需审查决议程序，债权人未审查的不构成善意",
        "key_factors": ["决议程序完备性", "债权人是否善意", "担保金额合理性", "公司章程规定"],
        "typical_outcome": "未经决议的担保对公司不发生效力",
    },
    "知识产权": {
        "tendency": "委托开发技术成果归属约定不明的，归开发方所有",
        "key_factors": ["合同约定", "技术成果性质", "双方贡献程度", "行业惯例"],
        "typical_outcome": "未明确约定的，申请专利的权利属于研究开发人",
    },
    "竞业限制": {
        "tendency": "未支付补偿金的劳动者可解除竞业限制义务",
        "key_factors": ["补偿金支付情况", "违约金合理性", "竞业范围", "期限长短"],
        "typical_outcome": "未支付补偿金的，劳动者可解除竞业限制约定",
    },
    "保证责任": {
        "tendency": "保证期间约定不明的为主债务履行期届满后六个月",
        "key_factors": ["保证期间约定", "主债务履行期", "债权人主张时间", "保证方式"],
        "typical_outcome": "约定不明的，保证期间为六个月",
    },
    "消费者保护": {
        "tendency": "网络购物管辖协议未合理提示消费者的，对消费者不发生效力",
        "key_factors": ["提示说明程度", "消费者注意能力", "条款公平性", "行业惯例"],
        "typical_outcome": "未合理提示的管辖条款无效，消费者可选择被告住所地起诉",
    },
}


class CaseLawRetriever:
    """
    类案要点库检索引擎
    
    数据来源：
    - 内置公开指导案例库（case_law_db.json）
    - 用户自整理案例（~/.contract-review/user_cases/*.json）
    """

    def __init__(self, db_file: Optional[Path] = None):
        self.db_file = db_file or CASE_LAW_DB_FILE
        self._cases: List[Dict[str, Any]] = []
        self._index: Dict[str, List[str]] = {}  # keyword -> case_ids
        self._dispute_index: Dict[str, List[str]] = {}  # dispute_type -> case_ids
        self._loaded = False

    # ================================================================
    # 数据加载
    # ================================================================

    def _load_data(self):
        """加载案例数据"""
        if self._loaded:
            return
        
        # 加载内置案例库
        if self.db_file.exists():
            try:
                with open(self.db_file, encoding='utf-8') as f:
                    data = json.load(f)
                self._cases = data.get("cases", [])
                self._build_index()
                logger.info(f"内置案例库加载完成: {len(self._cases)} 条")
            except Exception as e:
                logger.warning(f"加载内置案例库失败: {e}")
                self._cases = []
        
        # 加载用户自整理案例
        self._load_user_cases()
        
        self._loaded = True

    def _build_index(self):
        """构建索引"""
        self._index = defaultdict(list)
        self._dispute_index = defaultdict(list)
        
        for case in self._cases:
            case_id = case.get("id", "")
            if not case_id:
                continue
            
            # 关键词索引
            keywords = case.get("keywords", [])
            for kw in keywords:
                self._index[kw].append(case_id)
            
            # 标题分词索引
            title = case.get("title", "")
            for char in title:
                if '\u4e00' <= char <= '\u9fff':
                    self._index[char].append(case_id)
            
            # 争议条款类型索引
            dispute_clause = case.get("dispute_clause", "")
            if dispute_clause:
                self._dispute_index[dispute_clause].append(case_id)
            
            # 风险标签索引
            risk_tags = case.get("risk_tags", [])
            for tag in risk_tags:
                self._index[tag].append(case_id)

    def _load_user_cases(self):
        """加载用户自整理案例"""
        if not USER_CASE_DIR.exists():
            return
        
        user_count = 0
        for json_file in USER_CASE_DIR.glob("*.json"):
            try:
                with open(json_file, encoding='utf-8') as f:
                    data = json.load(f)
                
                # 支持两种格式：单条案例或案例列表
                if isinstance(data, list):
                    for case in data:
                        case["_source"] = f"user:{json_file.name}"
                        self._cases.append(case)
                        user_count += 1
                elif isinstance(data, dict):
                    data["_source"] = f"user:{json_file.name}"
                    self._cases.append(data)
                    user_count += 1
            except Exception as e:
                logger.warning(f"加载用户案例失败 {json_file}: {e}")
        
        if user_count > 0:
            logger.info(f"用户自整理案例加载完成: {user_count} 条")
            # 重建索引
            self._build_index()

    # ================================================================
    # 核心检索接口
    # ================================================================

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        关键词搜索案例
        
        Args:
            query: 搜索关键词
            max_results: 最大返回条数
        
        Returns:
            匹配的案例列表
        """
        self._load_data()
        
        if not self._cases:
            return []
        
        # 分词
        query_terms = self._tokenize(query)
        
        # 打分
        scores: Dict[str, float] = defaultdict(float)
        for term in query_terms:
            for case_id in self._index.get(term, []):
                scores[case_id] += 1.0
        
        # 排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # 组装结果
        results = []
        for case_id in sorted_ids[:max_results]:
            case = self._get_case_by_id(case_id)
            if case:
                case["_score"] = scores[case_id]
                results.append(case)
        
        return results

    def search_by_dispute_type(self, dispute_type: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        按争议条款类型搜索
        
        Args:
            dispute_type: 争议条款类型（如"违约责任"、"合同解除"）
            max_results: 最大返回条数
        
        Returns:
            匹配的案例列表
        """
        self._load_data()
        
        results = []
        for case in self._cases:
            case_dispute = case.get("dispute_clause", "")
            if dispute_type in case_dispute or case_dispute in dispute_type:
                results.append(case)
            elif any(dispute_type in tag for tag in case.get("risk_tags", [])):
                results.append(case)
        
        return results[:max_results]

    def search_by_risk_type(self, risk_type: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        按风险类型搜索相关案例
        
        Args:
            risk_type: 风险类型（如"违约金风险"、"合同解除风险"）
            max_results: 最大返回条数
        
        Returns:
            匹配的案例列表
        """
        self._load_data()
        
        # 映射到争议条款类型
        dispute_type = RISK_TO_DISPUTE_TYPE.get(risk_type, risk_type)
        
        results = []
        for case in self._cases:
            # 匹配争议条款类型
            case_dispute = case.get("dispute_clause", "")
            if dispute_type in case_dispute or case_dispute in dispute_type:
                results.append(case)
                continue
            
            # 匹配风险标签
            risk_tags = case.get("risk_tags", [])
            if any(risk_type in tag or tag in risk_type for tag in risk_tags):
                results.append(case)
                continue
            
            # 匹配关键词
            keywords = case.get("keywords", [])
            if any(dispute_type in kw or kw in dispute_type for kw in keywords):
                results.append(case)
        
        return results[:max_results]

    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取案例"""
        self._load_data()
        return self._get_case_by_id(case_id)

    def _get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """内部方法：根据 ID 获取案例"""
        for case in self._cases:
            if case.get("id") == case_id:
                return case
        return None

    # ================================================================
    # 判决倾向分析
    # ================================================================

    def get_court_tendency(self, dispute_type: str) -> Dict[str, Any]:
        """
        获取某类争议条款的法院倾向
        
        Args:
            dispute_type: 争议条款类型
        
        Returns:
            法院倾向分析结果
        """
        self._load_data()
        
        # 查找模板
        template = COURT_TENDENCY_TEMPLATES.get(dispute_type)
        
        # 查找相关案例
        related_cases = self.search_by_dispute_type(dispute_type, max_results=3)
        
        result = {
            "dispute_type": dispute_type,
            "tendency": template["tendency"] if template else "暂无明确倾向数据",
            "key_factors": template["key_factors"] if template else [],
            "typical_outcome": template["typical_outcome"] if template else "视具体案情而定",
            "related_cases": [
                {
                    "id": c.get("id"),
                    "case_no": c.get("case_no"),
                    "title": c.get("title"),
                    "holding": c.get("holding"),
                }
                for c in related_cases
            ],
            "total_related": len(related_cases),
        }
        
        return result

    def analyze_risk_tendency(self, risk_type: str) -> Dict[str, Any]:
        """
        分析某类风险的判决倾向
        
        Args:
            risk_type: 风险类型
        
        Returns:
            判决倾向分析结果
        """
        # 映射到争议条款类型
        dispute_type = RISK_TO_DISPUTE_TYPE.get(risk_type, risk_type)
        
        # 获取法院倾向
        tendency = self.get_court_tendency(dispute_type)
        
        # 补充风险类型信息
        tendency["risk_type"] = risk_type
        tendency["mapped_dispute_type"] = dispute_type
        
        return tendency

    def enrich_risks_with_tendency(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为风险点列表补充判决倾向参考
        
        Args:
            risks: 风险点列表
        
        Returns:
            补充判决倾向后的风险点列表
        """
        self._load_data()
        
        enriched = []
        for risk in risks:
            risk = dict(risk)
            risk_type = risk.get("risk_type", "")
            
            if risk_type:
                # 查找相关案例
                related = self.search_by_risk_type(risk_type, max_results=2)
                if related:
                    risk["case_references"] = [
                        {
                            "case_no": c.get("case_no"),
                            "title": c.get("title"),
                            "holding": c.get("holding"),
                        }
                        for c in related
                    ]
                    
                    # 添加法院倾向
                    dispute_type = RISK_TO_DISPUTE_TYPE.get(risk_type, risk_type)
                    template = COURT_TENDENCY_TEMPLATES.get(dispute_type)
                    if template:
                        risk["court_tendency"] = template["tendency"]
            
            enriched.append(risk)
        
        return enriched

    # ================================================================
    # 格式化输出
    # ================================================================

    def format_tendency_report(self, tendency: Dict[str, Any]) -> str:
        """
        格式化法院倾向报告
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"【{tendency['dispute_type']}】法院判决倾向分析")
        lines.append("=" * 60)
        
        lines.append(f"\n📌 倾向概述：{tendency['tendency']}")
        lines.append(f"\n⚖️ 典型结果：{tendency['typical_outcome']}")
        
        if tendency.get("key_factors"):
            lines.append("\n🔍 关键考量因素：")
            for factor in tendency["key_factors"]:
                lines.append(f"  • {factor}")
        
        if tendency.get("related_cases"):
            lines.append(f"\n📚 相关案例（{tendency['total_related']} 个）：")
            for case in tendency["related_cases"]:
                lines.append(f"\n  【{case['case_no']}】{case['title']}")
                lines.append(f"  要旨：{case['holding'][:100]}...")
        
        lines.append("\n" + "-" * 60)
        lines.append("⚠️ 以上分析基于公开指导案例整理，仅供合同风险审查参考，")
        lines.append("不构成法律意见。具体案件请咨询专业律师。")
        
        return "\n".join(lines)

    def format_case_summary(self, case: Dict[str, Any]) -> str:
        """格式化单条案例摘要"""
        lines = []
        lines.append(f"【{case.get('case_no', '未知')}】{case.get('title', '未知')}")
        lines.append(f"  法院：{case.get('court', '未知')} | 年份：{case.get('year', '未知')}")
        lines.append(f"  案由：{case.get('category', '未知')}")
        lines.append(f"  争议焦点：{case.get('dispute_clause', '未知')}")
        lines.append(f"  摘要：{case.get('summary', '无')[:150]}")
        lines.append(f"  裁判要旨：{case.get('holding', '无')[:150]}")
        lines.append(f"  法律依据：{', '.join(case.get('legal_basis', []))}")
        return "\n".join(lines)

    # ================================================================
    # 用户案例导入
    # ================================================================

    def import_user_cases(self, file_path: str) -> Dict[str, Any]:
        """
        导入用户自整理案例
        
        Args:
            file_path: JSON 文件路径
        
        Returns:
            导入结果
        """
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": f"文件不存在: {file_path}"}
        
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证格式
            cases = []
            if isinstance(data, list):
                cases = data
            elif isinstance(data, dict) and "cases" in data:
                cases = data["cases"]
            else:
                return {"status": "error", "message": "格式错误：需要案例列表或含 cases 字段的字典"}
            
            # 确保必要字段
            required_fields = ["id", "title", "holding"]
            valid_cases = []
            for case in cases:
                if all(f in case for f in required_fields):
                    valid_cases.append(case)
            
            if not valid_cases:
                return {"status": "error", "message": "无有效案例（缺少必要字段: id, title, holding）"}
            
            # 保存到用户目录
            USER_CASE_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = USER_CASE_DIR / f"imported_{timestamp}.json"
            
            with open(target, 'w', encoding='utf-8') as f:
                json.dump(valid_cases, f, ensure_ascii=False, indent=2)
            
            # 重新加载
            self._loaded = False
            self._load_data()
            
            return {
                "status": "ok",
                "imported": len(valid_cases),
                "file": str(target),
            }
        except Exception as e:
            return {"status": "error", "message": f"导入失败: {e}"}

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """简单分词：中文单字 + 英文单词"""
        tokens = []
        # 英文单词
        tokens.extend(re.findall(r'[a-zA-Z]+', text.lower()))
        # 中文单字
        tokens.extend(re.findall(r'[\u4e00-\u9fff]', text))
        return tokens

    @property
    def total_cases(self) -> int:
        self._load_data()
        return len(self._cases)

    @property
    def is_available(self) -> bool:
        self._load_data()
        return len(self._cases) > 0

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        self._load_data()
        
        categories = defaultdict(int)
        dispute_types = defaultdict(int)
        for case in self._cases:
            categories[case.get("category", "未知")] += 1
            dispute_types[case.get("dispute_clause", "未知")] += 1
        
        return {
            "total_cases": len(self._cases),
            "categories": dict(categories),
            "dispute_types": dict(dispute_types),
            "data_freshness": "静态公开案例库，非实时判例；数据截止 2026 年 7 月",
        }


# ================================================================
# 全局单例与便捷函数
# ================================================================

_default_retriever: Optional[CaseLawRetriever] = None


def get_case_retriever() -> CaseLawRetriever:
    """获取全局单例"""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = CaseLawRetriever()
    return _default_retriever


def search_cases(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """便捷函数：搜索案例"""
    return get_case_retriever().search(query, max_results)


def get_tendency(dispute_type: str) -> Dict[str, Any]:
    """便捷函数：获取法院倾向"""
    return get_case_retriever().get_court_tendency(dispute_type)


def enrich_risks(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """便捷函数：为风险点补充判决倾向"""
    return get_case_retriever().enrich_risks_with_tendency(risks)


# ================================================================
# 命令行测试
# ================================================================

if __name__ == "__main__":
    retriever = CaseLawRetriever()
    
    print("=" * 60)
    print("类案要点库 v5.2 — 测试")
    print("=" * 60)
    
    # 统计
    stats = retriever.get_stats()
    print(f"\n案例总数: {stats['total_cases']}")
    print(f"数据说明: {stats['data_freshness']}")
    
    # 测试搜索
    print("\n--- 测试关键词搜索 ---")
    results = retriever.search("违约金 过高", max_results=3)
    for r in results:
        print(f"  [{r.get('id')}] {r.get('title')}")
    
    # 测试争议类型搜索
    print("\n--- 测试争议类型搜索 ---")
    results = retriever.search_by_dispute_type("违约责任", max_results=3)
    for r in results:
        print(f"  [{r.get('id')}] {r.get('case_no')} {r.get('title')}")
    
    # 测试法院倾向
    print("\n--- 测试法院倾向 ---")
    tendency = retriever.get_court_tendency("违约责任")
    print(retriever.format_tendency_report(tendency))
    
    # 测试风险富化
    print("\n--- 测试风险富化 ---")
    sample_risks = [{
        "risk_id": "TEST-001",
        "risk_type": "违约金过高",
        "severity": "medium",
        "title": "违约金约定为合同金额的 50%",
        "description": "明显过高",
    }]
    enriched = retriever.enrich_risks_with_tendency(sample_risks)
    for risk in enriched:
        if risk.get("case_references"):
            print(f"  相关案例: {risk['case_references'][0]['case_no']}")
        if risk.get("court_tendency"):
            print(f"  法院倾向: {risk['court_tendency'][:50]}...")
    
    print("\n" + "=" * 60)
    print("测试完成")
