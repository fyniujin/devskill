#!/usr/bin/env python3
"""
unified_retriever.py v5.2
统一检索引擎 — 合并 legal_retriever（法条检索）与 clause_matcher（条款匹配）

架构：
- 共享分词（char/bigram）和 TF-IDF/BM25 基础设施
- 双索引：法条索引（来自 references/legal_basis/*.yaml）+ 条款索引（来自 references/clause_library/clauses.json）
- 统一搜索接口：search() 同时检索两个索引，按相关度合并排序
- 保留 enrich_risks() 和 match() 兼容接口，供现有 main.py 调用

v5.2 新增：统一检索引擎
"""

import json
import logging
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"
LEGAL_BASIS_DIR = REFERENCES_DIR / "legal_basis"
LEGAL_INDEX_FILE = LEGAL_BASIS_DIR / "index.json"
CLAUSE_LIBRARY_PATH = REFERENCES_DIR / "clause_library" / "clauses.json"
CLAUSE_INDEX_PATH = REFERENCES_DIR / "clause_library" / "clause_index.yaml"

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

# 风险类型 → 条款库分类
RISK_TYPE_MAPPING = {
    '主体风险': 'subject', '条款风险': 'clause', '金额风险': 'amount',
    '价款风险': 'amount', '履行风险': 'performance', '交付风险': 'performance',
    '质量风险': 'performance', '争议解决风险': 'dispute', '争议风险': 'dispute',
    '合规风险': 'compliance', '知识产权风险': 'ip', '知识产权': 'ip',
    '保密风险': 'confidentiality', '保密': 'confidentiality',
    '终止风险': 'termination', '解除风险': 'termination',
    '违约责任风险': 'liability', '违约风险': 'liability', '责任风险': 'liability',
}

ENGLISH_CATEGORY_MAPPING = {
    'subject': 'subject', 'party': 'subject',
    'clause': 'clause', 'terms': 'clause',
    'amount': 'amount', 'payment': 'amount', 'price': 'amount',
    'performance': 'performance', 'delivery': 'performance', 'quality': 'performance',
    'dispute': 'dispute', 'arbitration': 'dispute', 'jurisdiction': 'dispute',
    'compliance': 'compliance', 'regulatory': 'compliance',
    'ip': 'ip', 'intellectual_property': 'ip',
    'confidentiality': 'confidentiality', 'nda': 'confidentiality',
    'termination': 'termination', 'exit': 'termination',
    'liability': 'liability', 'breach': 'liability', 'penalty': 'liability',
}

SEVERITY_TO_LEVEL = {
    'critical': '高', 'high': '高', '严重': '高', '高': '高',
    'medium': '中等', '中等': '中等', '中': '中等',
    'low': '低', '一般': '中等', '提示': '低', '低': '低',
}

MATCH_THRESHOLD = 0.25

# BM25 参数
BM25_K1 = 1.5
BM25_B = 0.75


