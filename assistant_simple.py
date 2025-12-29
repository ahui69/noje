#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import time
import uuid
import sqlite3
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncIterator, Tuple

import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _now() -> float:
    return time.time()

def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k or k in os.environ:
            continue
        if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
            v = v[1:-1]
        os.environ[k] = v

_load_env_file(ENV_PATH)

AUTH_TOKEN = (os.getenv("AUTH_TOKEN") or "").strip()

def _auth_ok(req: Request) -> bool:
    if not AUTH_TOKEN:
        return True
    got = (req.headers.get("authorization") or "").strip()
    if got.lower().startswith("bearer "):
        got = got[7:].strip()
    return got == AUTH_TOKEN

LLM_BASE_URL = (os.getenv("LLM_BASE_URL") or "https://api.deepinfra.com/v1/openai").rstrip("/")
LLM_API_KEY = (os.getenv("LLM_API_KEY") or "").strip()
LLM_MODEL = (os.getenv("LLM_MODEL") or "").strip()

LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT", "60") or "60")

STREAM_FLUSH_CHARS = int(os.getenv("CHAT_STREAM_FLUSH_CHARS", "120") or "120")
STREAM_FLUSH_INTERVAL_MS = int(os.getenv("CHAT_STREAM_FLUSH_INTERVAL_MS", "120") or "120")
STREAM_FLUSH_INTERVAL_S = max(0.02, STREAM_FLUSH_INTERVAL_MS / 1000.0)

SESS_DB = os.getenv("SESSIONS_DB") or str(DATA_DIR / "sessions.db")

def _db() -> sqlite3.Connection:
    con = sqlite3.connect(SESS_DB, check_same_thread=False)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    con.commit()
    return con

def _ensure_session(con: sqlite3.Connection, user_id: str, session_id: Optional[str]) -> str:
    sid = (session_id or "").strip() or str(uuid.uuid4())
    now = _now()
    row = con.execute("SELECT id FROM sessions WHERE id=? AND user_id=?", (sid, user_id)).fetchone()
    if row:
        con.execute("UPDATE sessions SET updated_at=? WHERE id=?", (now, sid))
    else:
        con.execute(
            "INSERT INTO sessions(id,user_id,created_at,updated_at) VALUES(?,?,?,?)",
            (sid, user_id, now, now),
        )
    con.commit()
    return sid

def _append_msg(con: sqlite3.Connection, session_id: str, user_id: str, role: str, content: str) -> None:
    con.execute(
        "INSERT INTO messages(id,session_id,user_id,role,content,ts) VALUES(?,?,?,?,?,?)",
        (str(uuid.uuid4()), session_id, user_id, role, content, _now()),
    )
    con.commit()

def _load_context(con: sqlite3.Connection, session_id: str, limit: int = 30) -> List[Dict[str, str]]:
    rows = con.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY ts DESC LIMIT ?",
        (session_id, int(limit)),
    ).fetchall()
    rows.reverse()
    out: List[Dict[str, str]] = []
    for role, content in rows:
        out.append({"role": str(role), "content": str(content)})
    return out

def _llm_headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        h["Authorization"] = f"Bearer {LLM_API_KEY}"
    return h

def _check_llm_config() -> Optional[str]:
    if not LLM_API_KEY:
        return "Brak LLM_API_KEY w .env"
    if not LLM_MODEL:
        return "Brak LLM_MODEL w .env"
    return None

async def _llm_chat(messages: List[Dict[str, Any]], temperature: float, max_tokens: int) -> str:
    err = _check_llm_config()
    if err:
        return f"⚠️ {err}"
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "top_p": 0.9,
    }
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_S) as client:
        r = await client.post(f"{LLM_BASE_URL}/chat/completions", headers=_llm_headers(), json=payload)
        if r.status_code != 200:
            return f"❌ LLM Error ({r.status_code}): {r.text[:400]}"
        data = r.json()
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()

async def _llm_chat_stream_tokens(messages: List[Dict[str, Any]], temperature: float, max_tokens: int) -> AsyncIterator[str]:
    err = _check_llm_config()
    if err:
        yield f"⚠️ {err}"
        return

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "top_p": 0.9,
        "stream": True,
    }

    timeout = httpx.Timeout(timeout=LLM_TIMEOUT_S, connect=20.0, read=LLM_TIMEOUT_S)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", f"{LLM_BASE_URL}/chat/completions", headers=_llm_headers(), json=payload) as r:
            if r.status_code != 200:
                text = (await r.aread()).decode("utf-8", errors="ignore")
                yield f"❌ LLM Error ({r.status_code}): {text[:400]}"
                return

            async for line in r.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                if line.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                delta = ((obj.get("choices") or [{}])[0].get("delta") or {})
                token = delta.get("content")
                if token:
                    yield token

