#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STT (Speech-to-Text) Endpoint - konwersja audio na tekst
Wspiera: OpenAI Whisper, DeepInfra, Groq
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import base64

router = APIRouter(prefix="/api/stt", tags=["speech"])

class STTResponse(BaseModel):
    ok: bool
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None

@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Zamień audio na tekst (Speech-to-Text)
    
    Wspierane formaty: mp3, wav, m4a, webm, ogg
    Max size: 25MB
    """
    
    # Sprawdź rozmiar
    content = await audio.read()
    if len(content) > 25 * 1024 * 1024:  # 25MB
        raise HTTPException(400, "File too large (max 25MB)")
    
    # Sprawdź format
    allowed_types = ['audio/mpeg', 'audio/wav', 'audio/webm', 'audio/ogg', 'audio/m4a']
    if audio.content_type not in allowed_types and not audio.filename.endswith(('.mp3', '.wav', '.m4a', '.webm', '.ogg')):
        raise HTTPException(400, f"Unsupported format. Use: mp3, wav, m4a, webm, ogg")
    
    # 1. TRY OPENAI WHISPER (najlepsze)
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and not openai_key.endswith('...'):
            print("🎤 Próbuję OpenAI Whisper...")
            
            async with httpx.AsyncClient(timeout=60) as client:
                files = {
                    'file': (audio.filename, content, audio.content_type),
                    'model': (None, 'whisper-1'),
                    'language': (None, 'pl')  # Polski domyślnie
                }
                
                resp = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    files=files
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    text = result.get('text', '')
                    print(f"✅ OpenAI Whisper: {text[:50]}...")
                    
                    return STTResponse(
                        ok=True,
                        text=text,
                        language=result.get('language', 'pl')
                    )
    except Exception as e:
        print(f"❌ OpenAI Whisper: {e}")
    
    # 2. TRY GROQ WHISPER (darmowe, szybkie)
    try:
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            print("🎤 Próbuję Groq Whisper...")
            
            async with httpx.AsyncClient(timeout=60) as client:
                files = {
                    'file': (audio.filename, content, audio.content_type),
                    'model': (None, 'whisper-large-v3'),
                    'language': (None, 'pl')
                }
                
                resp = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    files=files
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    text = result.get('text', '')
                    print(f"✅ Groq Whisper: {text[:50]}...")
                    
                    return STTResponse(
                        ok=True,
                        text=text,
                        language='pl'
                    )
    except Exception as e:
        print(f"❌ Groq Whisper: {e}")
    
    # 3. TRY DEEPINFRA
    try:
        deepinfra_key = os.getenv('LLM_API_KEY')
        if deepinfra_key:
            print("🎤 Próbuję DeepInfra Whisper...")
            
            # DeepInfra wymaga base64
            audio_b64 = base64.b64encode(content).decode()
            
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.deepinfra.com/v1/inference/openai/whisper-large-v3",
                    headers={
                        "Authorization": f"Bearer {deepinfra_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "audio": audio_b64,
                        "language": "pl"
                    }
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    text = result.get('text', '')
                    print(f"✅ DeepInfra Whisper: {text[:50]}...")
                    
                    return STTResponse(
                        ok=True,
                        text=text,
                        language='pl'
                    )
    except Exception as e:
        print(f"❌ DeepInfra Whisper: {e}")
    
    raise HTTPException(500, "Wszystkie STT providery failed. Skonfiguruj OPENAI_API_KEY lub GROQ_API_KEY w .env")


@router.get("/providers")
async def list_stt_providers():
    """Lista dostępnych providerów STT"""
    
    providers = []
    
    if os.getenv('OPENAI_API_KEY'):
        providers.append({
            "name": "OpenAI Whisper",
            "model": "whisper-1",
            "quality": "excellent",
            "speed": "fast"
        })
    
    if os.getenv('GROQ_API_KEY'):
        providers.append({
            "name": "Groq Whisper",
            "model": "whisper-large-v3",
            "quality": "excellent",
            "speed": "very_fast",
            "free": True
        })
    
    if os.getenv('LLM_API_KEY'):
        providers.append({
            "name": "DeepInfra Whisper",
            "model": "whisper-large-v3",
            "quality": "good",
            "speed": "medium"
        })
    
    return {
        "ok": True,
        "providers": providers,
        "count": len(providers)
    }
