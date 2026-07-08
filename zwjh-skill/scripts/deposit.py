# -*- coding: utf-8 -*-
"""
自动沉淀 —— 把对话 / 文件 / 每日日志变成「记忆 + 图谱」。

流程（每个知识点）：
  1. 切词 -> 去重指纹（norm_hash）
  2. 完全重复：直接合并访问，不新增
  3. 近似重复（Jaccard ≥ 阈值）：更新原条目而不是新增
  4. 全新：入库为记忆，并做：
       - 提及链接（挂到已有实体）
       - 轻量关系抽取（模板）
       - 轻量事实抽取（"X 的 Y 是 Z"）
  5. 事实写入带「冲突消解」：同谓词旧值自动标记 superseded

所有步骤纯本地、零密钥、按硬件档位分批。
"""

from __future__ import annotations

import os
import re
from datetime import date

from . import config, embeddings, store
from .hardware import get_plan, recommend_subtasks
from . import graph

# 可读取的纯文本类型（避开一切二进制/可执行类型）
_TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".js", ".ts", ".json", ".csv", ".yaml", ".yml",
    ".html", ".htm", ".xml", ".toml", ".ini", ".cfg", ".rst", ".tex",
}

# 事实抽取模板：("X 的 Y 是/为 Z") -> (实体 X, 谓词 Y, 值 Z)
_FACT_PATTERNS = [
    re.compile(r"([一-龥A-Za-z0-9_]{1,20})的([一-龥A-Za-z0-9_]{1,10})[是为：:]\s*([^\n。；;]{1,60})"),
]


def _day_of(day: str | None) -> str:
    return day or config.today_str()


def deposit_text(text: str, source: str = "conversation", day: str | None = None,
                 link_graph: bool = True) -> dict:
    """
    沉淀一段文本为一个（或零个，若完全重复）记忆。

    返回：{status, memory_id, dedup, near_dup, relations, facts}
    """
    text = (text or "").strip()
    if len(text) < 4:
        return {"status": "skip", "reason": "too_short"}

    toks = embeddings.tokenize(text)
    if not toks:
        return {"status": "skip", "reason": "no_tokens"}
    h = embeddings.norm_hash(toks)
    day = _day_of(day)

    # 1) 完全重复
    exist = store.find_by_hash(h)
    if exist:
        store.update_access(exist["id"])
        return {"status": "dedup", "memory_id": exist["id"]}

    # 2) 近似重复（Jaccard）
    near = _find_near_dup(set(toks))
    if near:
        store.update_access(near["id"])
        return {"status": "near_dup", "memory_id": near["id"]}

    # 3) 新增
    mid = store.add_memory(day, source, text, h, toks)
    relations, facts = [], []
    if link_graph:
        relations = graph.auto_relate_from_text(text)
        facts = extract_facts(text, memory_id=mid)
    return {
        "status": "added",
        "memory_id": mid,
        "relations": relations,
        "facts": facts,
    }


def _find_near_dup(token_set: set[str]):
    """在已有记忆中找 Jaccard 超过阈值的近似重复。"""
    threshold = config.NEAR_DUP_JACCARD
    mems = store.all_memory_tokens()
    best, best_j = None, 0.0
    for mid, toks in mems:
        if not toks:
            continue
        j = embeddings.jaccard(token_set, set(toks))
        if j > best_j:
            best_j, best = j, mid
    if best and best_j >= threshold:
        conn = store.get_conn()
        row = conn.execute("SELECT * FROM memories WHERE id=?", (best,)).fetchone()
        return dict(row) if row else None
    return None


# 事实主语黑名单：这些词是动词/泛化词，不应作为实体
_FACT_SUBJECT_STOP = {
    "对接", "负责", "处理", "管理", "跟进", "联系", "支持", "推进", "协调",
    "参与", "创建", "开发", "维护", "运营", "接", "做", "搞", "产品", "状态",
    "情况", "问题", "事情", "东西", "系统", "项目",
}


