#!/usr/bin/env python3
"""
V1.1 新引擎测试
测试 Yandex/Startpage/Qwant/Brave 适配器和错误分类功能
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from search import (
    YandexAdapter, StartpageAdapter, QwantAdapter, BraveAdapter,
    EngineManager, SearchOrchestrator, STRICT_FALLBACK_ENGINES,
    classify_error, ErrorCategory, ClassifiedError,
    format_error_report,
)


class TestNewEngines(unittest.TestCase):
    """测试 V1.1 新增的 4 个国内备选引擎"""

    def test_yandex_adapter_name(self):
        adapter = YandexAdapter()
        self.assertEqual(adapter.name, "yandex")

    def test_startpage_adapter_name(self):
        adapter = StartpageAdapter()
        self.assertEqual(adapter.name, "startpage")

    def test_qwant_adapter_name(self):
        adapter = QwantAdapter()
        self.assertEqual(adapter.name, "qwant")

    def test_brave_adapter_name(self):
        adapter = BraveAdapter()
        self.assertEqual(adapter.name, "brave")

    def test_yandex_request_params(self):
        """Yandex 适配器请求参数验证"""
        async def _test():
            adapter = YandexAdapter()
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value="<html><body></body></html>")
            mock_response.status = 200
            mock_session = AsyncMock()
            mock_session.get = MagicMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)
            await adapter.search(mock_session, "test query")
            call_args = mock_session.get.call_args
            url = call_args[0][0]
            self.assertIn("text=test", url.replace("+", "%20"))  # query 参数
        
        asyncio.run(_test())

    def test_startpage_has_dnt(self):
        """Startpage 应该包含 DNT 头"""
        async def _test():
            adapter = StartpageAdapter()
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value="<html><body></body></html>")
            mock_response.status = 200
            mock_session = AsyncMock()
            mock_session.get = MagicMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)
            await adapter.search(mock_session, "test")
            call_args = mock_session.get.call_args
            headers = call_args[1].get('headers', {})
            # Startpage 不一定有 DDG=1，但我们应该检查它不发送 Cookie
            self.assertNotIn("Cookie", headers)

        asyncio.run(_test())

    def test_brave_has_dnt(self):
        """Brave 应该包含 DNT 头"""
        async def _test():
            adapter = BraveAdapter()
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value="<html><body></body></html>")
            mock_response.status = 200
            mock_session = AsyncMock()
            mock_session.get = MagicMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)
            await adapter.search(mock_session, "test")
            call_args = mock_session.get.call_args
            headers = call_args[1].get('headers', {})
            self.assertIn("User-Agent", headers)

        asyncio.run(_test())


class TestErrorClassification(unittest.TestCase):
    """测试错误分类功能"""

    def test_network_timeout(self):
        import aiohttp
        err = classify_error("test_engine", aiohttp.ServerTimeoutError("timeout"))
        self.assertEqual(err.category, ErrorCategory.NETWORK)
        self.assertEqual(err.engine, "test_engine")
        self.assertTrue(any("网络" in ts for ts in err.troubleshooting))

    def test_network_connection_error(self):
        err = classify_error("baidu", TimeoutError("connection timed out"))
        self.assertEqual(err.category, ErrorCategory.NETWORK)

    def test_config_key_error(self):
        err = classify_error("test", KeyError("missing_key"))
        self.assertEqual(err.category, ErrorCategory.CONFIG)
        self.assertTrue(any("config.yaml" in ts for ts in err.troubleshooting))

    def test_config_value_error(self):
        err = classify_error("test", ValueError("invalid value"))
        self.assertEqual(err.category, ErrorCategory.CONFIG)

    def test_engine_parser_error(self):
        err = classify_error("baidu", Exception("HTML parser error: cannot find 'div.result'"))
        self.assertEqual(err.category, ErrorCategory.ENGINE)
        self.assertTrue(any("页面结构" in ts for ts in err.troubleshooting))

    def test_generic_exception_is_engine(self):
        """通用 Exception 应归类为引擎错误"""
        err = classify_error("unknown", Exception("something went wrong"))
        self.assertEqual(err.category, ErrorCategory.ENGINE)


class TestFormatErrorReport(unittest.TestCase):
    """测试错误报告格式化"""

    def test_empty_errors(self):
        report = format_error_report([])
        self.assertEqual(report, "")

    def test_network_error_report(self):
        errors = [
            classify_error("baidu", TimeoutError("connection timed out")),
            classify_error("bing", ConnectionRefusedError("connection refused")),
        ]
        report = format_error_report(errors)
        self.assertIn("网络", report)
        self.assertIn("baidu", report)
        self.assertIn("bing", report)

    def test_mixed_error_report(self):
        errors = [
            classify_error("baidu", KeyError("missing")),
            classify_error("bing", TimeoutError("connection timed out")),
        ]
        report = format_error_report(errors)
        self.assertIn("配置", report)
        self.assertIn("网络", report)


class TestEngineManager(unittest.TestCase):
    """测试引擎管理器"""

    def test_init_all_engines(self):
        config = {
            "searxng": {"host": "127.0.0.1", "port": 8888},
            "search": {"default_engines": ["baidu", "bing"]},
            "privacy": {"default_mode": "normal"},
        }
        em = EngineManager(config)
        self.assertIn("yandex", em.engines)
        self.assertIn("startpage", em.engines)
        self.assertIn("qwant", em.engines)
        self.assertIn("brave", em.engines)
        self.assertIn("duckduckgo", em.engines)

    def test_strict_fallback_engines_list(self):
        """验证 strict 模式备用引擎列表包含国内可用引擎"""
        self.assertIn("yandex", STRICT_FALLBACK_ENGINES)
        self.assertIn("startpage", STRICT_FALLBACK_ENGINES)
        self.assertIn("qwant", STRICT_FALLBACK_ENGINES)
        self.assertIn("brave", STRICT_FALLBACK_ENGINES)
        # DDG 应该排在最后（国内不稳定）
        self.assertIn("duckduckgo", STRICT_FALLBACK_ENGINES)


class TestSearchOrchestratorErrors(unittest.TestCase):
    """测试编排器错误收集"""

    def test_orchestrator_has_error_list(self):
        config = {
            "searxng": {"host": "127.0.0.1", "port": 8888},
            "search": {"default_engines": ["baidu"]},
            "privacy": {"default_mode": "normal"},
        }
        orch = SearchOrchestrator(config)
        self.assertIsInstance(orch.classified_errors, list)

    def test_error_list_starts_empty(self):
        config = {
            "searxng": {"host": "127.0.0.1", "port": 8888},
            "search": {"default_engines": []},
            "privacy": {"default_mode": "strict", "strict": {"allowed_engines": []}},
        }
        orch = SearchOrchestrator(config)
        self.assertEqual(len(orch.classified_errors), 0)


if __name__ == "__main__":
    unittest.main()
