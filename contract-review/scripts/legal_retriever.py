#!/usr/bin/env python3
"""
legal_retriever.py v5.0
法条引用溯源引擎
功能：法条数据库检索、风险点自动匹配法条、法条全文展开、季度更新提醒
v5.0 新增：法条引用溯源（民法典合同编+公司法+司法解释）
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
LEGAL_BASIS_DIR = Path(__file__).resolve().parent.parent / "references" / "legal_basis"
INDEX_FILE = LEGAL_BASIS_DIR / "index.json"

# === 风险类型关键词 → 法条类别映射 ===
RISK_TO_LEGAL_CATEGORY = {
    "违约": ["通则", "典型合同", "担保"],
    "违约金": ["通则"],
    "定金": ["通则"],
    "质量": ["典型合同-买卖", "通则"],
    "交付": ["典型合同-买卖"],
    "付款": ["典型合同-买卖", "通则"],
    "价格": ["典型合同-买卖", "通则"],
    "工期": ["典型合同-建设工程"],
    "工程": ["典型合同-建设工程"],
    "劳动": ["劳动"],
    "工资": ["劳动"],
    "股权": ["公司法", "有限责任公司的股权转让"],
    "股东": ["公司法"],
    "董事": ["公司法"],
    "监事": ["公司法"],
    "知识产权": ["典型合同-技术合同", "ip"],
    "专利": ["典型合同-技术合同"],
    "技术": ["典型合同-技术合同"],
    "保密": ["通则"],
    "不可抗力": ["通则"],
    "争议": ["通则"],
    "仲裁": ["通则"],
    "诉讼": ["通则"],
    "格式条款": ["通则"],
    "合同成立": ["通则"],
    "合同无效": ["总则", "民法典"],
    "合同解除": ["通则"],
    "借贷": ["借贷", "典型合同-借款"],
    "利息": ["借贷", "典型合同-借款"],
    "租赁": ["租赁", "典型合同-租赁"],
    "转租": ["租赁", "典型合同-租赁"],
    "建设工程": ["建设工程"],
    "优先受偿": ["建设工程"],
    "买卖": ["典型合同-买卖", "买卖合同"],
    "食品安全": ["消费"],
    "保险": ["保险"],
    "房地产": ["房地产"],
    "担保": ["担保"],
    "保证": ["担保"],
    "代理": ["总则"],
    "欺诈": ["总则"],
    "胁迫": ["总则"],
    "重大误解": ["总则"],
    "显失公平": ["总则"],
    "电子": ["电子签名"],
}


class LegalRetriever:
    """法条检索引擎 — 本地 YAML 数据库 + 关键词自动匹配"""

    def __init__(self, basis_dir: Optional[Path] = None):
        self.basis_dir = basis_dir or LEGAL_BASIS_DIR
        self.index_file = self.basis_dir / "index.json"
        self._index: Dict[str, str] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._loaded: bool = False
        self._load_index()

    # ---------- 加载 ----------
    def _load_index(self):
        if not self.index_file.exists():
            logger.warning(f"法条索引文件不存在: {self.index_file}")
            return
        try:
            with open(self.index_file, encoding='utf-8') as f:
                data = json.load(f)
            self._index = data.get("index", {})
            self._loaded = True
            logger.debug(f"法条索引加载成功，共 {len(self._index)} 条")
        except Exception as e:
            logger.warning(f"法条索引加载失败: {e}")

    def _load_source(self, filename: str) -> Optional[Dict[str, Any]]:
        if filename in self._cache:
            return self._cache[filename]
        fpath = self.basis_dir / filename
        if not fpath.exists():
            return None
        try:
            import yaml
            with open(fpath, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self._cache[filename] = data
            return data
        except ImportError:
            logger.warning("未安装 pyyaml，无法读取法条数据库")
            return None
        except Exception as e:
            logger.warning(f"加载法条文件失败 {filename}: {e}")
            return None

    # ---------- 查询 ----------
    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """根据法条 ID 获取完整法条信息"""
        if not self._loaded:
            return None
        filename = self._index.get(article_id)
        if not filename:
            return None
        data = self._load_source(filename)
        if not data:
            return None
        for article in data.get("articles", data.get("interpretations", [])):
            if article.get("id") == article_id:
                article["law_name"] = data.get("law_name", "")
                return article
        return None

    def search_by_keywords(self, keywords: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
        """根据关键词搜索相关法条"""
        if not self._loaded:
            return []
        results: List[Dict[str, Any]] = []
        for filename in set(self._index.values()):
            data = self._load_source(filename)
            if not data:
                continue
            articles = data.get("articles", data.get("interpretations", []))
            for article in articles:
                score = self._keyword_score(article, keywords)
                if score > 0:
                    article["_score"] = score
                    article["law_name"] = data.get("law_name", "")
                    results.append(article)
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return results[:max_results]

    def _keyword_score(self, article: Dict[str, Any], keywords: List[str]) -> int:
        """计算法条与关键词的匹配分"""
        score = 0
        text = " ".join([
            article.get("title", ""),
            article.get("text", ""),
            " ".join(article.get("keywords", [])),
            article.get("category", ""),
        ]).lower()
        for kw in keywords:
            kw_lower = kw.lower()
            # 标题匹配权重最高
            if kw_lower in article.get("title", "").lower():
                score += 5
            # 关键词列表匹配
            for k in article.get("keywords", []):
                if kw_lower in k.lower() or k.lower() in kw_lower:
                    score += 3
            # 正文匹配
            if kw_lower in text:
                score += 1
        return score

    # ---------- 自动匹配 ----------
    def match_for_risk(self, risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为风险点自动匹配相关法条"""
        # 构建检索关键词
        keywords: List[str] = []
        title = str(risk.get("title", "") or "")
        description = str(risk.get("description", "") or "")
        risk_type = str(risk.get("risk_type", "") or "")
        clause_ref = str(risk.get("clause_ref", "") or "")

        # 风险类型直接映射
        keywords.extend(self._extract_keywords(risk_type))
        keywords.extend(self._extract_keywords(title))
        keywords.extend(self._extract_keywords(description))
        keywords.extend(self._extract_keywords(clause_ref))

        # 去重
        keywords = list(dict.fromkeys(keywords))

        # 搜索
        articles = self.search_by_keywords(keywords, max_results=3)
        return articles

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取法律相关关键词"""
        if not text:
            return []
        # 简单的关键词提取：匹配已知法律术语
        keywords = []
        text_lower = text.lower()
        for risk_key in RISK_TO_LEGAL_CATEGORY:
            if risk_key in text:
                keywords.append(risk_key)
        # 也提取 2-4 字词组
        for n in (4, 3, 2):
            for i in range(len(text) - n + 1):
                gram = text[i:i + n]
                if any(c in gram for c in "《》（）的之"):
                    continue
                if gram in ("合同", "下列", "应当", "可以", "不得", "必须"):
                    continue
                keywords.append(gram)
        return keywords

    # ---------- 格式化输出 ----------
    def format_citation(self, article: Dict[str, Any], include_text: bool = False) -> str:
        """格式化法条引用"""
        law = article.get("law_name", "相关法律")
        title = article.get("title", "")
        article_id = article.get("id", "")
        text = article.get("text", "")
        category = article.get("category", "")

        # 推断"第 X 条"
        article_num = self._infer_article_number(article_id, category)

        cite = f"依据《{law}》第 {article_num} 条"
        if title:
            cite += f"（{title}）"
        cite += f"：{text}" if include_text else ""
        return cite

    def _infer_article_number(self, article_id: str, category: str) -> str:
        """从法条 ID 推断条文序号"""
        # 尝试从 ID 中提取数字
        m = re.search(r'(\d+)$', article_id)
        if m:
            return m.group(1)
        return "?"

    def format_citation_full(self, article: Dict[str, Any]) -> str:
        """完整格式（含法条全文）"""
        return self.format_citation(article, include_text=True)

    # ---------- 批量富化 ----------
    def enrich_risks(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为风险点列表自动匹配法条并写入 legal_basis 字段"""
        enriched = []
        for risk in risks:
            risk = dict(risk)  # 不修改原对象
            articles = self.match_for_risk(risk)
            if articles:
                # 保留现有的 legal_basis，追加新引用
                existing = risk.get("legal_basis", "")
                citations = []
                for a in articles:
                    cite = self.format_citation(a, include_text=False)
                    citations.append(cite)
                # 合并并去重
                if existing:
                    citations.insert(0, existing)
                seen = set()
                unique = []
                for c in citations:
                    if c not in seen:
                        seen.add(c)
                        unique.append(c)
                risk["legal_basis"] = "；".join(unique[:3])
            enriched.append(risk)
        return enriched

    # ---------- 季度更新提醒 ----------
    def check_update_reminder(self) -> Optional[str]:
        """检查法条数据库是否需要更新（季度提醒）"""
        # 获取数据库中最新法条的更新日期
        latest = self._get_db_latest_date()
        if not latest:
            return None
        # 简单规则：每季度提醒一次
        from datetime import datetime, timedelta
        try:
            last_date = datetime.strptime(latest, "%Y-%m-%d")
            if datetime.now() - last_date > timedelta(days=90):
                return (
                    f"法条数据库已 {latest} 更新，距今超过 3 个月。"
                    f"建议检查最新法律法规变化。"
                )
        except ValueError:
            pass
        return None

    def _get_db_latest_date(self) -> Optional[str]:
        """获取数据库中最新日期"""
        if not self._loaded:
            return None
        dates = []
        for filename in set(self._index.values()):
            data = self._load_source(filename)
            if data:
                d = data.get("last_verified") or data.get("effective_date")
                if d:
                    dates.append(str(d))
        if dates:
            return max(dates)
        return None

    @property
    def is_available(self) -> bool:
        return self._loaded and len(self._index) > 0

    @property
    def total_articles(self) -> int:
        return len(self._index)


