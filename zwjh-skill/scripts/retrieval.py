# -*- coding: utf-8 -*-
"""
检索层 —— 语义检索 + 时间线检索。

语义检索：本地 TF-IDF 余弦（见 embeddings.py），零密钥、零联网、毫秒级。
时间线检索：按日期区间 + 关键词过滤，还原「某段时间发生了什么」。

两者都受硬件档位约束：批量处理、内存缓存可按档位关闭（见 hardware.py）。
"""

from __future__ import annotations

from collections import Counter

from . import config, embeddings, store
from .hardware import get_plan


def semantic_search(query: str, top_k: int = 8, day_from: str | None = None,
                    day_to: str | None = None) -> list[dict]:
    """
    语义检索：返回与 query 最相似的记忆条目。

    返回字段：memory_id, day, source, score, snippet
    """
    plan = get_plan()
    q_tokens = embeddings.tokenize(query)
    if not q_tokens:
        return []
    mem_tokens = store.all_memory_tokens()
    if not mem_tokens:
        return []
    idf = embeddings.build_idf(mem_tokens)
    q_vec = embeddings.tfidf_query(q_tokens, idf)

    # 按硬件档位分批打分，避免一次性占用过多内存
    batch = plan["batch_size"]
    scored: list[tuple[float, int]] = []
    for i in range(0, len(mem_tokens), batch):
        chunk = mem_tokens[i : i + batch]
        for mid, toks in chunk:
            if not toks:
                continue
            d_vec = embeddings.tf_vector(toks)
            # 转 TF-IDF：用文档 TF × 语料 IDF
            d_tfidf = Counter({t: f * idf.get(t, 1.0) for t, f in d_vec.items()})
            sc = embeddings.cosine(q_vec, d_tfidf)
            if sc > 0:
                scored.append((sc, mid))
        # 让出 CPU：超大语料时小睡，避免长占线程
        if len(mem_tokens) > batch * 4:
            import time
            time.sleep(0)

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    conn = store.get_conn()
    results = []
    for sc, mid in top:
        row = conn.execute("SELECT * FROM memories WHERE id=?", (mid,)).fetchone()
        if not row:
            continue
        day = row["day"]
        if day_from and day < day_from:
            continue
        if day_to and day > day_to:
            continue
        store.update_access(mid)
        text = row["raw_text"] or ""
        results.append(
            {
                "memory_id": mid,
                "day": day,
                "source": row["source"],
                "score": round(sc, 4),
                "snippet": text[:160],
            }
        )
    return results


def timeline_search(day_from: str | None, day_to: str | None,
                    keyword: str | None = None, limit: int = 100) -> list[dict]:
    """
    时间线检索：按日期区间（必填其一）返回记忆，可叠加关键词过滤。
    """
    mems = store.list_memories(day_from=day_from, day_to=day_to, limit=limit)
    out = []
    kw_tokens = embeddings.tokenize(keyword) if keyword else None
    for m in mems:
        if kw_tokens:
            mt = set(embeddings.tokenize(m["raw_text"]))
            if not (set(kw_tokens) & mt):
                continue
        store.update_access(m["id"])
        out.append(
            {
                "memory_id": m["id"],
                "day": m["day"],
                "source": m["source"],
                "snippet": (m["raw_text"] or "")[:160],
            }
        )
    return out


def ask(question: str, top_k: int = 5) -> str:
    """
    给 Agent 用的「记忆问答」：返回拼接后的相关记忆文本，便于直接引用。
    其他 skill 可调用此函数把长期记忆注入自己的上下文。
    """
    hits = semantic_search(question, top_k=top_k)
    if not hits:
        return "（记忆底座中没有找到相关内容）"
    parts = []
    for h in hits:
        parts.append(f"[{h['day']} · {h['source']} · 相关度 {h['score']}]\n{h['snippet']}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    r = semantic_search("发布失败 根因", top_k=3)
    for x in r:
        print(x["day"], x["score"], x["snippet"][:50])