def _sse(event: str, data: Any) -> bytes:
    # trzymamy Twoją obecną strukturę: {"event": "...", "data": ...}
    payload = {"event": event, "data": data}
    return ("data: " + json.dumps(payload, ensure_ascii=False) + "\n\n").encode("utf-8")

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatBody(BaseModel):
    message: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    user_id: str = Field(default="default")
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=8192)
    use_history: bool = True

def _extract_text(body: ChatBody) -> str:
    if body.message and body.message.strip():
        return body.message.strip()
    if body.messages and isinstance(body.messages, list) and body.messages:
        last = body.messages[-1]
        if isinstance(last, dict):
            c = last.get("content") or last.get("text") or ""
            if isinstance(c, str) and c.strip():
                return c.strip()
    return ""

def _normalize_messages(body: ChatBody, text: str, history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    msgs: List[Dict[str, Any]] = []
    sys = (body.system_prompt or "").strip()
    if sys:
        msgs.append({"role": "system", "content": sys})

    if body.use_history and history:
        msgs.extend(history)

    if body.messages and isinstance(body.messages, list) and body.messages:
        cleaned: List[Dict[str, str]] = []
        for m in body.messages[-40:]:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "").strip().lower()
            content = m.get("content") or m.get("text") or ""
            if role not in ("system", "user", "assistant"):
                continue
            if not isinstance(content, str) or not content.strip():
                continue
            cleaned.append({"role": role, "content": content.strip()})
        if cleaned:
            base = [x for x in msgs if x.get("role") == "system"]
            return base + cleaned

    msgs.append({"role": "user", "content": text})
    return msgs

@router.post("/assistant")
async def chat_assistant(req: Request, body: ChatBody) -> Dict[str, Any]:
    if not _auth_ok(req):
        raise HTTPException(status_code=401, detail="Unauthorized")

    text = _extract_text(body)
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")

    con = _db()
    try:
        sid = _ensure_session(con, body.user_id, body.session_id)
        history = _load_context(con, sid, limit=30) if body.use_history else []
        msgs = _normalize_messages(body, text, history)

        _append_msg(con, sid, body.user_id, "user", text)
        ans = await _llm_chat(msgs, temperature=body.temperature, max_tokens=body.max_tokens)
        _append_msg(con, sid, body.user_id, "assistant", ans)

        return {
            "answer": ans,
            "session_id": sid,
            "ts": _now(),
            "metadata": {
                "model": LLM_MODEL,
                "base_url": LLM_BASE_URL,
                "history_used": bool(body.use_history),
            },
        }
    finally:
        try:
            con.close()
        except Exception:
            pass