class UnifiedRetriever:
    """
    统一检索引擎
    
    共享基础设施：
    - _tokenize(): char/bigram 分词
    - _bm25_score(): BM25 打分
    - _tf_idf(): TF-IDF 打分
    
    双索引：
    - _legal_index: 法条索引 {article_id: {tokens, metadata}}
    - _clause_index: 条款索引 {clause_id: {tokens, metadata}}
    """

    def __init__(self):
        # 法条数据
        self._legal_index: Dict[str, Dict[str, Any]] = {}
        self._legal_cache: Dict[str, Dict[str, Any]] = {}
        self._legal_loaded = False
        
        # 条款数据
        self._clause_index: Dict[str, Dict[str, Any]] = {}
        self._clause_data: List[Dict] = []
        self._clause_by_id: Dict[str, Dict] = {}
        self._clause_keyword_index: Dict[str, List[str]] = {}
        self._clause_loaded = False
        
        # 共享统计
        self._doc_count = 0
        self._avg_doc_len = 0
        self._doc_lengths: Dict[str, int] = {}

    # ================================================================
    # 共享分词与评分基础设施
    # ================================================================

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        共享分词：char + bigram + 英文单词 + 数字
        中文单字 + 双字组合，对中文分词无依赖
        """
        tokens = []
        # 英文单词
        tokens.extend(re.findall(r'[a-zA-Z]+', text.lower()))
        # 数字
        tokens.extend(re.findall(r'\d+', text))
        # 中文 char + bigram
        cn_chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(cn_chars)
        for i in range(len(cn_chars) - 1):
            tokens.append(cn_chars[i] + cn_chars[i + 1])
        return tokens

    def _bm25_score(self, query_tokens: List[str], doc_id: str,
                    term_freqs: Dict[str, int]) -> float:
        """
        BM25 打分算法
        
        score = Σ IDF(qi) * (f(qi,D) * (k1+1)) / (f(qi,D) + k1 * (1 - b + b * |D|/avgdl))
        """
        score = 0.0
        doc_len = self._doc_lengths.get(doc_id, 0)
        avgdl = self._avg_doc_len if self._avg_doc_len > 0 else 1.0

        for term in query_tokens:
            # 逆文档频率
            df = sum(1 for d in self._doc_lengths if term in self._get_term_freqs(d))
            idf = math.log((self._doc_count - df + 0.5) / (df + 0.5) + 1.0)
            
            # 词频
            f = term_freqs.get(term, 0)
            if f == 0:
                continue
            
            # BM25 公式
            numerator = f * (BM25_K1 + 1)
            denominator = f + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / avgdl)
            score += idf * numerator / denominator
        
        return score

    def _tf_idf(self, query_tokens: List[str], doc_id: str,
                term_freqs: Dict[str, int]) -> float:
        """
        TF-IDF 打分（轻量备选）
        """
        score = 0.0
        doc_len = self._doc_lengths.get(doc_id, 1)
        if doc_len == 0:
            doc_len = 1

        for term in query_tokens:
            # 词频归一化
            tf = term_freqs.get(term, 0) / doc_len
            # 逆文档频率
            df = sum(1 for d in self._doc_lengths if term in self._get_term_freqs(d))
            idf = math.log(self._doc_count / (df + 1)) + 1.0
            score += tf * idf
        
        return score

    def _get_term_freqs(self, doc_id: str) -> Dict[str, int]:
        """获取文档的词频（从内存索引）"""
        if doc_id in self._legal_index:
            return self._legal_index[doc_id].get("_term_freqs", {})
        if doc_id in self._clause_index:
            return self._clause_index[doc_id].get("_term_freqs", {})
        return {}

    # ================================================================
    # 法条索引加载
    # ================================================================

    def _load_legal_index(self):
        """加载法条索引"""
        if self._legal_loaded:
            return
        
        if not LEGAL_INDEX_FILE.exists():
            logger.warning(f"法条索引文件不存在: {LEGAL_INDEX_FILE}")
            self._legal_loaded = True
            return
        
        try:
            with open(LEGAL_INDEX_FILE, encoding='utf-8') as f:
                index_data = json.load(f)
            
            index_map = index_data.get("index", {})
            
            for article_id, filename in index_map.items():
                data = self._load_legal_source(filename)
                if not data:
                    continue
                
                articles = data.get("articles", data.get("interpretations", []))
                for article in articles:
                    if article.get("id") != article_id:
                        continue
                    
                    # 构建可检索文本
                    text_parts = [
                        article.get("title", ""),
                        article.get("text", ""),
                        " ".join(article.get("keywords", [])),
                        article.get("category", ""),
                    ]
                    searchable_text = " ".join(filter(None, text_parts))
                    tokens = self._tokenize(searchable_text)
                    
                    # 词频统计
                    term_freqs = defaultdict(int)
                    for t in tokens:
                        term_freqs[t] += 1
                    
                    self._legal_index[article_id] = {
                        "_term_freqs": dict(term_freqs),
                        "_tokens": tokens,
                        "_metadata": article,
                        "_law_name": data.get("law_name", ""),
                        "_source_file": filename,
                    }
                    self._doc_lengths[article_id] = len(tokens)
            
            self._legal_loaded = True
            logger.debug(f"法条索引加载完成: {len(self._legal_index)} 条")
        except Exception as e:
            logger.warning(f"法条索引加载失败: {e}")
            self._legal_loaded = True

    def _load_legal_source(self, filename: str) -> Optional[Dict[str, Any]]:
        """加载法条源文件（带缓存）"""
        if filename in self._legal_cache:
            return self._legal_cache[filename]
        
        fpath = LEGAL_BASIS_DIR / filename
        if not fpath.exists():
            return None
        
        try:
            import yaml
            with open(fpath, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self._legal_cache[filename] = data
            return data
        except ImportError:
            logger.warning("未安装 pyyaml，无法读取法条数据库")
            return None
        except Exception as e:
            logger.warning(f"加载法条文件失败 {filename}: {e}")
            return None

    # ================================================================
    # 条款索引加载
    # ================================================================

    def _load_clause_index(self):
        """加载条款索引"""
        if self._clause_loaded:
            return
        
        try:
            with open(CLAUSE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._clause_data = data.get('clauses', [])
            self._clause_by_id = {c['id']: c for c in self._clause_data if 'id' in c}
            
            # 加载分类索引
            import yaml
            with open(CLAUSE_INDEX_PATH, 'r', encoding='utf-8') as f:
                clause_index = yaml.safe_load(f) or {}
            
            # 构建关键词倒排
            for cat_code, entry in clause_index.items():
                if not isinstance(entry, dict):
                    continue
                for kw in entry.get('keywords', []) or []:
                    self._clause_keyword_index.setdefault(str(kw), []).append(cat_code)
            
            # 为每个条款构建可检索文本
            for clause in self._clause_data:
                clause_id = clause.get('id', '')
                if not clause_id:
                    continue
                
                text_parts = [
                    clause.get('name', ''),
                    clause.get('category', ''),
                    clause.get('recommended_text', ''),
                    " ".join(clause.get('tags', []) or []),
                ]
                searchable_text = " ".join(filter(None, text_parts))
                tokens = self._tokenize(searchable_text)
                
                term_freqs = defaultdict(int)
                for t in tokens:
                    term_freqs[t] += 1
                
                self._clause_index[clause_id] = {
                    "_term_freqs": dict(term_freqs),
                    "_tokens": tokens,
                    "_metadata": clause,
                }
                self._doc_lengths[clause_id] = len(tokens)
            
            self._clause_loaded = True
            logger.debug(f"条款索引加载完成: {len(self._clause_index)} 条")
        except Exception as e:
            logger.warning(f"条款索引加载失败: {e}")
            self._clause_loaded = True

    # ================================================================
    # 索引统计更新
    # ================================================================

    def _update_stats(self):
        """更新全局统计信息"""
        self._doc_count = len(self._legal_index) + len(self._clause_index)
        if self._doc_count > 0:
            total_len = sum(self._doc_lengths.values())
            self._avg_doc_len = total_len / self._doc_count
        else:
            self._avg_doc_len = 0

    # ================================================================
    # 统一搜索接口
    # ================================================================

    def search(self, query: str, index_type: str = "both",
               max_results: int = 10, min_score: float = 0.01) -> List[Dict[str, Any]]:
        """
        统一搜索接口
        
        Args:
            query: 搜索关键词
            index_type: 索引类型 — "legal"(法条) / "clause"(条款) / "both"(双索引)
            max_results: 最大返回条数
            min_score: 最低分数阈值
        
        Returns:
            合并排序的搜索结果列表
        """
        self._load_legal_index()
        self._load_clause_index()
        self._update_stats()
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        results = []
        
        # 搜索法条索引
        if index_type in ("both", "legal"):
            for doc_id, doc_info in self._legal_index.items():
                term_freqs = doc_info.get("_term_freqs", {})
                score = self._bm25_score(query_tokens, doc_id, term_freqs)
                if score >= min_score:
                    results.append({
                        "type": "legal",
                        "id": doc_id,
                        "score": round(score, 4),
                        "title": doc_info["_metadata"].get("title", ""),
                        "text": doc_info["_metadata"].get("text", "")[:200],
                        "law_name": doc_info.get("_law_name", ""),
                        "category": doc_info["_metadata"].get("category", ""),
                        "metadata": doc_info["_metadata"],
                    })
        
        # 搜索条款索引
        if index_type in ("both", "clause"):
            for doc_id, doc_info in self._clause_index.items():
                term_freqs = doc_info.get("_term_freqs", {})
                score = self._bm25_score(query_tokens, doc_id, term_freqs)
                if score >= min_score:
                    results.append({
                        "type": "clause",
                        "id": doc_id,
                        "score": round(score, 4),
                        "title": doc_info["_metadata"].get("name", ""),
                        "text": doc_info["_metadata"].get("recommended_text", "")[:200],
                        "category": doc_info["_metadata"].get("category", ""),
                        "metadata": doc_info["_metadata"],
                    })
        
        # 按分数降序排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    def search_legal(self, keywords: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
        """
        法条关键词搜索（兼容 legal_retriever.search_by_keywords）
        
        Args:
            keywords: 关键词列表
            max_results: 最大返回条数
        
        Returns:
            法条搜索结果
        """
        query = " ".join(keywords)
        return self.search(query, index_type="legal", max_results=max_results)

    def search_clause(self, keywords: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
        """
        条款关键词搜索
        
        Args:
            keywords: 关键词列表
            max_results: 最大返回条数
        
        Returns:
            条款搜索结果
        """
        query = " ".join(keywords)
        return self.search(query, index_type="clause", max_results=max_results)

    # ================================================================
    # 兼容接口：法条富化（enrich_risks）
    # ================================================================

    def enrich_risks(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为风险点列表自动匹配法条并写入 legal_basis 字段
        （兼容 legal_retriever.enrich_risks）
        """
        self._load_legal_index()
        self._update_stats()
        
        enriched = []
        for risk in risks:
            risk = dict(risk)  # 不修改原对象
            
            # 构建检索关键词
            keywords = self._extract_keywords_from_risk(risk)
            query = " ".join(keywords)
            query_tokens = self._tokenize(query)
            
            if not query_tokens:
                enriched.append(risk)
                continue
            
            # BM25 检索
            results = []
            for doc_id, doc_info in self._legal_index.items():
                term_freqs = doc_info.get("_term_freqs", {})
                score = self._bm25_score(query_tokens, doc_id, term_freqs)
                if score > 0:
                    results.append((score, doc_info))
            
            results.sort(key=lambda x: x[0], reverse=True)
            
            if results:
                citations = []
                for score, doc_info in results[:3]:
                    article = doc_info["_metadata"]
                    cite = self._format_citation(article, doc_info.get("_law_name", ""))
                    citations.append(cite)
                
                existing = risk.get("legal_basis", "")
                if existing:
                    citations.insert(0, existing)
                
                # 去重
                seen = set()
                unique = []
                for c in citations:
                    if c not in seen:
                        seen.add(c)
                        unique.append(c)
                
                risk["legal_basis"] = "；".join(unique[:3])
            
            enriched.append(risk)
        
        return enriched

    def _extract_keywords_from_risk(self, risk: Dict[str, Any]) -> List[str]:
        """从风险点提取关键词"""
        keywords = []
        title = str(risk.get("title", "") or "")
        description = str(risk.get("description", "") or "")
        risk_type = str(risk.get("risk_type", "") or "")
        clause_ref = str(risk.get("clause_ref", "") or "")
        
        # 风险类型映射
        for risk_key in RISK_TO_LEGAL_CATEGORY:
            if risk_key in risk_type or risk_key in title or risk_key in description:
                keywords.append(risk_key)
        
        # 提取 2-4 字词组
        for text in [title, description]:
            for n in (4, 3, 2):
                for i in range(len(text) - n + 1):
                    gram = text[i:i + n]
                    if any(c in gram for c in "《》（）的之"):
                        continue
                    if gram in ("合同", "下列", "应当", "可以", "不得", "必须"):
                        continue
                    keywords.append(gram)
        
        # 去重保序
        return list(dict.fromkeys(keywords))

    def _format_citation(self, article: Dict[str, Any], law_name: str) -> str:
        """格式化法条引用"""
        title = article.get("title", "")
        article_id = article.get("id", "")
        text = article.get("text", "")
        
        # 推断条文序号
        m = re.search(r'(\d+)$', article_id)
        article_num = m.group(1) if m else "?"
        
        cite = f"依据《{law_name or '相关法律'}》第 {article_num} 条"
        if title:
            cite += f"（{title}）"
        return cite

    # ================================================================
    # 兼容接口：条款匹配（match）
    # ================================================================

    def match(self, risk: Dict, contract_type: str = "") -> Optional[Dict]:
        """
        为风险点匹配推荐条款（兼容 clause_matcher.match）
        """
        self._load_clause_index()
        self._update_stats()
        
        if not self._clause_data:
            return None
        
        # 解析分类
        categories = self._resolve_categories(risk)
        candidate_ids = self._collect_candidates(categories)
        
        # 构建候选池
        pool = (
            [self._clause_by_id[i] for i in candidate_ids if i in self._clause_by_id]
            if candidate_ids else self._clause_data
        )
        
        # 构建风险查询文本
        risk_text = f"{risk.get('title', '')} {risk.get('description', '')}"
        query_tokens = self._tokenize(risk_text)
        
        if not query_tokens:
            return None
        
        best_match = None
        best_score = 0.0
        
        for clause in pool:
            clause_id = clause.get('id', '')
            doc_info = self._clause_index.get(clause_id)
            if not doc_info:
                continue
            
            term_freqs = doc_info.get("_term_freqs", {})
            score = self._bm25_score(query_tokens, clause_id, term_freqs)
            
            # 分类加权
            clause_category = clause.get('category', '')
            if clause_category and clause_category in categories:
                rank = categories.index(clause_category)
                if rank == 0:
                    score += 0.25
                elif rank == 1:
                    score += 0.15
                else:
                    score += 0.06
            
            # 适用范围加权
            applicable_scope = clause.get('applicable_scope', []) or []
            if applicable_scope:
                if contract_type and any(contract_type in s or s in contract_type
                                         for s in applicable_scope):
                    score += 0.12
                elif '通用' in applicable_scope:
                    score += 0.06
            
            # 风险等级匹配
            sev = str(risk.get('severity', '')).strip()
            risk_level = SEVERITY_TO_LEVEL.get(sev.lower(), SEVERITY_TO_LEVEL.get(sev, ''))
            clause_level = str(clause.get('risk_level', '')).strip()
            if risk_level and clause_level and risk_level == clause_level:
                score += 0.08
            
            if score > best_score + 1e-9:
                best_score = score
                best_match = clause
        
        if best_score < MATCH_THRESHOLD:
            return None
        return best_match

    def match_top_n(self, risk: Dict, contract_type: str = "", n: int = 3) -> List[Dict]:
        """返回匹配度最高的前 N 条条款"""
        self._load_clause_index()
        self._update_stats()
        
        if not self._clause_data:
            return []
        
        categories = self._resolve_categories(risk)
        candidate_ids = self._collect_candidates(categories)
        pool = (
            [self._clause_by_id[i] for i in candidate_ids if i in self._clause_by_id]
            if candidate_ids else self._clause_data
        )
        
        risk_text = f"{risk.get('title', '')} {risk.get('description', '')}"
        query_tokens = self._tokenize(risk_text)
        
        scored = []
        for clause in pool:
            clause_id = clause.get('id', '')
            doc_info = self._clause_index.get(clause_id)
            if not doc_info:
                continue
            
            term_freqs = doc_info.get("_term_freqs", {})
            score = self._bm25_score(query_tokens, clause_id, term_freqs)
            
            # 分类加权
            clause_category = clause.get('category', '')
            if clause_category and clause_category in categories:
                rank = categories.index(clause_category)
                if rank == 0:
                    score += 0.25
                elif rank == 1:
                    score += 0.15
                else:
                    score += 0.06
            
            if score >= MATCH_THRESHOLD:
                item = dict(clause)
                item['score'] = round(score, 3)
                scored.append(item)
        
        scored.sort(key=lambda c: c['score'], reverse=True)
        return scored[:n]

    def _resolve_categories(self, risk: Dict) -> List[str]:
        """解析风险点归属的条款库分类"""
        weights: Dict[str, float] = {}

        def bump(code: str, w: float):
            if code:
                weights[code] = weights.get(code, 0.0) + w

        risk_type = str(risk.get('risk_type', '')).strip()

        if risk_type in RISK_TYPE_MAPPING:
            bump(RISK_TYPE_MAPPING[risk_type], 10.0)
        else:
            for cn, code in RISK_TYPE_MAPPING.items():
                if cn and cn in risk_type:
                    bump(code, 6.0)

        low = risk_type.lower()
        if low in ENGLISH_CATEGORY_MAPPING:
            bump(ENGLISH_CATEGORY_MAPPING[low], 10.0)

        text = f"{risk.get('title', '')} {risk.get('description', '')}"
        for kw, codes in self._clause_keyword_index.items():
            if kw and kw in text:
                w = 0.6 if len(kw) <= 2 else (1.2 if len(kw) == 3 else 2.2)
                w = w / max(1, len(codes))
                for code in codes:
                    bump(code, w)

        return [c for c, _ in sorted(weights.items(), key=lambda kv: kv[1], reverse=True)]

    def _collect_candidates(self, categories: List[str]) -> set:
        """按分类收集候选条款 id"""
        candidate_ids = set()
        for code in categories:
            # 从 clause_index.yaml 获取
            try:
                import yaml
                with open(CLAUSE_INDEX_PATH, 'r', encoding='utf-8') as f:
                    clause_index = yaml.safe_load(f) or {}
                entry = clause_index.get(code)
                if isinstance(entry, dict):
                    candidate_ids.update(entry.get('clause_ids', []) or [])
            except Exception:
                pass
        return candidate_ids

    # ================================================================
    # 兼容接口：法条查询
    # ================================================================

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """根据法条 ID 获取完整法条信息（兼容 legal_retriever.get_article）"""
        self._load_legal_index()
        
        if article_id in self._legal_index:
            return self._legal_index[article_id]["_metadata"]
        
        # 回退到原始加载逻辑
        if not LEGAL_INDEX_FILE.exists():
            return None
        try:
            with open(LEGAL_INDEX_FILE, encoding='utf-8') as f:
                index_data = json.load(f)
            filename = index_data.get("index", {}).get(article_id)
            if not filename:
                return None
            data = self._load_legal_source(filename)
            if not data:
                return None
            for article in data.get("articles", data.get("interpretations", [])):
                if article.get("id") == article_id:
                    article["law_name"] = data.get("law_name", "")
                    return article
        except Exception:
            pass
        return None

    def get_clause_by_id(self, clause_id: str) -> Optional[Dict]:
        """按条款编号精确获取"""
        self._load_clause_index()
        return self._clause_by_id.get(clause_id)

    # ================================================================
    # 兼容接口：更新提醒
    # ================================================================

    def check_update_reminder(self) -> Optional[str]:
        """检查法条数据库是否需要更新（季度提醒）"""
        self._load_legal_index()
        
        latest = self._get_db_latest_date()
        if not latest:
            return None
        
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
        dates = []
        for filename in set(self._legal_cache.keys()):
            data = self._legal_cache.get(filename)
            if data:
                d = data.get("last_verified") or data.get("effective_date")
                if d:
                    dates.append(str(d))
        if dates:
            return max(dates)
        return None

    # ================================================================
    # 属性
    # ================================================================

    @property
    def is_available(self) -> bool:
        self._load_legal_index()
        return len(self._legal_index) > 0

    @property
    def total_articles(self) -> int:
        self._load_legal_index()
        return len(self._legal_index)

    @property
    def total_clauses(self) -> int:
        self._load_clause_index()
        return len(self._clause_index)

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        self._load_legal_index()
        self._load_clause_index()
        return {
            "legal_articles": len(self._legal_index),
            "clauses": len(self._clause_index),
            "total_documents": len(self._legal_index) + len(self._clause_index),
            "avg_doc_length": round(self._avg_doc_len, 2),
        }


