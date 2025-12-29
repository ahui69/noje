#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat_advanced_endpoint.py — router "Chat (Advanced) [core]".

Wymagania:
- eksportuje `router: APIRouter`
- NIE robi circular import z app/main
- działa nawet jeśli część modułów jest nieobecna
"""

from __future__ import annotations

import asyncio
import importlib
from typing import Any, AsyncIterator, Callable, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .advanced_cognitive_engine import (
    CognitiveRequest,
    CognitiveResult,
    CognitiveMode,
    get_engine,
)

router = APIRouter(prefix="/core/chat/advanced", tags=["core-chat-advanced"])


def _resolve_llm_call() -> Optional[Callable[..., Any]]:
    """
    Szuka funkcji LLM w repo bez zabijania importów.
    Obsługiwane sygnatury (przykładowe):
      - call_llm(messages, **params)
      - chat_completion(messages, **params)
      - completion(messages, **params)
    """
    candidates = [
        ("core.llm", "call_llm"),
        ("core.llm", "chat_completion"),
        ("core.llm", "completion"),
        ("core.llm_client", "call_llm"),
        ("core.openai_client", "chat_completion"),
        ("llm", "call_llm"),
    ]
    for mod_name, fn_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                return fn
        except Exception:
            continue
    return None


def _engine() -> Any:
    eng = get_engine()
    if getattr(eng, "llm_call", None) is None:
        fn = _resolve_llm_call()
        if fn is not None:
            eng.set_llm_call(fn)
    return eng


def _to_openai_response(text: str, model: str = "mrd-advanced") -> Dict[str, Any]:
    # OpenAI-compatible minimal chat.completions
    return {
        "id": "mrd-adv",
        "object": "chat.completion",
        "created": int(__import__("time").time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


async def _sse_stream_text(text: str) -> AsyncIterator[bytes]:
    """
    Stabilny fallback streaming (SSE), nawet jeśli LLM nie streamuje.
    Dzieli odpowiedź na kawałki, żeby front miał "życie".
    """
    # start
    yield b"event: message\ndata: {\"type\":\"start\"}\n\n"

    # chunking
    chunk_size = 40
    for i in range(0, len(text), chunk_size):
        part = text[i : i + chunk_size]
        payload = {"choices": [{"delta": {"content": part}, "index": 0, "finish_reason": None}]}
        yield ("data: " + __import__("json").dumps(payload, ensure_ascii=False) + "\n\n").encode("utf-8")
        await asyncio.sleep(0)

    # end
    end_payload = {"choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]}
    yield ("data: " + __import__("json").dumps(end_payload, ensure_ascii=False) + "\n\n").encode("utf-8")
    yield b"data: [DONE]\n\n"


@router.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "component": "chat_advanced"}


@router.post("")
async def chat_advanced(req: Request) -> JSONResponse:
    """
    Przyjmuje:
    - CognitiveRequest (prompt/messages/mode/context/params)
    - albo OpenAI-like {messages:[{role,content}], temperature, max_tokens, stream}
    Zwraca: CognitiveResult dict (twoje API)
    """
    payload = await req.json()
    try:
        cr = CognitiveRequest(**payload)
    except Exception:
        # fallback: minimal OpenAI-like mapowanie
        msgs = payload.get("messages") or []
        mode = payload.get("mode")
        cr = CognitiveRequest(
            messages=msgs,
            prompt=payload.get("prompt") or "",
            mode=mode,
            temperature=payload.get("temperature"),
            top_p=payload.get("top_p"),
            max_tokens=payload.get("max_tokens"),
            stream=bool(payload.get("stream") or False),
            context=payload.get("context") or {},
            user_id=payload.get("user_id"),
            session_id=payload.get("session_id"),
        )

    eng = _engine()
    result = await eng.process_request(cr)

    out = CognitiveResult(
        ok=True,
        mode=cr.parsed_mode().value,
        output=result.response,
        data={
            "metadata": result.metadata,
            "analysis": result.analysis,
            "memory": result.memory,
        },
        error=None,
    )
    return JSONResponse(out.as_dict())


@router.post("/openai")
async def chat_advanced_openai(req: Request) -> JSONResponse:
    """
    OpenAI-compatible odpowiedź (chat.completions) dla prostych klientów.
    """
    payload = await req.json()
    try:
        cr = CognitiveRequest(**payload)
    except Exception:
        cr = CognitiveRequest(
            messages=payload.get("messages") or [],
            prompt=payload.get("prompt") or "",
            mode=payload.get("mode"),
            temperature=payload.get("temperature"),
            top_p=payload.get("top_p"),
            max_tokens=payload.get("max_tokens"),
            stream=bool(payload.get("stream") or False),
            context=payload.get("context") or {},
            user_id=payload.get("user_id"),
            session_id=payload.get("session_id"),
        )

    eng = _engine()
    result = await eng.process_request(cr)
    return JSONResponse(_to_openai_response(result.response))


@router.post("/stream")
async def chat_advanced_stream(req: Request) -> StreamingResponse:
    """
    SSE stream (OpenAI-style).
    Jeśli twój llm_call potrafi streamować, nadal masz sensowny fallback.
    """
    payload = await req.json()
    try:
        cr = CognitiveRequest(**payload)
    except Exception:
        cr = CognitiveRequest(
            messages=payload.get("messages") or [],
            prompt=payload.get("prompt") or "",
            mode=payload.get("mode"),
            temperature=payload.get("temperature"),
            top_p=payload.get("top_p"),
            max_tokens=payload.get("max_tokens"),
            stream=True,
            context=payload.get("context") or {},
            user_id=payload.get("user_id"),
            session_id=payload.get("session_id"),
        )

    eng = _engine()
    result = await eng.process_request(cr)
    return StreamingResponse(_sse_stream_text(result.response), media_type="text/event-stream")