def extract_facts(text: str, memory_id: int | None = None) -> list[dict]:
    """从文本抽取简单事实并写入（带冲突消解）。"""
    out = []
    for pat in _FACT_PATTERNS:
        for m in pat.finditer(text):
            ent_name = graph._clean_entity(m.group(1))
            pred = m.group(2).strip()
            val = m.group(3).strip()
            if not ent_name or not pred or not val:
                continue
            if ent_name in _FACT_SUBJECT_STOP or pred in _FACT_SUBJECT_STOP:
                continue
            if len(pred) > 8 or len(val) > 60 or len(ent_name) > 20:
                continue
            if ent_name == pred:
                continue
            ent_type = graph._guess_type(ent_name)
            eid = store.upsert_entity(ent_type, ent_name, importance=0.7)
            res = store.add_fact(eid, pred, val, source_memory_id=memory_id)
            out.append({"entity": ent_name, "predicate": pred,
                        "value": val, "conflict": res["conflict"]})
    return out


def deposit_conversation(text: str, day: str | None = None) -> dict:
    """沉淀一段对话（按空行分段，每段一个知识点）。"""
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not parts:
        parts = [text]
    plan = get_plan()
    sub = recommend_subtasks(len(parts), plan)
    # 顺序处理（保证图谱一致性），但给出「建议子任务数」用于上层调度
    results = [deposit_text(p, source="conversation", day=day) for p in parts]
    added = sum(1 for r in results if r.get("status") == "added")
    return {"total": len(parts), "added": added, "suggested_subtasks": sub,
            "details": results}


def ingest_file(path: str, day: str | None = None) -> dict:
    """读取一个纯文本文件并沉淀为多个知识点。"""
    p = path
    if not os.path.exists(p):
        return {"status": "error", "reason": "not_found"}
    ext = os.path.splitext(p)[1].lower()
    if ext not in _TEXT_SUFFIXES:
        return {"status": "error", "reason": f"unsupported_type:{ext}"}
    try:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(p, "r", encoding="gbk") as f:
                content = f.read()
        except Exception:
            return {"status": "error", "reason": "decode_error"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

    # 按段落 / 行 切分，控制单条长度
    chunks = _split_file(content)
    plan = get_plan()
    sub = recommend_subtasks(len(chunks), plan)
    results = [deposit_text(c, source=f"file:{os.path.basename(p)}", day=day)
               for c in chunks]
    added = sum(1 for r in results if r.get("status") == "added")
    return {"file": p, "chunks": len(chunks), "added": added,
            "suggested_subtasks": sub}


def _split_file(content: str, max_len: int = 600) -> list[str]:
    chunks = []
    buf = []
    for line in content.splitlines():
        buf.append(line)
        txt = "\n".join(buf)
        if len(txt) >= max_len:
            if txt.strip():
                chunks.append(txt.strip())
            buf = []
    if buf:
        txt = "\n".join(buf).strip()
        if txt:
            chunks.append(txt)
    return chunks


def index_daily_logs() -> dict:
    """
    把历史「每日日志」（YYYY-MM-DD.md）补录进记忆底座。
    这样原有 v1.7 积累的记忆也能被语义检索 / 图谱使用——「原有功能保留」。
    """
    config.ensure_dirs()
    mem_dir = config.MEMORY_DIR
    files = sorted(mem_dir.glob("20??-??-??.md"))
    total_added = 0
    for fp in files:
        day = fp.stem
        if store.get_daily_log(day):
            continue  # 已索引，幂等跳过，避免每日重复堆积
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        res = deposit_text(content, source="daily_log", day=day,
                           link_graph=False)  # 每日日志整体作为一条「当日记忆」
        if res.get("status") == "added":
            total_added += 1
    return {"daily_logs": len(files), "added": total_added}


if __name__ == "__main__":
    r = deposit_text("机器学习项目需要大量算力和数据", source="test")
    print(r)
    print(index_daily_logs())
