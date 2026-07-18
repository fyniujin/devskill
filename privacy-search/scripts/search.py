#!/usr/bin/env python3
"""
F1: 多引擎并行搜索模块
- asyncio + aiohttp 并发请求 6+ 搜索引擎
- BeautifulSoup 解析 HTML 结果
- SimHash 去重（汉明距离 ≤ 3）
- 多引擎交叉验证排序
- 超时控制 + 请求频率限制
"""

import asyncio
import hashlib
import random
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

import aiohttp
import yaml
from bs4 import BeautifulSoup

# ============================================================
# 数据结构
# ============================================================

@dataclass
class SearchResult:
    """单条搜索结果"""
    title: str
    url: str
    snippet: str
    engine: str
    rank: int = 0
    simhash: Optional[int] = None

    def compute_simhash(self) -> int:
        """计算 SimHash（基于 title + snippet 的前 128 字符）"""
        text = f"{self.title} {self.snippet}"[:128].lower()
        # 简化版 SimHash：基于字符 n-gram
        ngrams = [text[i:i+3] for i in range(len(text) - 2)]
        hashes = [int(hashlib.md5(g.encode()).hexdigest(), 16) for g in ngrams]
        if not hashes:
            self.simhash = 0
            return 0
        # 合并 hash
        combined = 0
        for h in hashes:
            combined ^= h
        self.simhash = combined & ((1 << 64) - 1)
        return self.simhash


@dataclass
class SearchResponse:
    """搜索响应"""
    engine: str
    results: List[SearchResult] = field(default_factory=list)
    error: Optional[str] = None
    elapsed: float = 0.0


# ============================================================
# 搜索引擎适配器
# ============================================================

class EngineAdapter:
    """搜索引擎适配器基类"""

    def __init__(self, name: str, timeout: int = 10):
        self.name = name
        self.timeout = timeout

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        raise NotImplementedError

    def parse(self, html: str, num: int) -> List[SearchResult]:
        raise NotImplementedError


