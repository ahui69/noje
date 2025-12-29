#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib
import inspect
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, conint, confloat, constr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


def _get_bearer_token(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization") or ""
    auth = auth.strip()
    if not auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Unauthorized")
    return parts[1].strip()


async def _maybe_await(v: Any) -> Any:
    if inspect.isawaitable(v):
        return await v
    return v


async def _verify_request_auth(request: Request) -> None:
    token = _get_bearer_token(request)

    verify_fn = None
    for mod_name in ("core.auth", "auth"):
        try:
            mod = importlib.import_module(mod_name)
            cand = getattr(mod, "verify_token", None)
            if callable(cand):
                verify_fn = cand
                break
        except Exception:
            continue

    if verify_fn is None:
        raise HTTPException(status_code=500, detail="Auth verifier not found")

    try:
        ok = await _maybe_await(verify_fn(token))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("verify_token failed")
        raise HTTPException(status_code=401, detail=f"Unauthorized: {e}") from e

    if ok is False:
        raise HTTPException(status_code=401, detail="Unauthorized")


class HybridSearchRequest(BaseModel):
    query: constr(min_length=1) = Field(..., description="Search query")
    limit: conint(ge=1, le=100) = Field(10, description="Max hits")
    user_id: constr(min_length=1, max_length=128) = Field("default", description="User id")
    show_breakdown: bool = Field(False, description="Include breakdown if available")
    min_score: confloat(ge=0.0) = Field(0.0, description="Minimum score")


class SearchHit(BaseModel):
    id: Optional[str] = None
    score: float
    text: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    breakdown: Optional[Dict[str, Any]] = None


class HybridSearchResponse(BaseModel):
    query: str
    hits: List[SearchHit]
    took_ms: float
    breakdown: Optional[Dict[str, Any]] = None
    used_fallback: bool = False


def _pick_hybrid_callable() -> Optional[Callable[..., Any]]:
    candidates: Sequence[Tuple[str, str]] = (
        ("core.semantic", "hybrid_search"),
        ("core.hybrid_search", "hybrid_search"),
        ("core.hierarchical_memory", "hybrid_search"),
        ("core.advanced_memory", "hybrid_search"),
        ("core.memory", "hybrid_search"),
        ("hybrid_search", "hybrid_search"),
    )
    for mod_name, attr in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn
    return None


def _extract_hits_and_breakdown(raw: Any) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if raw is None:
        return [], None

    if isinstance(raw, tuple) and len(raw) == 2:
        a, b = raw
        if isinstance(a, list) and isinstance(b, dict):
            return a, b
        if isinstance(a, dict) and isinstance(b, list):
            return b, a

    if isinstance(raw, dict):
        for key in ("hits", "results", "items"):
            val = raw.get(key)
            if isinstance(val, list):
                br = raw.get("breakdown") if isinstance(raw.get("breakdown"), dict) else None
                return val, br
        if "breakdown" in raw and isinstance(raw["breakdown"], dict):
            return [], raw["breakdown"]

    if isinstance(raw, list):
        return raw, None

    return [], None


def _norm_score(d: Dict[str, Any]) -> float:
    for k in ("score", "similarity", "sim", "rank_score"):
        if k in d:
            try:
                return float(d[k])
            except Exception:
                return 0.0
    return 0.0


def _norm_text(d: Dict[str, Any]) -> str:
    for k in ("text", "content", "chunk", "snippet", "message", "value"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _norm_id(d: Dict[str, Any]) -> Optional[str]:
    for k in ("id", "doc_id", "rowid", "key", "uuid"):
        v = d.get(k)
        if v is None:
            continue
        try:
            s = str(v).strip()
            return s if s else None
        except Exception:
            continue
    return None


def _norm_source(d: Dict[str, Any]) -> Optional[str]:
    for k in ("source", "collection", "type", "table"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _strip_known_fields(d: Dict[str, Any]) -> Dict[str, Any]:
    drop = {"text", "content", "chunk", "snippet", "message", "value", "score", "similarity", "sim", "rank_score", "breakdown"}
    return {k: v for k, v in d.items() if k not in drop}


@dataclass(frozen=True)
class _DbPlan:
    path: str
    table: str
    is_fts: bool
    text_col: str


_DB_PLAN: Optional[_DbPlan] = None


def _candidate_db_paths() -> List[str]:
    env = (os.getenv("MEMORY_DB_PATH") or os.getenv("MEM_DB_PATH") or "").strip()
    cands: List[str] = []
    if env:
        cands.append(env)
    cands.extend([
        "/root/mrd/mem.db",
        "/root/mrd/core/mem.db",
        os.path.join(os.getcwd(), "mem.db"),
        os.path.join(os.getcwd(), "core", "mem.db"),
    ])
    uniq: List[str] = []
    seen = set()
    for p in cands:
        p2 = os.path.abspath(p)
        if p2 not in seen and os.path.isfile(p2):
            seen.add(p2)
            uniq.append(p2)
    return uniq


def _sqlite_connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def _detect_db_plan() -> Optional[_DbPlan]:
    global _DB_PLAN
    if _DB_PLAN is not None:
        return _DB_PLAN

    paths = _candidate_db_paths()
    if not paths:
        return None

    for path in paths:
        try:
            con = _sqlite_connect(path)
            try:
                rows = con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' OR type='view'").fetchall()
            finally:
                con.close()
        except Exception:
            continue

        tables: List[Tuple[str, str]] = []
        for r in rows:
            name = str(r["name"])
            sql = str(r["sql"] or "")
            tables.append((name, sql))

        fts_tables: List[str] = []
        for name, sql in tables:
            s = (sql or "").lower()
            if "virtual table" in s and "fts" in s:
                fts_tables.append(name)

        if fts_tables:
            chosen = None
            for prefer in ("mem_fts", "memory_fts", "mrd_fts", "notes_fts", "facts_fts"):
                if prefer in fts_tables:
                    chosen = prefer
                    break
            if chosen is None:
                chosen = fts_tables[0]

            text_col = "content"
            try:
                con = _sqlite_connect(path)
                try:
                    cols = [str(x["name"]) for x in con.execute(f"PRAGMA table_info({chosen})").fetchall()]
                finally:
                    con.close()
                for c in ("content", "text", "body", "value"):
                    if c in cols:
                        text_col = c
                        break
            except Exception:
                text_col = "content"

            _DB_PLAN = _DbPlan(path=path, table=chosen, is_fts=True, text_col=text_col)
            return _DB_PLAN

        for prefer in ("memories", "memory", "notes", "facts", "entries"):
            if any(name == prefer for name, _ in tables):
                chosen = prefer
                text_col = "content"
                try:
                    con = _sqlite_connect(path)
                    try:
                        cols = [str(x["name"]) for x in con.execute(f"PRAGMA table_info({chosen})").fetchall()]
                    finally:
                        con.close()
                    for c in ("content", "text", "body", "value"):
                        if c in cols:
                            text_col = c
                            break
                except Exception:
                    text_col = "content"
                _DB_PLAN = _DbPlan(path=path, table=chosen, is_fts=False, text_col=text_col)
                return _DB_PLAN

        for name, _ in tables:
            try:
                con = _sqlite_connect(path)
                try:
                    cols = [str(x["name"]) for x in con.execute(f"PRAGMA table_info({name})").fetchall()]
                finally:
                    con.close()
                for c in ("content", "text", "body", "value"):
                    if c in cols:
                        _DB_PLAN = _DbPlan(path=path, table=name, is_fts=False, text_col=c)
                        return _DB_PLAN
            except Exception:
                continue

    return None


def _fts_search(plan: _DbPlan, query: str, limit: int) -> List[Dict[str, Any]]:
    con = _sqlite_connect(plan.path)
    try:
        q = query.strip()
        if not q:
            return []
        sql = f"""
            SELECT
                rowid AS rowid,
                snippet({plan.table}, -1, '', '', ' … ', 16) AS snippet,
                bm25({plan.table}) AS rank
            FROM {plan.table}
            WHERE {plan.table} MATCH ?
            ORDER BY rank ASC
            LIMIT ?
        """
        rows = con.execute(sql, (q, int(limit))).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            rank = float(r["rank"]) if r["rank"] is not None else 0.0
            score = 1.0 / (1.0 + max(rank, 0.0))
            out.append(
                {
                    "rowid": int(r["rowid"]),
                    "score": score,
                    "text": str(r["snippet"] or "").strip(),
                    "table": plan.table,
                    "db": plan.path,
                    "rank": rank,
                }
            )
        return out
    finally:
        con.close()


def _like_search(plan: _DbPlan, query: str, limit: int) -> List[Dict[str, Any]]:
    con = _sqlite_connect(plan.path)
    try:
        q = query.strip()
        if not q:
            return []
        like = f"%{q}%"
        sql = f"""
            SELECT rowid AS rowid, {plan.text_col} AS text
            FROM {plan.table}
            WHERE {plan.text_col} LIKE ?
            LIMIT ?
        """
        rows = con.execute(sql, (like, int(limit))).fetchall()
        out: List[Dict[str, Any]] = []
        for i, r in enumerate(rows):
            text = str(r["text"] or "").strip()
            if not text:
                continue
            score = 0.5 - (0.001 * i)
            out.append(
                {
                    "rowid": int(r["rowid"]),
                    "score": float(score),
                    "text": text[:2000],
                    "table": plan.table,
                    "db": plan.path,
                }
            )
        return out
    finally:
        con.close()


def _fallback_search(query: str, limit: int) -> List[Dict[str, Any]]:
    plan = _detect_db_plan()
    if plan is None:
        return []
    try:
        if plan.is_fts:
            hits = _fts_search(plan, query, limit)
            if hits:
                return hits
        return _like_search(plan, query, limit)
    except Exception:
        logger.exception("fallback sqlite search failed")
        return []


def _call_primary_hybrid(fn, payload):
    """
    Best-effort wywołanie primary hybrid callable bez wywalania endpointu.
    Celowo NIE przekazuje `show_breakdown` (to debug endpointu, nie parametr wyszukiwarki).

    Zasada:
      - najpierw próba kwargs (tylko te, które funkcja przyjmuje albo **kwargs),
      - przy TypeError (np. unexpected keyword) spadamy do pozycyjnych wariantów.
    """
    import inspect

    if fn is None:
        return None

    query = payload.query
    limit = int(payload.limit)
    user_id = str(payload.user_id)
    min_score = float(payload.min_score)

    base = {
        "query": query,
        "limit": limit,
        "user_id": user_id,
        "min_score": min_score,
    }

    try:
        sig = inspect.signature(fn)
        params = sig.parameters
        has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except Exception:
        sig = None
        params = {}
        has_varkw = False

    # 1) kwargs (najczystsze)
    if has_varkw:
        try:
            return fn(**base)
        except TypeError:
            pass

    if sig is not None and params:
        filtered = {k: v for k, v in base.items() if k in params}
        if filtered:
            try:
                return fn(**filtered)
            except TypeError:
                pass

    # 2) positional fallbacks (różne spotykane sygnatury)
    candidates = [
        (query, limit, user_id, min_score),
        (query, limit, user_id),
        (query, limit),
        (query,),
    ]
    for args in candidates:
        try:
            return fn(*args)
        except TypeError:
            continue

    # 3) last resort
    return fn(query)

    took_ms = (time.perf_counter() - t0) * 1000.0
    return HybridSearchResponse(
        query=payload.query,
        hits=hits_out,
        took_ms=float(round(took_ms, 3)),
        breakdown=breakdown,
        used_fallback=bool(used_fallback),
    )
