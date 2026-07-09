#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线测试（无需任何厂商密钥）。

覆盖：模型注册表解析、任务分类、路由决策、成本计算、硬件档位、语义缓存、更新检查。
运行：python tests/test_router.py   （在技能根目录执行）
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))

import classifier
import cost_tracker
import hardware
import cache
import yaml_simple
import update_check
import router
import report


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = router.load_registry()

    def test_load_providers(self):
        provs = self.reg.get("providers", {})
        self.assertIn("deepseek", provs)
        self.assertIn("qwen", provs)
        self.assertIn("glm", provs)
        self.assertIn("kimi", provs)
        self.assertIn("hunyuan", provs)
        self.assertIn("doubao", provs)
        self.assertIn("ernie", provs)
        self.assertIn("spark", provs)

    def test_model_fields(self):
        m = self.reg["providers"]["deepseek"]["models"][0]
        self.assertEqual(m["name"], "deepseek-chat")
        self.assertIsInstance(m["ctx"], int)
        self.assertIn("price_in", m)


class TestClassifier(unittest.TestCase):
    def test_code(self):
        c = classifier.classify("帮我用 Python 写一个快速排序函数")
        self.assertEqual(c["task_type"], "code")

    def test_reason(self):
        c = classifier.classify("为什么天空是蓝色的？请分析其物理原理")
        self.assertTrue(c["needs_reasoning"])

    def test_long(self):
        big = "长文内容。" * 20000
        c = classifier.classify(big)
        self.assertEqual(c["length_bucket"], "long")

    def test_translate(self):
        c = classifier.classify("把这段话翻译成英文")
        self.assertEqual(c["task_type"], "translate")

    def test_hint_override(self):
        c = classifier.classify("随便聊聊", task_hint="reason")
        self.assertEqual(c["task_type"], "reason")


class TestResolve(unittest.TestCase):
    def setUp(self):
        self.reg = router.load_registry()
        # 让 deepseek 成为「已配置」厂商
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-dummy"

    def tearDown(self):
        os.environ.pop("DEEPSEEK_API_KEY", None)

    def test_cheap(self):
        p, m, reason = router.resolve("cheap", classifier.classify("hello"), self.reg)
        self.assertEqual(p, "deepseek")
        self.assertEqual(m, "deepseek-chat")  # 比 reasoner 便宜

    def test_quality(self):
        p, m, reason = router.resolve("quality", classifier.classify("hello"), self.reg)
        self.assertEqual(p, "deepseek")
        self.assertEqual(m, "deepseek-reasoner")  # 带 reasoner，能力最强

    def test_auto_reason(self):
        cls = classifier.classify("请推导并证明勾股定理")
        p, m, _ = router.resolve("auto", cls, self.reg)
        self.assertEqual(m, "deepseek-reasoner")

    def test_no_config_raises(self):
        os.environ.pop("DEEPSEEK_API_KEY", None)
        with self.assertRaises(router.AdapterError):
            router.resolve("auto", classifier.classify("hi"), self.reg)


class TestCost(unittest.TestCase):
    def test_compute(self):
        price = {"in": 1, "out": 2}
        cost = cost_tracker.compute_cost(price, 1_000_000, 1_000_000)
        self.assertAlmostEqual(cost, 3.0, places=4)

    def test_zero_price(self):
        self.assertEqual(cost_tracker.compute_cost(None, 100, 100), 0.0)


class TestHardware(unittest.TestCase):
    def test_profile(self):
        p = hardware.profile()
        self.assertIn(p["tier"], ("low", "mid", "high"))
        self.assertGreaterEqual(p["max_concurrency"], 1)
        self.assertGreaterEqual(p["batch_size"], 1)

    def test_recommend(self):
        n = hardware.recommend_subtasks(100)
        self.assertLessEqual(n, hardware.profile()["max_concurrency"])


class TestCache(unittest.TestCase):
    _db = os.path.join(tempfile.gettempdir(), "cnllm_test_cache.db")

    def setUp(self):
        if os.path.exists(self._db):
            os.remove(self._db)

    def test_roundtrip(self):
        cache.put("测试问题A", "deepseek", "deepseek-chat", "答案A", db_path=self._db)
        hit = cache.get("测试问题A", db_path=self._db)
        self.assertIsNotNone(hit)
        self.assertEqual(hit[2], "答案A")

    def test_miss(self):
        self.assertIsNone(cache.get("不存在的问题", db_path=self._db))


class TestUpdateCheck(unittest.TestCase):
    def test_offline_safe(self):
        # 不抛异常；无 update_url 时返回稳定结果
        has_update, latest, msg = update_check.run("1.0.0", "", "")
        self.assertIsInstance(has_update, bool)
        self.assertEqual(latest, "1.0.0")


class TestReport(unittest.TestCase):
    def test_html_escape(self):
        # 厂商名/周期若含 HTML 特殊字符，必须被转义，不能注入到导出报表
        import tempfile
        agg = {
            "period": "<b>month</b>",
            "total_cost": 0.0, "total_calls": 1, "success_rate": 100.0,
            "p95_ms": 1, "total_in": 0, "total_out": 0,
            "by_provider": {"<img src=x onerror=alert(1)>": {"cost": 0.0, "calls": 1, "in": 0, "out": 0}},
        }
        path = os.path.join(tempfile.gettempdir(), "cnllm_test_report.html")
        report.render_html(agg, path)
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        os.remove(path)
        self.assertIn("&lt;img src=x", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;b&gt;month&lt;/b&gt;", html)


class TestAdapters(unittest.TestCase):
    def test_unknown_adapter_raises(self):
        # 未知 adapter 类型必须抛中文 AdapterError，绝不该 traceback
        with self.assertRaises(router.AdapterError):
            router.build("no_such_adapter", {})


class TestSuggestMode(unittest.TestCase):
    def setUp(self):
        self.reg = router.load_registry()
        # 清空所有厂商密钥，模拟「未配置」环境
        for k in ("DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "ZHIPU_API_KEY",
                  "MOONSHOT_API_KEY", "HUNYUAN_API_KEY", "ARK_API_KEY",
                  "ERNIE_OPENAI_KEY", "ERNIE_API_KEY", "ERNIE_SECRET_KEY",
                  "SPARK_APP_ID", "SPARK_API_KEY", "SPARK_API_SECRET"):
            os.environ.pop(k, None)

    def test_suggest_without_key(self):
        # 无密钥时，allow_unconfigured 应给出基于注册表的合法推荐路由
        cls = classifier.classify("随便聊聊")
        p, m, reason = router.resolve("auto", cls, self.reg, allow_unconfigured=True)
        self.assertIn(p, self.reg["providers"])
        names = [x["name"] for x in self.reg["providers"][p]["models"]]
        self.assertIn(m, names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