# ---------- 便捷函数 ----------
_default_retriever: Optional[LegalRetriever] = None


def get_retriever() -> LegalRetriever:
    """获取全局单例"""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = LegalRetriever()
    return _default_retriever


def enrich_risks(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """便捷函数：为风险点列表匹配法条"""
    return get_retriever().enrich_risks(risks)


def search_law(keywords: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
    """便捷函数：搜索法条"""
    return get_retriever().search_by_keywords(keywords, max_results)


if __name__ == "__main__":
    # 简单测试
    retriever = LegalRetriever()
    print(f"法条数据库可用: {retriever.is_available}")
    print(f"法条总数: {retriever.total_articles}")

    # 测试搜索
    results = retriever.search_by_keywords(["违约金", "过高"], max_results=3)
    print(f"\n搜索'违约金 过高'，命中 {len(results)} 条:")
    for r in results:
        print(f"  - {retriever.format_citation(r, include_text=True)}")

    # 测试富化
    sample_risks = [{
        "risk_id": "TEST-001",
        "risk_type": "违约金过高",
        "severity": "medium",
        "title": "违约金约定为合同金额的 50%，明显过高",
        "description": "依据《民法典》第 584 条，违约金过高可请求人民法院适当减少",
        "suggestion": "建议将违约金调整至合同金额的 10%-20%",
        "legal_basis": "",
        "text_snippet": "违约金 50%",
        "clause_ref": "第 8 条",
    }]
    enriched = retriever.enrich_risks(sample_risks)
    print("\n富化结果:")
    for risk in enriched:
        print(f"  法条: {risk.get('legal_basis', '无')}")

    # 季度提醒
    reminder = retriever.check_update_reminder()
    if reminder:
        print(f"\n⚠️ {reminder}")
    else:
        print("\n✅ 法条数据库更新及时")
