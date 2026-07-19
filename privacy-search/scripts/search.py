#!/usr/bin/env python3
"""
F1: 多引擎并行搜索模块
- asyncio + aiohttp 并发请求 6+ 搜索引擎
- BeautifulSoup 解析 HTML 结果
- SimHash 去重（汉明距离 ≤ 3）
- 多引擎交叉验证排序
- 超时控制 + 请求频率限制
- 错误分类：网络错误、配置错误、引擎错误
- 国内可用备选引擎：Yandex/Startpage/Qwant/Brave/Ecosia/Kagi
"""

import asyncio
import hashlib
import random
import re
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

import aiohttp
import yaml
from bs4 import BeautifulSoup


# ============================================================
# 错误分类
# ============================================================

class ErrorCategory(str, Enum):
    """错误分类"""
    NETWORK = "network"
    CONFIG = "config"
    ENGINE = "engine"


@dataclass
class ClassifiedError:
    """分类错误信息"""
    category: ErrorCategory
    engine: str
    message: str
    troubleshooting: List[str]
    exception: Optional[Exception] = None


def classify_error(engine: str, exception: Exception) -> ClassifiedError:
    """
    将统一的 Exception 分类为 network/config/engine

    Error categorization principles:
    - NetworkError → network (timeout, connection refused, DNS failure, SSL error, proxy error)
    - ConfigError → config (missing/invalid config key, invalid engine name)
    - ParserError → engine (HTML parsing failure, response format changed)
    """
    # Network errors
    network_exceptions = (
        aiohttp.ClientConnectorError,
        aiohttp.ServerDisconnectedError,
        aiohttp.ClientOSError,
        TimeoutError,
        ConnectionRefusedError,
    )

    # Config errors
    config_exceptions = (
        KeyError,
        ValueError,
    )

    # Check network errors first
    if isinstance(exception, network_exceptions):
        msg = str(exception).lower()
        if "timeout" in msg or "timed out" in msg:
            troubleshooting = [
                f"  1. 检查网络连接是否正常（ping www.baidu.com）",
                f"  2. 确认网络环境不受限制（特定网络可能阻止访问某些引擎）",
                f"  3. 增加超时时间：修改 config.yaml 中 search.timeout",
                f"  4. 检查代理/VPN 设置是否正确",
            ]
        elif "dns" in msg or "resolve" in msg:
            troubleshooting = [
                f"  1. DNS 解析失败，尝试更换 DNS 服务器",
                f"  2. 检查网络连接是否正常",
            ]
        else:
            troubleshooting = [
                f"  1. 检查网络连接是否正常",
                f"  2. 确认目标引擎网站可访问",
                f"  3. 如使用代理，检查代理配置",
            ]
        return ClassifiedError(
            category=ErrorCategory.NETWORK,
            engine=engine,
            message=f"网络连接失败: {exception}",
            troubleshooting=troubleshooting,
            exception=exception,
        )

    # Config errors
    if isinstance(exception, config_exceptions):
        troubleshooting = [
            f"  1. 确认 config.yaml 文件格式正确（冒号后有空格）",
            f"  2. 复制 references/config.yaml.example 重新配置",
            f"  3. 检查引用的引擎名称是否正确",
        ]
        return ClassifiedError(
            category=ErrorCategory.CONFIG,
            engine=engine,
            message=f"配置错误: {exception}",
            troubleshooting=troubleshooting,
            exception=exception,
        )

    # Engine parser errors (default)
    troubleshooting = [
        f"  1. {engine} 可能已更新页面结构",
        f"  2. 尝试更新本 skill 到最新版本",
        f"  3. 暂不使用该引擎：--engines 参数排除",
    ]
    return ClassifiedError(
        category=ErrorCategory.ENGINE,
        engine=engine,
        message=f"引擎解析或请求失败: {exception}",
        troubleshooting=troubleshooting,
        exception=exception,
    )


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
# 🆕 V1.1: 国内可用备选引擎（strict 模式自动降级）
# ============================================================

