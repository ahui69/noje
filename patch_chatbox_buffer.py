#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys
from pathlib import Path

REPL = """
@router.post("/chat/completions")
async def chat_completions(req: Request):
    import os
    import json
    import time
    import uuid
    from typing import Any, Dict, AsyncIterator, Optional

    import httpx
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse, StreamingResponse

    expected = (os.getenv("AUTH_TOKEN") or "").strip()
    if expected:
        hdr = (req.headers.get("authorization") or "").strip()
        if not hdr.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")
        got = hdr.split(" ", 1)[1].strip()
        if got != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    body = await req.json()

    base_url = (os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "").strip().rstrip("/")
    api_key = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    env_model = (os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "").strip()

    if not base_url:
        base_url = "https://api.deepinfra.com/v1/openai"
    if not env_model:
        env_model = "NousResearch/Hermes-3-Llama-3.1-405B"

    model = str(body.get("model") or env_model)
    messages = body.get("messages") or []
    stream = bool(body.get("stream") or False)

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(body.get("temperature", 0.7) or 0.7),
        "max_tokens": int(body.get("max_tokens", 2000) or 2000),
        "top_p": float(body.get("top_p", 0.9) or 0.9),
        "stream": stream,
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout_s = float(os.getenv("CHAT_STREAM_TIMEOUT_S", "180"))
    timeout = httpx.Timeout(timeout=timeout_s, connect=20.0, read=timeout_s)

    if not stream:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            if r.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Upstream HTTP {r.status_code}: {r.text[:1200]}")
            return JSONResponse(r.json())

    keepalive_ms = int(os.getenv("CHATBOX_KEEPALIVE_MS", "250"))
    flush_ms = int(os.getenv("CHATBOX_FLUSH_MS", "700"))
    max_silence_ms = int(os.getenv("CHATBOX_MAX_SILENCE_MS", "1200"))
    min_chars = int(os.getenv("CHATBOX_MIN_CHARS", "180"))
    hard_chars = int(os.getenv("CHATBOX_HARD_CHARS", "1800"))

    boundary_hard = ".!?\n"
    boundary_soft = ",;:)]}\\\"' "

    def _sse_data(payload_str: str) -> str:
        return f"data: {payload_str}\\n\\n"

    def _sse_comment(msg: str) -> str:
        return f": {msg}\\n\\n"

    def _coerce_tok(tok: Any) -> str:
        if tok is None:
            return ""
        if isinstance(tok, list):
            return "".join(str(x) for x in tok)
        if isinstance(tok, (bytes, bytearray)):
            return bytes(tok).decode("utf-8", errors="ignore")
        if isinstance(tok, str):
            return tok
        return str(tok)

    def _find_last_boundary(buf: str, chars: str) -> int:
        last = -1
        for ch in chars:
            i = buf.rfind(ch)
            if i > last:
                last = i
        return last

    async def gen() -> AsyncIterator[str]:
        created = int(time.time())
        chat_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"

        buf = ""
        last_emit = time.monotonic()
        next_keepalive = time.monotonic() + (keepalive_ms / 1000.0)

        def emit_chunk(text: str) -> str:
            chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
            }
            return _sse_data(json.dumps(chunk, ensure_ascii=False))

        def maybe_flush(force: bool) -> Optional[str]:
            nonlocal buf, last_emit
            if not buf:
                return None

            now = time.monotonic()
            age_ms = int((now - last_emit) * 1000.0)

            if force:
                out = buf
                buf = ""
                last_emit = now
                return out

            if len(buf) >= hard_chars:
                window = buf[:hard_chars]
                idx = _find_last_boundary(window, boundary_hard)
                if idx < 0:
                    idx = _find_last_boundary(window, boundary_soft)
                if idx < 0:
                    for i in range(hard_chars - 1, -1, -1):
                        if window[i].isspace():
                            idx = i
                            break
                if idx < 0:
                    idx = hard_chars - 1
                out = buf[: idx + 1]
                buf = buf[idx + 1 :]
                last_emit = now
                return out

            if age_ms >= flush_ms and len(buf) >= min_chars:
                idx = _find_last_boundary(buf, boundary_hard)
                if idx >= 0 and (idx + 1) >= min_chars:
                    out = buf[: idx + 1]
                    buf = buf[idx + 1 :]
                    last_emit = now
                    return out

            if age_ms >= max_silence_ms and len(buf) >= (min_chars * 2):
                idx = _find_last_boundary(buf, boundary_soft)
                if idx >= 0 and (idx + 1) >= min_chars:
                    out = buf[: idx + 1]
                    buf = buf[idx + 1 :]
                    last_emit = now
                    return out

            return None

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{base_url}/chat/completions", headers=headers, json=payload) as r:
                if r.status_code != 200:
                    raw = (await r.aread()).decode("utf-8", errors="ignore")
                    err = {
                        "id": chat_id,
                        "object": "error",
                        "created": created,
                        "model": model,
                        "error": {"message": raw[:1200], "type": "upstream_error"},
                    }
                    yield _sse_data(json.dumps(err, ensure_ascii=False))
                    yield _sse_data("[DONE]")
                    return

                async for line in r.aiter_lines():
                    now = time.monotonic()
                    if now >= next_keepalive:
                        next_keepalive = now + (keepalive_ms / 1000.0)
                        yield _sse_comment("keepalive")

                    if not line:
                        out = maybe_flush(False)
                        if out:
                            yield emit_chunk(out)
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

                    t = _coerce_tok(tok)
                    if t:
                        buf += t

                    while True:
                        out = maybe_flush(False)
                        if not out:
                            break
                        yield emit_chunk(out)

                out = maybe_flush(True)
                if out:
                    yield emit_chunk(out)

        yield _sse_data("[DONE]")

    return StreamingResponse(gen(), media_type="text/event-stream")
""".lstrip("\n")


def main() -> int:
    target = Path("/root/mrd/openai_compat.py")
    if not target.exists():
        print("Brak /root/mrd/openai_compat.py", file=sys.stderr)
        return 2

    s = target.read_text(encoding="utf-8")

    pat = re.compile(
        r'(?ms)^[ \t]*@router\.post\(\s*[\'"]\/chat\/completions[\'"]\s*\).*?'
        r'^[ \t]*(?:async\s+def|def)\s+\w+\s*\(.*?\):.*?(?=^[ \t]*@router\.|\Z)'
    )
    m = pat.search(s)
    if not m:
        print('Nie znaleziono @router.post("/chat/completions") w openai_compat.py', file=sys.stderr)
        return 3

    backup = target.with_suffix(".py.bak.chatboxbuf")
    backup.write_text(s, encoding="utf-8")

    s2 = s[:m.start()] + REPL + "\n" + s[m.end():]
    target.write_text(s2, encoding="utf-8")

    print("OK: spatchowano", str(target))
    print("Backup:", str(backup))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
