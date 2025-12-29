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

    # jeżeli projekt ma globalne stałe - preferuj je (bez wywalania jeśli nie ma)
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

    # --- stream tuning ---
    ping_ms = int(os.getenv("CHAT_STREAM_PING_MS", "200"))
    flush_chars = int(os.getenv("CHAT_STREAM_FLUSH_CHARS", "1800"))      # twardy limit
    flush_ms = float(os.getenv("CHAT_STREAM_FLUSH_MS", "700"))           # limit czasowy
    min_chars = int(os.getenv("CHAT_STREAM_MIN_CHARS", "220"))           # minimalny sensowny kawałek

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
            cleaned = [{"role": "user", "content": " "}]  # minimalnie niepuste, żeby upstream nie wywalił

    messages: List[Dict[str, str]] = []
    if sys_prompt:
        messages.append({"role": "system", "content": sys_prompt})
    # nie dubluj system promptów z usera
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

    # --- DB/session best-effort ---
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

        # sesja
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

        # meta
        yield _sse("meta", {"session_id": sid, "ts": _now(), "model": model})

        stream_buf = ""
        full_parts: List[str] = []
        last_flush = time.monotonic()
        next_ping = time.monotonic() + (ping_ms / 1000.0)

        boundary_hard = {".", "!", "?", "\n"}
        boundary_soft = {",", ";", ":", ")", "]", '"', "'"}
        # spacja też jest granicą, ale nie chcemy flushować co słowo -> używamy jej tylko przy długim buforze

        def should_flush(force: bool) -> bool:
            nonlocal last_flush, stream_buf
            if not stream_buf:
                return False
            if force:
                return True

            # twardy limit rozmiaru: tu flush może wypaść "w środku", ale to jest awaryjne
            if len(stream_buf) >= flush_chars:
                return True

            now = time.monotonic()

            # time-based: flush dopiero gdy bufor ma sensowny rozmiar i kończy się na twardej granicy
            if (now - last_flush) * 1000.0 >= flush_ms and len(stream_buf) >= min_chars:
                last = stream_buf[-1]
                if last in boundary_hard:
                    return True

                # jeśli już jest bardzo długie, pozwól na miękką granicę albo spację
                if len(stream_buf) >= (min_chars * 2):
                    if last.isspace() or last in boundary_soft:
                        return True

            return False

        def emit_delta(force: bool) -> Optional[str]:
            nonlocal stream_buf, last_flush
            if should_flush(force):
                out = stream_buf
                stream_buf = ""
                last_flush = time.monotonic()
                return out
            return None

        def maybe_ping() -> Optional[Dict[str, Any]]:
            nonlocal next_ping
            now = time.monotonic()
            if now >= next_ping:
                next_ping = now + (ping_ms / 1000.0)
                return {"ts": _now()}
            return None

        try:
            # upstream call
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
                        # ping nawet gdy cisza
                        p = maybe_ping()
                        if p is not None:
                            yield _sse("ping", p)

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

                        out = emit_delta(False)
                        if out is not None:
                            yield _sse("delta", out)

            # flush końcowy
            out = emit_delta(True)
            if out is not None:
                yield _sse("delta", out)

        except Exception as e:
            yield _sse("error", str(e))

        final = "".join(full_parts).strip()

        # zapis assistant msg (best-effort)
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

    # Wytnij cały blok endpointa /assistant/stream
    pat = re.compile(
        r'(?ms)^[ \t]*@router\.post\(\s*[\'"]\/assistant\/stream[\'"]\s*\)\s*\n'
        r'^[ \t]*async\s+def\s+chat_assistant_stream\b.*?(?=^\s*@router\.|\Z)'
    )
    m = pat.search(s)
    if not m:
        print("Nie znalazłem endpointa @router.post(\"/assistant/stream\") w assistant_simple.py", file=sys.stderr)
        return 2

    s2 = s[:m.start()] + REPL + "\n" + s[m.end():]
    p.write_text(s2, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
