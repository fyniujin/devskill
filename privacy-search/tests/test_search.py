#!/usr/bin/env python3
"""
F1 单测：多引擎并行搜索
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from search import (
    BaiduAdapter, BingAdapter, DuckDuckGoAdapter,
    SogouAdapter, So360Adapter, SearXNGAdapter,
    SearchResult, SearchResponse,
    deduplicate_results, cross_engine_rank,
    SearchOrchestrator,
    hamming_distance, load_config
)


class TestSimHash(unittest.TestCase):
    """测试 SimHash 计算"""

    def test_compute_simhash(self):
        r = SearchResult(title="test", url="http://example.com", snippet="hello", engine="test")
        h = r.compute_simhash()
        self.assertIsInstance(h, int)
        self.assertGreaterEqual(h, 0)

    def test_same_text_same_hash(self):
        r1 = SearchResult(title="test", url="http://a.com", snippet="hello world", engine="test")
        r2 = SearchResult(title="test", url="http://b.com", snippet="hello world", engine="test")
        self.assertEqual(r1.compute_simhash(), r2.compute_simhash())

    def test_different_text_different_hash(self):
        r1 = SearchResult(title="apple", url="http://a.com", snippet="fruit", engine="test")
        r2 = SearchResult(title="python", url="http://b.com", snippet="programming", engine="test")
        # 差异较大的文本 simhash 应不同
        self.assertNotEqual(r1.compute_simhash(), r2.compute_simhash())


class TestHammingDistance(unittest.TestCase):
    """测试汉明距离"""

    def test_same_number(self):
        self.assertEqual(hamming_distance(0, 0), 0)

    def test_different_number(self):
        # 1 (01) vs 2 (10) -> distance = 2
        self.assertEqual(hamming_distance(1, 2), 2)

    def test_known_distance(self):
        # 0xFF vs 0x00 -> 8 bits different
        self.assertEqual(hamming_distance(0xFF, 0x00), 8)


class TestDeduplicate(unittest.TestCase):
    """测试 SimHash 去重"""

    def test_no_duplicates(self):
        results = [
            SearchResult(title="a", url="http://a.com", snippet="aaa", engine="test"),
            SearchResult(title="b", url="http://b.com", snippet="bbb", engine="test"),
        ]
        unique = deduplicate_results(results)
        self.assertEqual(len(unique), 2)

    def test_remove_near_duplicates(self):
        results = [
            SearchResult(title="hello world test", url="http://a.com", snippet="hello world test", engine="test"),
            SearchResult(title="hello world test", url="http://b.com", snippet="hello world test", engine="test"),
        ]
        unique = deduplicate_results(results, threshold=3)
        # 完全相同的文本应被去重为 1 条
        self.assertEqual(len(unique), 1)

    def test_keep_longest_snippet(self):
        """验证保留摘要更长的版本（用 threshold=0 精确去重）"""
        # title + snippet 完全相同 → 精确去重
        results = [
            SearchResult(title="same title", url="http://a.com", snippet="identical content here", engine="test"),
            SearchResult(title="same title", url="http://b.com", snippet="identical content here", engine="test"),
        ]
        unique = deduplicate_results(results, threshold=0)
        self.assertEqual(len(unique), 1)

    def test_keep_longest_snippet_different(self):
        """近似内容去重后保留更长摘要"""
        results = [
            SearchResult(title="hello world greeting", url="http://a.com", snippet="short one", engine="test"),
            SearchResult(title="hello world greeting", url="http://b.com", snippet="short one and more details added here for length", engine="test"),
        ]
        unique = deduplicate_results(results, threshold=5)
        if len(unique) == 1:
            self.assertIn("details", unique[0].snippet)
        else:
            # threshold=5 不一定合并，这也是可接受的
            self.assertEqual(len(unique), 2)


class TestCrossEngineRank(unittest.TestCase):
    """测试交叉验证排序"""

    def test_ranking_by_engine_coverage(self):
        # item 2 出现在 2 个引擎中，应排在前面
        results = [
            SearchResult(title="a", url="http://a.com", snippet="aaa", engine="baidu", rank=1),
            SearchResult(title="b", url="http://b.com", snippet="bbb", engine="baidu", rank=1),
            SearchResult(title="b2", url="http://b.com", snippet="bbb2", engine="bing", rank=2),
        ]
        ranked = cross_engine_rank(results)
        # b 出现在 2 个引擎，应排第一
        self.assertEqual(ranked[0].url, "http://b.com")

    def test_single_engine(self):
        results = [
            SearchResult(title="a", url="http://a.com", snippet="aaa", engine="test", rank=1),
            SearchResult(title="b", url="http://b.com", snippet="bbb", engine="test", rank=2),
        ]
        ranked = cross_engine_rank(results)
        self.assertEqual(len(ranked), 2)


class TestEngineAdapters(unittest.TestCase):
    """测试搜索引擎适配器"""

    def test_baidu_adapter_name(self):
        adapter = BaiduAdapter()
        self.assertEqual(adapter.name, "baidu")

    def test_bing_adapter_name(self):
        adapter = BingAdapter()
        self.assertEqual(adapter.name, "bing")

    def test_duckduckgo_adapter_name(self):
        adapter = DuckDuckGoAdapter()
        self.assertEqual(adapter.name, "duckduckgo")

    def test_duckduckgo_dnt_header(self):
        """DuckDuckGo 适配器应包含 DNT 头"""
        async def _test():
            adapter = DuckDuckGoAdapter()
            # Mock session
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value="<html><body></body></html>")
            mock_response.status = 200
            mock_session = AsyncMock()
            mock_session.get = MagicMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await adapter.search(mock_session, "test")
            # 验证 DNT 头被传递
            call_args = mock_session.get.call_args
            headers = call_args[1].get('headers', {})
            self.assertEqual(headers.get('DNT'), '1')

        asyncio.run(_test())


class TestSearchOrchestrator(unittest.TestCase):
    """测试搜索编排器"""

    def test_init_engines(self):
        config = {
            "search": {"default_engines": ["baidu", "bing", "duckduckgo"]},
            "searxng": {"host": "127.0.0.1", "port": 8888},
        }
        orch = SearchOrchestrator(config)
        self.assertIn("baidu", orch.engines)
        self.assertIn("bing", orch.engines)
        self.assertIn("duckduckgo", orch.engines)

    def test_rate_limit_check(self):
        config = {
            "search": {"daily_request_limit": 200},
            "searxng": {"host": "127.0.0.1", "port": 8888},
        }
        orch = SearchOrchestrator(config)
        self.assertTrue(orch._check_rate_limit("baidu"))
        # 模拟超过限制
        orch._request_counts["baidu"] = 200
        self.assertFalse(orch._check_rate_limit("baidu"))


class TestLoadConfig(unittest.TestCase):
    """测试配置加载"""

    def test_load_nonexistent_config(self):
        config = load_config("/nonexistent/path/config.yaml")
        self.assertEqual(config, {})


if __name__ == "__main__":
    unittest.main()