# ================================================================
# 全局单例与便捷函数
# ================================================================

_default_retriever: Optional[UnifiedRetriever] = None


def get_retriever() -> UnifiedRetriever:
    """获取全局单例"""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = UnifiedRetriever()
    return _default_retriever


def enrich_risks(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """便捷函数：为风险点列表匹配法条（兼容 legal_retriever.enrich_risks）"""
    return get_retriever().enrich_risks(risks)


def search_law(keywords: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
    """便捷函数：搜索法条（兼容 legal_retriever.search_law）"""
    return get_retriever().search_legal(keywords, max_results)


def match_clause(risk: Dict, contract_type: str = "") -> Optional[Dict]:
    """便捷函数：匹配条款（兼容 clause_matcher.match）"""
    return get_retriever().match(risk, contract_type)


def search_unified(query: str, index_type: str = "both",
                   max_results: int = 10) -> List[Dict[str, Any]]:
    """便捷函数：统一搜索"""
    return get_retriever().search(query, index_type, max_results)


# ================================================================
# 命令行测试
# ================================================================

if __name__ == "__main__":
    retriever = UnifiedRetriever()
    
    print("=" * 60)
    print("统一检索引擎 v5.2 — 测试")
    print("=" * 60)
    
    # 统计
    stats = retriever.get_stats()
    print(f"\n索引统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # 测试统一搜索
    print("\n--- 测试统一搜索 ---")
    results = retriever.search("违约金 过高", max_results=5)
    for r in results:
        print(f"  [{r['type']}] {r['id']} (score={r['score']}) {r['title'][:30]}")
    
    # 测试法条搜索
    print("\n--- 测试法条搜索 ---")
    results = retriever.search_legal(["违约金", "过高"], max_results=3)
    for r in results:
        print(f"  {r['id']} (score={r['score']}) {r['title'][:30]}")
    
    # 测试条款搜索
    print("\n--- 测试条款搜索 ---")
    results = retriever.search_clause(["违约责任", "赔偿"], max_results=3)
    for r in results:
        print(f"  {r['id']} (score={r['score']}) {r['title'][:30]}")
    
    # 测试富化
    print("\n--- 测试风险富化 ---")
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
    for risk in enriched:
        print(f"  法条: {risk.get('legal_basis', '无')}")
    
    # 测试条款匹配
    print("\n--- 测试条款匹配 ---")
    test_risk = {
        'risk_id': 'T1', 'risk_type': '条款风险',
        'title': '违约责任约定不明确',
        'description': '未约定违约金计算方式', 'severity': '严重'
    }
    result = retriever.match(test_risk, '买卖合同')
    if result:
        print(f"  匹配: {result['id']} {result.get('name')}")
    else:
        print("  未匹配到条款")
    
    # 测试更新提醒
    print("\n--- 测试更新提醒 ---")
    reminder = retriever.check_update_reminder()
    if reminder:
        print(f"  ⚠️ {reminder}")
    else:
        print("  ✅ 数据库更新及时")
    
    print("\n" + "=" * 60)
    print("测试完成")
