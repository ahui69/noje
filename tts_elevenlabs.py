#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ElevenLabs TTS Provider - Text-to-Speech
Wspiera polskie głosy i różne języki
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from core.config import *
from core.helpers import log_error, log_info


# Dostępne polskie głosy ElevenLabs
POLISH_VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",  # Rachel - kobiecy, naturalny
    "antoni": "ErXwobaYiN019PkySvjV",  # Antoni - męski, profesjonalny
    "adam": "pNInz6obpgDQGcFmaJgB",   # Adam - męski, przyjazny
    "bella": "EXAVITQu4vr4xnSDxMaL",   # Bella - kobiecy, młoda
    "darek": "7QSNr9zM4s8Vy3h6gM2Y",  # Darek - męski, głęboki
    "ewa": "29vD33N1CtxCmqQRPOHJ",    # Ewa - kobiecy, dojrzały
    "jan": "AZnzlk1XvdvUeBnXmlld",    # Jan - męski, neutralny
    "maja": "9BWtsMINqrJLr0FYiFns",   # Maja - kobiecy, energiczny
}


async def text_to_speech(
    text: str,
    voice_id: str = "rachel",
    model: str = "eleven_monolingual_v1",
    voice_settings: Optional[Dict[str, Any]] = None
) -> Optional[bytes]:
    """
    Konwertuj tekst na mowę używając ElevenLabs

    Args:
        text: Tekst do konwersji
        voice_id: ID głosu (domyślnie Rachel)
        model: Model TTS
        voice_settings: Ustawienia głosu (stability, similarity_boost, style, use_speaker_boost)

    Returns:
        Audio data jako bytes lub None jeśli błąd
    """
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not api_key:
            log_error("ELEVENLABS_API_KEY not set", "TTS")
            return None

        # Jeśli voice_id to nazwa, zamień na ID
        if voice_id in POLISH_VOICES:
            voice_id = POLISH_VOICES[voice_id]

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }

        # Domyślne ustawienia głosu
        if voice_settings is None:
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }

        data = {
            "text": text,
            "model_id": model,
            "voice_settings": voice_settings
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()

            audio_data = response.content
            log_info(f"TTS generated {len(audio_data)} bytes for text: {text[:50]}...", "TTS")
            return audio_data

    except Exception as e:
        log_error(f"ElevenLabs TTS failed: {e}", "TTS")
        return None


async def get_voices() -> List[Dict[str, Any]]:
    """
    Pobierz listę dostępnych głosów z ElevenLabs

    Returns:
        Lista głosów z ich właściwościami
    """
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not api_key:
            return []

        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "xi-api-key": api_key
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            voices = data.get("voices", [])
            log_info(f"Retrieved {len(voices)} voices from ElevenLabs", "TTS")
            return voices

    except Exception as e:
        log_error(f"Failed to get ElevenLabs voices: {e}", "TTS")
        return []


def get_polish_voice_id(voice_name: str) -> Optional[str]:
    """
    Pobierz ID głosu po nazwie polskiej

    Args:
        voice_name: Nazwa głosu (rachel, antoni, itp.)

    Returns:
        Voice ID lub None jeśli nie znaleziono
    """
    return POLISH_VOICES.get(voice_name.lower())