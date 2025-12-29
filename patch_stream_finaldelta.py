#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys

REPL = r'''@router.post("/assistant/stream")
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
'''

def main() -> int:
    p = Path("/root/mrd/assistant_simple.py")
    s = p.read_text(encoding="utf-8")

    pat = re.compile(
        r'(?ms)^[ \t]*@router\.post\(\s*[\'"]\/assistant\/stream[\'"]\s*\)\s*\n'
        r'^[ \t]*async\s+def\s+chat_assistant_stream\b.*?(?=^\s*@router\.|\Z)'
    )
    m = pat.search(s)
    if not m:
        print('Nie znalazłem endpointa @router.post("/assistant/stream") w assistant_simple.py', file=sys.stderr)
        return 2

    s2 = s[:m.start()] + REPL + "\n" + s[m.end():]
    p.write_text(s2, encoding="utf-8")
    print("OK: /assistant/stream ustawiony na final-delta (jedna wypowiedź)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
