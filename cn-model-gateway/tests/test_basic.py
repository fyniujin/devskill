"""Basic smoke tests."""
from __future__ import annotations

import sys
import os
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.adapters.base import ChatMessage, BaseAdapter, ChatResponse, ContentChunk
from src.router import ModelRouter, ERROR_PARAM_INVALID, ERROR_RATE_LIMITED, ERROR_INTERNAL
from src.monitor import get_hardware_info, compute_concurrency_limit, Monitor
from src.mcp_server import MCPServer


class TestChatMessage(unittest.TestCase):
    def test_to_dict(self):
        m = ChatMessage(role="user", content="hello")
        self.assertEqual(m.to_dict(), {"role": "user", "content": "hello"})

    def test_content_chunk(self):
        c = ContentChunk(type="text", text="hi")
        self.assertEqual(c.to_dict(), {"type": "text", "text": "hi"})

    def test_chat_response(self):
        r = ChatResponse(content="hi", model="m", provider="p")
        self.assertEqual(r.content, "hi")
        self.assertEqual(r.duration_ms, 0)


class TestRouter(unittest.TestCase):
    def test_register_empty_config(self):
        router = ModelRouter()
        result = router.register_all({})
        # All providers should be False when no config
        self.assertIn("deepseek", result)
        self.assertFalse(result["deepseek"])
        self.assertEqual(len(result), 6)

    def test_auto_select_no_providers(self):
        router = ModelRouter()
        self.assertIsNone(router.auto_select())

    def test_list_available_empty(self):
        router = ModelRouter()
        self.assertEqual(router.list_available(), [])

    def test_error_mapping_invalid_key(self):
        router = ModelRouter()
        err = router._map_error("deepseek", "Error: invalid_api_key")
        self.assertIn("-32602", str(err))

    def test_error_mapping_rate_limit(self):
        router = ModelRouter()
        err = router._map_error("tongyi", "Throttling.RateLimit exceeded")
        self.assertIn("-32002", str(err))


class TestHardware(unittest.TestCase):
    def test_get_hardware_info(self):
        info = get_hardware_info()
        self.assertIn("cpu_cores", info)
        self.assertIn("memory_mb", info)
        self.assertIsInstance(info["cpu_cores"], int)

    def test_compute_concurrency_low_mem(self):
        limit = compute_concurrency_limit({"cpu_cores": 8, "memory_mb": 2048})
        self.assertEqual(limit, 1)

    def test_compute_concurrency_normal(self):
        limit = compute_concurrency_limit({"cpu_cores": 8, "memory_mb": 16384})
        self.assertGreaterEqual(limit, 1)
        self.assertLessEqual(limit, 4)


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()
        self.monitor = Monitor()
        self.server = MCPServer(self.router, self.monitor)

    def test_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 1)
        self.assertIn("result", resp)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "cn-model-gateway")

    def test_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = self.server.handle_request(req)
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("ask_model", tool_names)
        self.assertIn("compare_models", tool_names)
        self.assertIn("list_providers", tool_names)

    def test_resources_list(self):
        req = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
        resp = self.server.handle_request(req)
        uris = [r["uri"] for r in resp["result"]["resources"]]
        self.assertIn("cn-model-gateway://config", uris)

    def test_prompts_list(self):
        req = {"jsonrpc": "2.0", "id": 4, "method": "prompts/list", "params": {}}
        resp = self.server.handle_request(req)
        names = [p["name"] for p in resp["result"]["prompts"]]
        self.assertIn("code_review", names)
        self.assertIn("translate", names)

    def test_unknown_method(self):
        req = {"jsonrpc": "2.0", "id": 5, "method": "foo/bar", "params": {}}
        resp = self.server.handle_request(req)
        self.assertIn("error", resp)

    def test_tool_list_providers_empty(self):
        req = {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
               "params": {"name": "list_providers", "arguments": {}}}
        resp = self.server.handle_request(req)
        self.assertIn("result", resp)


if __name__ == "__main__":
    unittest.main()