@router.post("/assistant/stream")
async def chat_assistant_stream(req: Request, body: ChatBody) -> StreamingResponse:
    import os
    import json
    import time
    import uuid
    from typing import Any, Dict, List, Optional

    import httpx

    # --- konfiguracja LLM (OpenAI-compatible) ---
    base_url = (os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "").strip().rstrip("/")
    api_key = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    model = (os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "").strip()

    try:
        _g_base = globals().get("LLM_BASE_URL")
        if isinstance(_g_base, str) and _g_base.strip():
            base_url = _g_base.strip().rstrip("/")
    except Exception:
        pass
    try:
        _g_key = globals().get("LLM_API_KEY")
        if isinstance(_g_key, str) and _g_key.strip():
            api_key = _g_key.strip()
    except Exception:
        pass
    try:
        _g_model = globals().get("LLM_MODEL")
        if isinstance(_g_model, str) and _g_model.strip():
            model = _g_model.strip()
    except Exception:
        pass

    if not base_url:
        base_url = "https://api.deepinfra.com/v1/openai"
    if not model:
        model = "NousResearch/Hermes-3-Llama-3.1-405B"

    timeout_s = float(os.getenv("CHAT_STREAM_TIMEOUT_S", "120"))

    # --- stream behavior ---
    # final = jedno delta na koniec
    chunk_mode = (os.getenv("CHAT_STREAM_CHUNK_MODE", "final") or "final").strip().lower()
    ping_ms = int(os.getenv("CHAT_STREAM_PING_MS", "500"))  # keepalive (nie tekst)
    hard_max_buf = int(os.getenv("CHAT_STREAM_HARD_MAX_BUF", "20000"))  # awaryjne ograniczenie

    # --- system prompt ---
    sys_prompt = ""
    try:
        sp = getattr(body, "system_prompt", None)
        if isinstance(sp, str) and sp.strip():
            sys_prompt = sp.strip()
    except Exception:
        pass
    if not sys_prompt:
        try:
            env_sp = os.getenv("MORDZIX_SYSTEM_PROMPT", "").strip()
            if env_sp:
                sys_prompt = env_sp
        except Exception:
            pass

    # --- messages ---
    text = (getattr(body, "message", None) or "").strip()
    cleaned: List[Dict[str, str]] = []
    msgs_in = getattr(body, "messages", None)
    if isinstance(msgs_in, list) and msgs_in:
        for m in msgs_in[-60:]:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "").strip().lower()
            content = m.get("content") or m.get("text") or ""
            if role not in ("system", "user", "assistant"):
                continue
            if not isinstance(content, str) or not content.strip():
                continue
            cleaned.append({"role": role, "content": content.strip()})

    if not cleaned:
        if text:
            cleaned = [{"role": "user", "content": text}]
        else:
            cleaned = [{"role": "user", "content": " "}]

    messages: List[Dict[str, str]] = []
    if sys_prompt:
        messages.append({"role": "system", "content": sys_prompt})
    messages.extend([m for m in cleaned if m.get("role") != "system"])

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(getattr(body, "temperature", 0.7) or 0.7),
        "max_tokens": int(getattr(body, "max_tokens", 2000) or 2000),
        "top_p": float(getattr(body, "top_p", 0.9) or 0.9),
        "stream": True,
    }

    uid = (getattr(body, "user_id", None) or "default")
    req_sess = getattr(body, "session_id", None)
    con = None
    sid: Optional[str] = None

    def _now() -> float:
        try:
            fn = globals().get("_now")
            if callable(fn):
                return float(fn())
        except Exception:
            pass
        return float(time.time())

    def _safe_close() -> None:
        nonlocal con
        try:
            if con is not None:
                con.close()
        except Exception:
            pass
        con = None

    async def gen():
        nonlocal con, sid

        try:
            _db_fn = globals().get("_db")
            _ensure_fn = globals().get("_ensure_session")
            if callable(_db_fn) and callable(_ensure_fn):
                con = _db_fn()
                sid = _ensure_fn(con, uid, req_sess)
            else:
                sid = req_sess or str(uuid.uuid4())
        except Exception:
            sid = req_sess or str(uuid.uuid4())
            _safe_close()

        yield _sse("meta", {"session_id": sid, "ts": _now(), "model": model})

        stream_buf = ""
        full_parts: List[str] = []

        next_ping = time.monotonic() + (max(ping_ms, 0) / 1000.0)

        async def maybe_ping():
            nonlocal next_ping
            if ping_ms <= 0:
                return
            now = time.monotonic()
            if now >= next_ping:
                next_ping = now + (ping_ms / 1000.0)
                # komentarz SSE (nie "data:"), klient tego nie parsuje jako event tekstu
                yield b": ping\n\n"

        try:
            timeout = httpx.Timeout(timeout=timeout_s, connect=20.0, read=timeout_s)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", f"{base_url}/chat/completions", headers=headers, json=payload) as r:
                    if r.status_code != 200:
                        raw = (await r.aread()).decode("utf-8", errors="ignore")
                        yield _sse("error", f"LLM HTTP {r.status_code}: {raw[:800]}")
                        yield _sse("done", {"ok": True})
                        _safe_close()
                        return

                    async for line in r.aiter_lines():
                        async for k in maybe_ping():
                            yield k

                        if not line:
                            continue
                        if line.startswith("data:"):
                            line = line[5:].strip()
                        if not line:
                            continue
                        if line == "[DONE]":
                            break

                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue

                        tok = None
                        try:
                            ch = (obj.get("choices") or [{}])[0]
                            delta = ch.get("delta") or {}
                            tok = delta.get("content")
                        except Exception:
                            tok = None

                        if tok is None:
                            continue

                        if isinstance(tok, list):
                            tok = "".join(str(x) for x in tok)
                        elif isinstance(tok, (bytes, bytearray)):
                            tok = bytes(tok).decode("utf-8", errors="ignore")
                        elif not isinstance(tok, str):
                            tok = str(tok)

                        if not tok:
                            continue

                        full_parts.append(tok)
                        stream_buf += tok

                        # AWARYJNIE: jak ktoś wygeneruje gigantyczny tekst, to nie trzymamy w RAM w nieskończoność
                        if len(stream_buf) >= hard_max_buf and chunk_mode != "final":
                            yield _sse("delta", stream_buf)
                            stream_buf = ""

        except Exception as e:
            yield _sse("error", str(e))

        final = (stream_buf + "".join(full_parts)).strip() if not stream_buf else stream_buf.strip()
        if not final:
            final = "".join(full_parts).strip()

        if final:
            # final = jedno delta na koniec
            yield _sse("delta", final)

        try:
            _append = globals().get("_append_msg")
            if con is not None and callable(_append) and final:
                _append(con, sid, uid, "assistant", final)
        except Exception:
            pass

        _safe_close()
        yield _sse("done", {"ok": True})

    return StreamingResponse(gen(), media_type="text/event-stream")