class BaiduAdapter(EngineAdapter):
    """百度搜索引擎"""

    def __init__(self):
        super().__init__("baidu", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://www.baidu.com/s?wd={quote(query)}&rn={num}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        start = time.time()
        try:
            async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                html = await resp.text()
                results = self.parse(html, num)
                return SearchResponse(engine=self.name, results=results, elapsed=time.time() - start)
        except Exception as e:
            return SearchResponse(engine=self.name, error=str(e), elapsed=time.time() - start)

    def parse(self, html: str, num: int) -> List[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        for idx, item in enumerate(soup.select("div.result")[:num]):
            title_el = item.select_one("h3 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("div.c-abstract, div.content-right_8Zs40, span.content-right_8Zs40")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class BingAdapter(EngineAdapter):
    """必应搜索引擎"""

    def __init__(self):
        super().__init__("bing", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://cn.bing.com/search?q={quote(query)}&count={num}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        start = time.time()
        try:
            async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                html = await resp.text()
                results = self.parse(html, num)
                return SearchResponse(engine=self.name, results=results, elapsed=time.time() - start)
        except Exception as e:
            return SearchResponse(engine=self.name, error=str(e), elapsed=time.time() - start)

    def parse(self, html: str, num: int) -> List[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        for idx, item in enumerate(soup.select("li.b_algo")[:num]):
            title_el = item.select_one("h2 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("p")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class DuckDuckGoAdapter(EngineAdapter):
    """DuckDuckGo 搜索引擎（隐私优先）"""

    def __init__(self):
        super().__init__("duckduckgo", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "DNT": "1",
        }
        start = time.time()
        try:
            async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                html = await resp.text()
                results = self.parse(html, num)
                return SearchResponse(engine=self.name, results=results, elapsed=time.time() - start)
        except Exception as e:
            return SearchResponse(engine=self.name, error=str(e), elapsed=time.time() - start)

    def parse(self, html: str, num: int) -> List[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        for idx, item in enumerate(soup.select("div.result")[:num]):
            title_el = item.select_one("a.result__a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("a.result__snippet")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class SogouAdapter(EngineAdapter):
    """搜狗搜索引擎"""

    def __init__(self):
        super().__init__("sogou", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://www.sogou.com/web?query={quote(query)}&ie=utf8"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        start = time.time()
        try:
            async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                html = await resp.text()
                results = self.parse(html, num)
                return SearchResponse(engine=self.name, results=results, elapsed=time.time() - start)
        except Exception as e:
            return SearchResponse(engine=self.name, error=str(e), elapsed=time.time() - start)

    def parse(self, html: str, num: int) -> List[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        for idx, item in enumerate(soup.select("div.vrwrap")[:num]):
            title_el = item.select_one("h3 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("p.str_info, div.str_info")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class So360Adapter(EngineAdapter):
    """360 搜索引擎"""

    def __init__(self):
        super().__init__("360", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://www.so.com/s?q={quote(query)}&ie=utf-8"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        start = time.time()
        try:
            async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                html = await resp.text()
                results = self.parse(html, num)
                return SearchResponse(engine=self.name, results=results, elapsed=time.time() - start)
        except Exception as e:
            return SearchResponse(engine=self.name, error=str(e), elapsed=time.time() - start)

    def parse(self, html: str, num: int) -> List[SearchResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        for idx, item in enumerate(soup.select("li.res-list")[:num]):
            title_el = item.select_one("h3 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("p.res-desc")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class SearXNGAdapter(EngineAdapter):
    """本地 SearXNG 实例"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        super().__init__("searxng", timeout=10)
        self.base_url = f"http://{host}:{port}"

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"{self.base_url}/search?q={quote(query)}&format=json&pageno=1"
        start = time.time()
        try:
            async with session.get(url, timeout=self.timeout) as resp:
                if resp.status != 200:
                    return SearchResponse(engine=self.name, error=f"HTTP {resp.status}", elapsed=time.time() - start)
                data = await resp.json()
                results = self.parse(data, num)
                return SearchResponse(engine=self.name, results=results, elapsed=time.time() - start)
        except Exception as e:
            return SearchResponse(engine=self.name, error=str(e), elapsed=time.time() - start)

    def parse(self, data: dict, num: int) -> List[SearchResult]:
        results = []
        for idx, item in enumerate(data.get("results", [])[:num]):
            title = item.get("title", "")
            url = item.get("url", "")
            snippet = item.get("content", "")
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


# ============================================================
# SimHash 去重
# ============================================================

def hamming_distance(a: int, b: int) -> int:
    """计算两个 64 位整数的汉明距离"""
    x = a ^ b
    distance = 0
    while x:
        distance += 1
        x &= x - 1
    return distance


def deduplicate_results(results: List[SearchResult], threshold: int = 3) -> List[SearchResult]:
    """
    SimHash 去重
    - 汉明距离 ≤ threshold 视为重复
    - 保留摘要最长的版本
    """
    if not results:
        return []

    # 计算每条结果的 simhash
    for r in results:
        r.compute_simhash()

    # 按 simhash 分组
    unique: List[SearchResult] = []
    seen_hashes: List[Tuple[int, SearchResult]] = []

    for r in results:
        is_dup = False
        for h, existing in seen_hashes:
            if r.simhash is not None and h is not None and hamming_distance(r.simhash, h) <= threshold:
                # 重复，保留摘要更长的
                if len(r.snippet) > len(existing.snippet):
                    existing.snippet = r.snippet
                    existing.title = r.title if len(r.title) > len(existing.title) else existing.title
                is_dup = True
                break
        if not is_dup:
            unique.append(r)
            seen_hashes.append((r.simhash, r))

    return unique


# ============================================================
# 交叉验证排序
# ============================================================

def cross_engine_rank(results: List[SearchResult]) -> List[SearchResult]:
    """
    多引擎交叉验证排序
    - 出现在越多引擎的结果排名越靠前
    - 同引擎内按原始排名加权
    """
    # 按 URL 聚合
    url_map: Dict[str, List[SearchResult]] = defaultdict(list)
    for r in results:
        url_map[r.url].append(r)

    # 计算综合得分
    scored: List[Tuple[float, SearchResult]] = []
    for url, items in url_map.items():
        engine_count = len(set(item.engine for item in items))
        # 最佳排名（越小越好）
        best_rank = min(item.rank for item in items)
        # 综合分 = 引擎覆盖数 * 10 - 最佳排名
        score = engine_count * 10 - best_rank
        # 取摘要最长的作为代表
        representative = max(items, key=lambda x: len(x.snippet))
        scored.append((score, representative))

    # 按得分降序排列
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ============================================================
# 搜索编排器
# ============================================================

class SearchOrchestrator:
    """搜索编排器：并发调度 + 去重 + 排序"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engines: Dict[str, EngineAdapter] = {}
        self._init_engines()
        # 请求频率控制
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._last_reset = datetime.now()

    def _init_engines(self):
        """初始化引擎适配器"""
        engine_map = {
            "baidu": BaiduAdapter,
            "bing": BingAdapter,
            "sogou": SogouAdapter,
            "360": So360Adapter,
            "duckduckgo": DuckDuckGoAdapter,
            "searxng": lambda: SearXNGAdapter(
                host=self.config.get("searxng", {}).get("host", "127.0.0.1"),
                port=self.config.get("searxng", {}).get("port", 8888),
            ),
        }
        for name, cls in engine_map.items():
            try:
                self.engines[name] = cls()
            except Exception:
                pass

    def _check_rate_limit(self, engine_name: str) -> bool:
        """检查是否超过日请求上限"""
        # 每日重置
        if datetime.now() - self._last_reset > timedelta(days=1):
            self._request_counts.clear()
            self._last_reset = datetime.now()
        limit = self.config.get("search", {}).get("daily_request_limit", 200)
        return self._request_counts[engine_name] < limit

    async def search(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        num: int = 10,
        privacy_mode: str = "normal",
    ) -> List[SearchResult]:
        """
        执行多引擎并行搜索

        Args:
            query: 搜索关键词
            engines: 指定引擎列表（None 使用配置默认）
            num: 每个引擎返回结果数
            privacy_mode: normal | strict

        Returns:
            去重排序后的结果列表
        """
        # 确定引擎列表
        if engines is None:
            if privacy_mode == "strict":
                engines = self.config.get("privacy", {}).get("strict", {}).get("allowed_engines", ["duckduckgo", "searxng"])
            else:
                engines = self.config.get("search", {}).get("default_engines", list(self.engines.keys()))

        # 过滤可用引擎
        active_engines = [name for name in engines if name in self.engines and self._check_rate_limit(name)]

        if not active_engines:
            return []

        # 并发请求
        timeout = self.config.get("search", {}).get("timeout", 10)
        connector = aiohttp.TCPConnector(limit=self.config.get("search", {}).get("max_concurrent", 6))

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for name in active_engines:
                adapter = self.engines[name]
                # 请求间隔随机化
                delay = random.uniform(
                    self.config.get("search", {}).get("request_delay_min", 1.0),
                    self.config.get("search", {}).get("request_delay_max", 5.0),
                )
                tasks.append(self._search_with_delay(adapter, session, query, num, delay))

            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集结果
        all_results: List[SearchResult] = []
        for resp in responses:
            if isinstance(resp, Exception):
                continue
            if resp.error:
                continue
            all_results.extend(resp.results)
            self._request_counts[resp.engine] += 1

        # 去重
        unique = deduplicate_results(all_results)

        # 排序
        ranked = cross_engine_rank(unique)

        return ranked

    async def _search_with_delay(
        self,
        adapter: EngineAdapter,
        session: aiohttp.ClientSession,
        query: str,
        num: int,
        delay: float,
    ) -> SearchResponse:
        """带随机延迟的搜索请求"""
        await asyncio.sleep(delay)
        return await adapter.search(session, query, num)


# ============================================================
# CLI 入口
# ============================================================

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def main():
    """CLI 入口"""
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(description="隐私搜索 - 多引擎并行搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--engines", help="指定引擎，逗号分隔 (baidu,bing,sogou,360,duckduckgo,searxng)")
    parser.add_argument("--num", type=int, default=10, help="每个引擎返回结果数")
    parser.add_argument("--privacy", choices=["normal", "strict"], default="normal", help="隐私模式")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)

    # 解析引擎列表
    engines = None
    if args.engines:
        engines = [e.strip() for e in args.engines.split(",")]

    # 执行搜索
    orchestrator = SearchOrchestrator(config)
    results = asyncio.run(orchestrator.search(
        query=args.query,
        engines=engines,
        num=args.num,
        privacy_mode=args.privacy,
    ))

    # 输出结果
    if args.json:
        import json
        output = [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "engine": r.engine,
            }
            for r in results
        ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n🔍 搜索: {args.query} | 模式: {args.privacy} | 结果: {len(results)} 条\n")
        for idx, r in enumerate(results, 1):
            print(f"[{idx}] {r.title}")
            print(f"    {r.url}")
            print(f"    {r.snippet[:100]}...")
            print(f"    — {r.engine}")
            print()


if __name__ == "__main__":
    import os
    main()
