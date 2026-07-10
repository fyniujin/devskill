"""语义缓存（本地、零密钥、零联网，省 token）。

- 精确命中：归一化 query 后做哈希，完全一致的请求直接返回缓存结果，跳过 API 调用。
- 模糊命中（可选）：用 difflib 做相似度匹配，超过阈值也复用。
- 存储：本地 SQLite，带 TTL 自动过期。

安全：仅缓存 query 与对应回复文本，不缓存任何密钥；路径在用户主目录。
"""

import os
import sqlite3
import hashlib
import time
import re
import difflib

DEFAULT_CACHE_DB = os.path.join(os.path.expanduser("~"), ".cn_llm_router", "cache.db")
FUZZY_THRESHOLD = 0.80
# 模糊匹配最低字符数：过短的 query 容易误命中（如"你好"匹配到"你好吗"），直接跳过模糊。
MIN_FUZZY_LEN = 8


def _norm(text):
    """归一化：去空白、转小写、去标点。用于缓存 key。"""
    if not text:
        return ""
    s = text.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\u4e00-\u9fff]+", " ", s)
    return s.strip()


def _conn(db_path=None):
    db = db_path or DEFAULT_CACHE_DB
    if db == ":memory:":
        return sqlite3.connect(":memory:")
    os.makedirs(os.path.dirname(db), exist_ok=True)
    c = sqlite3.connect(db)
    c.execute(
        """CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qhash TEXT UNIQUE, norm_query TEXT,
            provider TEXT, model TEXT, response TEXT,
            created_at REAL
        )"""
    )
    c.commit()
    return c


def get(prompt, ttl_hours=168, fuzzy=False, db_path=None):
    """返回缓存命中时的 (provider, model, response)，否则 None。"""
    norm = _norm(prompt)
    if not norm:
        return None
    qh = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    c = _conn(db_path)
    try:
        now = time.time()
        row = c.execute(
            "SELECT provider, model, response, created_at FROM cache WHERE qhash=?",
            (qh,),
        ).fetchone()
        if row:
            provider, model, resp, created = row
            if (now - created) <= ttl_hours * 3600:
                return (provider, model, resp)
            else:
                c.execute("DELETE FROM cache WHERE qhash=?", (qh,))
                c.commit()

        if fuzzy:
            # 过短的 query 跳过模糊匹配，避免短句误命中
            if len(norm) < MIN_FUZZY_LEN:
                pass  # 不做模糊，直接返回 None
            else:
                rows = c.execute(
                    "SELECT provider, model, response, norm_query, created_at FROM cache"
                ).fetchall()
                best = None
                best_ratio = 0.0
                for provider, model, resp, nq, created in rows:
                    if (now - created) > ttl_hours * 3600:
                        continue
                    ratio = difflib.SequenceMatcher(None, norm, nq).ratio()
                    # 长度惩罚：两句话长度差异越大，越可能是不同问题
                    # 惩罚公式：adjusted = raw_ratio × (0.8 + 0.2 × length_ratio)
                    # 同长时不惩罚(×1.0)，极端差异时保留原始分数的 80%
                    len_a, len_b = len(norm), len(nq)
                    if min(len_a, len_b) > 0:
                        length_penalty = min(len_a, len_b) / max(len_a, len_b)
                    else:
                        length_penalty = 0.0
                    adjusted_ratio = ratio * (0.8 + 0.2 * length_penalty)
                    if adjusted_ratio > best_ratio:
                        best_ratio = adjusted_ratio
                        best = (provider, model, resp)
                if best and best_ratio >= FUZZY_THRESHOLD:
                    return best
    finally:
        c.close()
    return None


def put(prompt, provider, model, response, db_path=None):
    """写入缓存（幂等：同 key 覆盖）。"""
    norm = _norm(prompt)
    if not norm:
        return
    qh = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    c = _conn(db_path)
    try:
        c.execute(
            "INSERT OR REPLACE INTO cache (qhash, norm_query, provider, model, response, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (qh, norm, provider, model, response, time.time()),
        )
        c.commit()
    finally:
        c.close()


def stats(db_path=None):
    c = _conn(db_path)
    try:
        n = c.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        return {"entries": n}
    finally:
        c.close()


def clear(db_path=None):
    c = _conn(db_path)
    try:
        n = c.execute("DELETE FROM cache").rowcount
        c.commit()
        return n
    finally:
        c.close()
