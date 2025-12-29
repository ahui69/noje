#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/tts", tags=["tts"])

ELEVENLABS_API_KEY = (os.getenv("ELEVENLABS_API_KEY") or "").strip()
ELEVENLABS_VOICE_ID = (os.getenv("ELEVENLABS_VOICE_ID") or "").strip()
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


def _now() -> float:
    return time.time()


def _auth_headers() -> Dict[str, str]:
    if not ELEVENLABS_API_KEY:
        return {"Content-Type": "application/json"}
    return {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}


def _require_cfg() -> Optional[str]:
    if not ELEVENLABS_API_KEY:
        return "Brak ELEVENLABS_API_KEY w środowisku"
    if not ELEVENLABS_VOICE_ID:
        return "Brak ELEVENLABS_VOICE_ID w środowisku"
    return None


class TTSSpeakBody(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    model_id: str = Field(default="eleven_multilingual_v2", min_length=1, max_length=200)
    stability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    similarity_boost: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    style: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    use_speaker_boost: Optional[bool] = Field(default=None)


@router.get("/voices")
async def list_voices(_: Request) -> Dict[str, Any]:
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY nie jest ustawiony")

    url = f"{ELEVENLABS_BASE}/voices"
    timeout = httpx.Timeout(timeout=40.0, connect=20.0, read=40.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, headers=_auth_headers())
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"ElevenLabs error ({r.status_code}): {r.text[:800]}")
        data = r.json()

    voices = []
    for v in (data.get("voices") or []):
        voices.append(
            {
                "voice_id": v.get("voice_id"),
                "name": v.get("name"),
                "category": v.get("category"),
                "labels": v.get("labels") or {},
                "preview_url": v.get("preview_url"),
            }
        )

    return {"ok": True, "count": len(voices), "voices": voices, "ts": _now()}


@router.post("/speak")
async def speak(_: Request, body: TTSSpeakBody) -> Response:
    err = _require_cfg()
    if err:
        raise HTTPException(status_code=500, detail=err)

    url = f"{ELEVENLABS_BASE}/text-to-speech/{ELEVENLABS_VOICE_ID}"
    payload: Dict[str, Any] = {
        "text": body.text,
        "model_id": body.model_id,
    }

    settings: Dict[str, Any] = {}
    if body.stability is not None:
        settings["stability"] = float(body.stability)
    if body.similarity_boost is not None:
        settings["similarity_boost"] = float(body.similarity_boost)
    if body.style is not None:
        settings["style"] = float(body.style)
    if body.use_speaker_boost is not None:
        settings["use_speaker_boost"] = bool(body.use_speaker_boost)
    if settings:
        payload["voice_settings"] = settings

    timeout = httpx.Timeout(timeout=120.0, connect=20.0, read=120.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            url,
            headers={**_auth_headers(), "Accept": "audio/mpeg"},
            json=payload,
        )

        if r.status_code != 200:
            # ElevenLabs czasem zwraca JSON błędu
            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    j = r.json()
                    msg = json.dumps(j, ensure_ascii=False)[:1200]
                except Exception:
                    msg = r.text[:1200]
            else:
                msg = r.text[:1200]
            raise HTTPException(status_code=502, detail=f"ElevenLabs error ({r.status_code}): {msg}")

        audio = r.content

    # Stabilny zwrot mp3
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'inline; filename="tts.mp3"',
            "X-TTS-Provider": "elevenlabs",
            "X-TTS-Voice-Id": ELEVENLABS_VOICE_ID,
        },
    )


@router.get("/status")
async def status(_: Request) -> Dict[str, Any]:
    return {
        "ok": True,
        "provider": "elevenlabs",
        "voice_id_set": bool(ELEVENLABS_VOICE_ID),
        "api_key_set": bool(ELEVENLABS_API_KEY),
        "ts": _now(),
    }
# @# router.exception_handler(HTTPException)  # disabled: APIRouter has no exception_handler
async def _http_exc(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