class YandexAdapter(EngineAdapter):
    """Yandex 搜索引擎（俄罗斯，国内可用）"""

    def __init__(self):
        super().__init__("yandex", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://yandex.com/search/?text={quote(query)}&numdoc={num}"
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
        for idx, item in enumerate(soup.select("li.serp-item")[:num]):
            title_el = item.select_one("a.Link, h2 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("div.TextContainer, div.Cluster-Content")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class StartpageAdapter(EngineAdapter):
    """Startpage 搜索引擎（Google 代理，国内可用）"""

    def __init__(self):
        super().__init__("startpage", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://www.startpage.com/do/dsearch?query={quote(query)}&cat=web"
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
        for idx, item in enumerate(soup.select("div.w-gl__result")[:num]):
            title_el = item.select_one("a.w-gl__result-title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("p.w-gl__description")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class QwantAdapter(EngineAdapter):
    """Qwant 搜索引擎（法国，国内可用）"""

    def __init__(self):
        super().__init__("qwant", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://www.qwant.com/?q={quote(query)}&t=web"
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
        for idx, item in enumerate(soup.select("article.webResult")[:num]):
            title_el = item.select_one("a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("p.webResult_description")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


class BraveAdapter(EngineAdapter):
    """Brave 搜索引擎（美国，国内可用）"""

    def __init__(self):
        super().__init__("brave", timeout=10)

    async def search(self, session: aiohttp.ClientSession, query: str, num: int = 10) -> SearchResponse:
        url = f"https://search.brave.com/search?q={quote(query)}&source=web"
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
        for idx, item in enumerate(soup.select("div.snippet")[:num]):
            title_el = item.select_one("a.heading-serpresult")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            snippet_el = item.select_one("p.snippet-description, p.description")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet, engine=self.name, rank=idx+1))
        return results


# ============================================================
# 🆕 V1.1: 引擎管理器（含自动降级）
# ============================================================

class EngineManager:
    """
    搜索引擎管理器
    - 管理所有可用引擎
    - strict 模式下国内可用性优先
    - 引擎故障自动降级
    """

    ALL_ENGINE_NAMES = [
        "baidu", "bing", "sogou", "360",
        "duckduckgo", "startpage", "yandex", "qwant", "brave",
        "searxng"
    ]

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engines: Dict[str, EngineAdapter] = {}
        self.failed_engines: set = set()
        self._init_engines()

    def _init_engines(self):
        """初始化所有引擎"""
        searxng_host = self.config.get("searxng", {}).get("host", "127.0.0.1")
        searxng_port = self.config.get("searxng", {}).get("port", 8888)
        engine_map = {
            "baidu": BaiduAdapter,
            "bing": BingAdapter,
            "sogou": SogouAdapter,
            "360": So360Adapter,
            "duckduckgo": DuckDuckGoAdapter,
            "yandex": YandexAdapter,
            "startpage": StartpageAdapter,
            "qwant": QwantAdapter,
            "brave": BraveAdapter,
            "searxng": lambda: SearXNGAdapter(host=searxng_host, port=searxng_port),
        }
        for name, cls in engine_map.items():
            try:
                self.engines[name] = cls()
            except Exception:
                pass


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

    for r in results:
        r.compute_simhash()

    unique: List[SearchResult] = []
    seen_hashes: List[Tuple[int, SearchResult]] = []

    for r in results:
        is_dup = False
        for h, existing in seen_hashes:
            if r.simhash is not None and h is not None and hamming_distance(r.simhash, h) <= threshold:
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
    url_map: Dict[str, List[SearchResult]] = defaultdict(list)
    for r in results:
        url_map[r.url].append(r)

    scored: List[Tuple[float, SearchResult]] = []
    for url, items in url_map.items():
        engine_count = len(set(item.engine for item in items))
        best_rank = min(item.rank for item in items)
        score = engine_count * 10 - best_rank
        representative = max(items, key=lambda x: len(x.snippet))
        scored.append((score, representative))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ============================================================
# 🆕 V1.2: 引擎故障自动降级（strict 模式增强）
# ============================================================

# strict 模式国内可用引擎（优先级顺序）
STRICT_FALLBACK_ENGINES = [
    "yandex",      # 俄罗斯，国内稳定
    "startpage",   # Google 代理，国内可用
    "qwant",       # 法国，国内可用
    "brave",       # 美国，国内可用
    "duckduckgo",  # 隐私优先，国内不稳定
]


async def try_engine_with_fallback(
    adapter: EngineAdapter,
    session: aiohttp.ClientSession,
    query: str,
    num: int,
) -> Tuple[Optional[SearchResult], Optional[ClassifiedError]]:
    """
    尝试搜索，失败时返回分类错误
    用于 strict 模式下一引擎失败自动切换到下一引擎
    """
    try:
        result = await adapter.search(session, query, num)
        if result.error and result.error.strip():
            err = classify_error(adapter.name, Exception(result.error))
            return None, err
        return result, None
    except Exception as e:
        err = classify_error(adapter.name, e)
        return None, err


# ============================================================
# 搜索编排器
# ============================================================

class SearchOrchestrator:
    """搜索编排器：并发调度 + 去重 + 排序 + 错误处理"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine_manager = EngineManager(config)
        self.engines: Dict[str, EngineAdapter] = self.engine_manager.engines
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._last_reset = datetime.now()
        # collect errors for reporting
        self._classified_errors: List[ClassifiedError] = []

    @property
    def classified_errors(self) -> List[ClassifiedError]:
        return self._classified_errors

    def _check_rate_limit(self, engine_name: str) -> bool:
        """检查是否超过日请求上限"""
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
        - strict 模式自动选择国内可用引擎
        - 引擎故障自动降级
        - 收集分类错误
        """
        self._classified_errors = []

        # 确定引擎列表
        if engines is None:
            if privacy_mode == "strict":
                # strict 模式：使用国内可用备选引擎 + 本地 SearXNG
                engines = STRICT_FALLBACK_ENGINES.copy()
                if self.config.get("searxng", {}).get("enabled", True):
                    engines.insert(0, "searxng")  # SearXNG 最优先
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
                delay = random.uniform(
                    self.config.get("search", {}).get("request_delay_min", 1.0),
                    self.config.get("search", {}).get("request_delay_max", 5.0),
                )
                tasks.append(self._search_with_error_handling(adapter, session, query, num, delay))

            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集结果
        all_results: List[SearchResult] = []
        for resp in responses:
            if isinstance(resp, Exception):
                continue
            if resp is None:
                continue
            # resp could be tuple (results, error) or SearchResponse
            if isinstance(resp, tuple):
                if resp[1]:  # has error
                    self._classified_errors.append(resp[1])  # type: ignore
                if resp[0]:  # has results
                    all_results.extend(resp[0])
                    if resp[0]:
                        engine_name = resp[0][0].engine
                        self._request_counts[engine_name] += 1
            elif isinstance(resp, SearchResponse):
                if resp.error:
                    continue
                all_results.extend(resp.results)
                self._request_counts[resp.engine] += 1

        # V1.2: strict 模式自动降级
        if privacy_mode == "strict" and not all_results:
            # 主引擎全部失败，尝试兜底引擎
            fallback_engines = ["baidu", "bing"]  # 国内可用但隐私保护较弱
            for fb_name in fallback_engines:
                if fb_name in self.engines and self._check_rate_limit(fb_name):
                    adapter = self.engines[fb_name]
                    try:
                        connector2 = aiohttp.TCPConnector(limit=1)
                        async with aiohttp.ClientSession(connector=connector2) as session:
                            resp = await adapter.search(session, query, num)
                            if resp.results:
                                all_results.extend(resp.results)
                                print(f"⚠️  备选引擎降级：{fb_name}（隐私保护较弱，建议检查网络后重试）")
                                break
                    except Exception:
                        pass

        # 去重
        unique = deduplicate_results(all_results)

        # 排序
        ranked = cross_engine_rank(unique)

        return ranked

    async def _search_with_error_handling(
        self,
        adapter: EngineAdapter,
        session: aiohttp.ClientSession,
        query: str,
        num: int,
        delay: float,
    ) -> Tuple[List[SearchResult], Optional[ClassifiedError]]:
        """带错误分类的搜索请求"""
        await asyncio.sleep(delay)
        start = time.time()
        try:
            resp = await asyncio.wait_for(
                adapter.search(session, query, num),
                timeout=adapter.timeout + 2,
            )
            if resp.error:
                err = classify_error(adapter.name, Exception(resp.error))
                return ([], err)
            return (resp.results, None)
        except asyncio.TimeoutError:
            err = classify_error(adapter.name, TimeoutError(f"Request timed out after {adapter.timeout}s"))
            return ([], err)
        except Exception as e:
            err = classify_error(adapter.name, e)
            return ([], err)


# ============================================================
# 🆕 V1.2: 错误报告输出
# ============================================================

def format_error_report(errors: List[ClassifiedError]) -> str:
    """格式化错误报告"""
    if not errors:
        return ""

    report = []
    # 按错误分类分组
    by_category: Dict[str, List[ClassifiedError]] = defaultdict(list)
    for e in errors:
        by_category[e.category.value].append(e)

    for category, errs in by_category.items():
        if category == "network":
            report.append("🌐 网络问题：")
        elif category == "config":
            report.append("⚙️  配置问题：")
        else:
            report.append("🔧 引擎问题：")

        for e in errs:
            report.append(f"  ✗ {e.engine}: {e.message}")
            for ts in e.troubleshooting[:2]:  # 只显示前 2 条排查建议
                report.append(f"    {ts}")

    return "\n".join(report)


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
    parser.add_argument("--engines", help="指定引擎，逗号分隔 (baidu,bing,sogou,360,duckduckgo,startpage,yandex,qwant,brave,searxng)")
    parser.add_argument("--num", type=int, default=10, help="每个引擎返回结果数")
    parser.add_argument("--privacy", choices=["normal", "strict"], default="normal", help="隐私模式")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细错误信息")

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

    # 输出错误摘要（分类错误）
    errors = orchestrator.classified_errors
    if errors and args.verbose:
        print("\n" + "=" * 60)
        print("🔍 错误诊断报告：")
        print(format_error_report(errors))
        print()

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

    # 如果没有结果但有错误，给用户提示
    if not results and errors and not args.verbose:
        # 按错误类型聚合
        categories = set(e.category.value for e in errors)
        if "network" in categories:
            print("💡 网络连接失败，请检查网络或使用 --verbose 查看详情")
        elif "config" in categories:
            print("💡 配置错误，请检查 config.yaml 或使用 --verbose 查看详情")
        elif "engine" in categories:
            print("💡 搜索引擎解析失败，请稍后重试或更换引擎")


if __name__ == "__main__":
    import os
    main()
