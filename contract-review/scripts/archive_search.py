#!/usr/bin/env python3
"""
archive_search.py v5.2
档案库全文检索引擎
功能：倒排索引（char/bigram + TF-IDF）、多维过滤（条款类型/风险等级/对方主体）、命中高亮
v5.2 新增：档案库全文检索
"""

import json
import logging
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
INDEX_DIR = Path.home() / '.contract-review' / 'search_index'
INDEX_FILE = INDEX_DIR / 'inverted_index.json'
DOC_INDEX_FILE = INDEX_DIR / 'doc_index.json'
METADATA_FILE = INDEX_DIR / 'metadata.json'


class ArchiveSearch:
    """档案库全文检索引擎 — 倒排索引 + TF-IDF + 多维过滤"""

    def __init__(self, index_dir: Optional[Path] = None):
        self.index_dir = index_dir or INDEX_DIR
        self.index_file = self.index_dir / 'inverted_index.json'
        self.doc_index_file = self.index_dir / 'doc_index.json'
        self.metadata_file = self.index_dir / 'metadata.json'
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存中的索引
        self._inverted_index: Dict[str, Dict[str, List[int]]] = {}  # term -> {doc_id: [positions]}
        self._doc_index: Dict[str, Dict[str, Any]] = {}  # doc_id -> doc_metadata
        self._doc_count: int = 0
        self._avg_doc_len: float = 0
        
        self._load_index()

    # ---------- 分词 ----------
    def _tokenize(self, text: str) -> List[str]:
        """
        分词：char + bigram
        支持中文和英文
        """
        tokens = []
        
        # 英文单词
        en_tokens = re.findall(r'[a-zA-Z]+', text.lower())
        tokens.extend(en_tokens)
        
        # 数字
        num_tokens = re.findall(r'\d+', text)
        tokens.extend(num_tokens)
        
        # 中文 char + bigram
        cn_chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(cn_chars)
        
        # bigram
        for i in range(len(cn_chars) - 1):
            tokens.append(cn_chars[i] + cn_chars[i + 1])
        
        return tokens

    # ---------- 索引构建 ----------
    def build_index(self, documents: List[Dict[str, Any]]):
        """
        构建倒排索引
        
        Args:
            documents: 文档列表，每个文档包含：
                - doc_id: 文档 ID
                - text: 文本内容
                - metadata: 元数据（contract_type, risk_level, counterparty, date 等）
        """
        self._inverted_index = defaultdict(lambda: defaultdict(list))
        self._doc_index = {}
        self._doc_count = len(documents)
        
        total_len = 0
        
        for doc in documents:
            doc_id = doc['doc_id']
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            # 分词
            tokens = self._tokenize(text)
            total_len += len(tokens)
            
            # 记录文档信息
            self._doc_index[doc_id] = {
                'length': len(tokens),
                'metadata': metadata,
                'text_preview': text[:200],
            }
            
            # 构建倒排索引
            for pos, token in enumerate(tokens):
                self._inverted_index[token][doc_id].append(pos)
        
        if self._doc_count > 0:
            self._avg_doc_len = total_len / self._doc_count
        
        self._save_index()
        logger.info(f"索引构建完成: {self._doc_count} 篇文档, {len(self._inverted_index)} 个词项")

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """添加单篇文档到索引"""
        # 如果文档已存在，先删除
        if doc_id in self._doc_index:
            self.remove_document(doc_id)
        
        # 分词
        tokens = self._tokenize(text)
        
        # 更新文档索引
        self._doc_index[doc_id] = {
            'length': len(tokens),
            'metadata': metadata,
            'text_preview': text[:200],
        }
        self._doc_count += 1
        
        # 更新倒排索引
        for pos, token in enumerate(tokens):
            if doc_id not in self._inverted_index[token]:
                self._inverted_index[token][doc_id] = []
            self._inverted_index[token][doc_id].append(pos)
        
        # 更新平均文档长度
        total_len = sum(d['length'] for d in self._doc_index.values())
        self._avg_doc_len = total_len / self._doc_count if self._doc_count > 0 else 0
        
        self._save_index()

    def remove_document(self, doc_id: str):
        """从索引中删除文档"""
        if doc_id not in self._doc_index:
            return
        
        # 从倒排索引中删除
        for term in list(self._inverted_index.keys()):
            if doc_id in self._inverted_index[term]:
                del self._inverted_index[term][doc_id]
                if not self._inverted_index[term]:
                    del self._inverted_index[term]
        
        # 从文档索引中删除
        del self._doc_index[doc_id]
        self._doc_count -= 1
        
        # 更新平均文档长度
        if self._doc_count > 0:
            total_len = sum(d['length'] for d in self._doc_index.values())
            self._avg_doc_len = total_len / self._doc_count
        else:
            self._avg_doc_len = 0
        
        self._save_index()

    # ---------- TF-IDF 计算 ----------
    def _tf(self, term: str, doc_id: str) -> float:
        """计算词频（对数频率）"""
        if doc_id not in self._inverted_index.get(term, {}):
            return 0
        tf = len(self._inverted_index[term][doc_id])
        return 1 + math.log10(tf) if tf > 0 else 0

    def _idf(self, term: str) -> float:
        """计算逆文档频率"""
        df = len(self._inverted_index.get(term, {}))
        if df == 0:
            return 0
        return math.log10(self._doc_count / df)

    def _tf_idf(self, term: str, doc_id: str) -> float:
        """计算 TF-IDF"""
        return self._tf(term, doc_id) * self._idf(term)

    def _bm25(self, term: str, doc_id: str, k1: float = 1.5, b: float = 0.75) -> float:
        """
        计算 BM25 分数（比 TF-IDF 更精确）
        """
        if doc_id not in self._inverted_index.get(term, {}):
            return 0
        
        tf = len(self._inverted_index[term][doc_id])
        df = len(self._inverted_index.get(term, {}))
        
        if df == 0 or self._avg_doc_len == 0:
            return 0
        
        idf = math.log10((self._doc_count - df + 0.5) / (df + 0.5) + 1)
        doc_len = self._doc_index[doc_id]['length']
        
        score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / self._avg_doc_len))
        return score

    # ---------- 搜索 ----------
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        highlight: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        全文检索
        
        Args:
            query: 搜索关键词
            filters: 过滤条件
                - clause_type: 条款类型
                - risk_level: 风险等级
                - counterparty: 对方主体
                - date_from: 开始日期
                - date_to: 结束日期
            top_k: 返回结果数
            highlight: 是否高亮命中片段
            
        Returns:
            搜索结果列表
        """
        if not query.strip():
            return []
        
        # 分词
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        # 计算每个文档的 BM25 分数
        doc_scores: Dict[str, float] = defaultdict(float)
        
        for token in query_tokens:
            for doc_id in self._inverted_index.get(token, {}):
                doc_scores[doc_id] += self._bm25(token, doc_id)
        
        # 应用过滤
        filtered_results = []
        for doc_id, score in doc_scores.items():
            doc = self._doc_index.get(doc_id)
            if not doc:
                continue
            
            metadata = doc.get('metadata', {})
            
            # 过滤条件
            if filters:
                if filters.get('clause_type') and metadata.get('clause_type') != filters['clause_type']:
                    continue
                if filters.get('risk_level') and metadata.get('risk_level') != filters['risk_level']:
                    continue
                if filters.get('counterparty') and filters['counterparty'] not in metadata.get('counterparty', ''):
                    continue
                if filters.get('date_from') and metadata.get('date', '') < filters['date_from']:
                    continue
                if filters.get('date_to') and metadata.get('date', '') > filters['date_to']:
                    continue
            
            # 构建结果
            result = {
                'doc_id': doc_id,
                'score': round(score, 4),
                'metadata': metadata,
                'preview': doc.get('text_preview', ''),
            }
            
            # 高亮
            if highlight:
                result['highlight'] = self._highlight(doc.get('text_preview', ''), query_tokens)
            
            filtered_results.append(result)
        
        # 按分数排序
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        return filtered_results[:top_k]

    def _highlight(self, text: str, query_tokens: List[str], context: int = 30) -> str:
        """
        高亮命中片段
        
        Args:
            text: 原文
            query_tokens: 查询词
            context: 上下文长度
            
        Returns:
            高亮后的片段
        """
        if not text or not query_tokens:
            return text
        
        # 找到第一个匹配位置
        text_lower = text.lower()
        best_pos = -1
        
        for token in query_tokens:
            pos = text_lower.find(token)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
        
        if best_pos == -1:
            return text[:100] + "..."
        
        # 提取上下文
        start = max(0, best_pos - context)
        end = min(len(text), best_pos + len(query_tokens[0]) + context)
        
        snippet = text[start:end]
        
        # 高亮标记
        for token in query_tokens:
            snippet = snippet.replace(token, f"**{token}**")
            snippet = snippet.replace(token.lower(), f"**{token.lower()}**")
        
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        
        return prefix + snippet + suffix

    # ---------- 索引持久化 ----------
    def _save_index(self):
        """保存索引到磁盘"""
        # 保存倒排索引
        index_data = {
            term: dict(docs) for term, docs in self._inverted_index.items()
        }
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False)
        
        # 保存文档索引
        with open(self.doc_index_file, 'w', encoding='utf-8') as f:
            json.dump(self._doc_index, f, ensure_ascii=False, indent=2)
        
        # 保存元数据
        metadata = {
            'doc_count': self._doc_count,
            'avg_doc_len': self._avg_doc_len,
            'updated_at': datetime.now().isoformat(),
        }
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _load_index(self):
        """从磁盘加载索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._inverted_index = defaultdict(lambda: defaultdict(list), data)
            
            if self.doc_index_file.exists():
                with open(self.doc_index_file, 'r', encoding='utf-8') as f:
                    self._doc_index = json.load(f)
            
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                self._doc_count = metadata.get('doc_count', 0)
                self._avg_doc_len = metadata.get('avg_doc_len', 0)
            
            logger.debug(f"索引加载完成: {self._doc_count} 篇文档")
        except Exception as e:
            logger.warning(f"索引加载失败: {e}")
            self._inverted_index = defaultdict(lambda: defaultdict(list))
            self._doc_index = {}
            self._doc_count = 0
            self._avg_doc_len = 0

    # ---------- 统计信息 ----------
    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            'doc_count': self._doc_count,
            'term_count': len(self._inverted_index),
            'avg_doc_len': round(self._avg_doc_len, 2),
        }


# ---------- 便捷函数 ----------
_default_search: Optional[ArchiveSearch] = None


def get_search_engine() -> ArchiveSearch:
    """获取全局单例"""
    global _default_search
    if _default_search is None:
        _default_search = ArchiveSearch()
    return _default_search


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='档案库全文检索 v5.2')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # index 子命令
    index_parser = subparsers.add_parser('index', help='构建索引')
    index_parser.add_argument('--input', required=True, help='输入 JSON 文件路径')
    
    # search 子命令
    search_parser = subparsers.add_parser('search', help='搜索')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('--clause-type', help='按条款类型过滤')
    search_parser.add_argument('--risk-level', help='按风险等级过滤')
    search_parser.add_argument('--counterparty', help='按对方主体过滤')
    search_parser.add_argument('--top-k', type=int, default=10, help='返回结果数')
    
    # stats 子命令
    subparsers.add_parser('stats', help='索引统计')
    
    args = parser.parse_args()
    engine = get_search_engine()
    
    if args.command == 'index':
        with open(args.input, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        engine.build_index(documents)
        stats = engine.get_stats()
        print(f"✅ 索引构建完成: {stats['doc_count']} 篇, {stats['term_count']} 个词项")
    
    elif args.command == 'search':
        filters = {}
        if args.clause_type:
            filters['clause_type'] = args.clause_type
        if args.risk_level:
            filters['risk_level'] = args.risk_level
        if args.counterparty:
            filters['counterparty'] = args.counterparty
        
        results = engine.search(args.query, filters=filters, top_k=args.top_k)
        
        if not results:
            print("未找到匹配结果")
        else:
            print(f"找到 {len(results)} 个结果:")
            for r in results:
                print(f"\n  [{r['score']}] {r['doc_id']}")
                if r.get('highlight'):
                    print(f"     {r['highlight']}")
    
    elif args.command == 'stats':
        stats = engine.get_stats()
        print(f"文档数: {stats['doc_count']}")
        print(f"词项数: {stats['term_count']}")
        print(f"平均文档长度: {stats['avg_doc_len']}")
    
    else:
        parser.print_help()
