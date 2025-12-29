#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision Provider - Universal Image Analysis
Wspiera: OpenAI Vision, Google Vision AI, lokalne modele
"""

import os
import base64
import httpx
from typing import Optional, Dict, Any
from core.config import *
from core.helpers import log_error, log_info


async def analyze_image_universal(
    base64_data: str,
    mime_type: str = "image/png",
    filename: str = "image.png",
    prompt: str = "Opisz dokładnie co widzisz na tym obrazie. Podaj szczegóły, kolory, obiekty, tekst jeśli jest."
) -> Optional[str]:
    """
    Uniwersalna analiza obrazów - próbuje różne providery

    Args:
        base64_data: Obraz w base64
        mime_type: Typ MIME obrazu
        filename: Nazwa pliku
        prompt: Prompt dla analizy

    Returns:
        Opis obrazu lub None jeśli błąd
    """
    try:
        # 1. Spróbuj OpenAI Vision
        result = await _analyze_openai_vision(base64_data, mime_type, prompt)
        if result:
            return result

        # 2. Spróbuj Google Vision AI
        result = await _analyze_google_vision(base64_data, prompt)
        if result:
            return result

        # 3. Fallback - podstawowa analiza (OCR jeśli tekst)
        result = await _analyze_basic(base64_data, mime_type, filename)
        return result

    except Exception as e:
        log_error(f"Vision analysis failed: {e}", "VISION")
        return None


async def _analyze_openai_vision(base64_data: str, mime_type: str, prompt: str) -> Optional[str]:
    """Analiza przez OpenAI Vision API"""
    try:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None

        url = "https://api.openai.com/v1/chat/completions"

        # Przygotuj wiadomość z obrazem
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_data}"
                        }
                    }
                ]
            }
        ]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4-vision-preview",
            "messages": messages,
            "max_tokens": 500
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            log_info("OpenAI Vision analysis completed", "VISION")
            return content

    except Exception as e:
        log_error(f"OpenAI Vision failed: {e}", "VISION")
        return None


async def _analyze_google_vision(base64_data: str, prompt: str) -> Optional[str]:
    """Analiza przez Google Vision AI"""
    try:
        api_key = os.getenv("GOOGLE_VISION_API_KEY", "").strip()
        if not api_key:
            return None

        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

        # Zakoduj obraz ponownie dla Google
        image_data = {
            "content": base64_data
        }

        features = [
            {
                "type": "LABEL_DETECTION",
                "maxResults": 10
            },
            {
                "type": "TEXT_DETECTION",
                "maxResults": 1
            },
            {
                "type": "IMAGE_PROPERTIES"
            }
        ]

        data = {
            "requests": [
                {
                    "image": image_data,
                    "features": features
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()

            result = response.json()

            # Parsuj wyniki
            annotations = result["responses"][0]

            description = []

            # Labels
            if "labelAnnotations" in annotations:
                labels = [label["description"] for label in annotations["labelAnnotations"][:5]]
                description.append(f"Etykiety: {', '.join(labels)}")

            # Text
            if "textAnnotations" in annotations:
                text = annotations["textAnnotations"][0]["description"]
                description.append(f"Tekst: {text[:200]}...")

            # Colors
            if "imagePropertiesAnnotation" in annotations:
                colors = annotations["imagePropertiesAnnotation"]["dominantColors"]["colors"][:3]
                color_names = []
                for color in colors:
                    rgb = color["color"]
                    color_names.append(f"RGB({rgb.get('red', 0)}, {rgb.get('green', 0)}, {rgb.get('blue', 0)})")
                description.append(f"Kolory dominujące: {', '.join(color_names)}")

            final_desc = " | ".join(description)
            log_info("Google Vision analysis completed", "VISION")
            return final_desc

    except Exception as e:
        log_error(f"Google Vision failed: {e}", "VISION")
        return None


async def _analyze_basic(base64_data: str, mime_type: str, filename: str) -> Optional[str]:
    """Podstawowa analiza - tylko OCR jeśli dostępny"""
    try:
        # Spróbuj OCR z pytesseract jeśli zainstalowany
        try:
            import pytesseract
            from PIL import Image
            import io

            # Dekoduj base64 do PIL Image
            image_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_data))

            # Wykonaj OCR
            text = pytesseract.image_to_string(image, lang='pol+eng')

            if text.strip():
                return f"Wykryty tekst: {text.strip()}"
            else:
                return f"Obraz {filename} - nie wykryto tekstu (OCR)"

        except ImportError:
            return f"Obraz {filename} - analiza niedostępna (brak pytesseract)"

    except Exception as e:
        log_error(f"Basic vision analysis failed: {e}", "VISION")
        return f"Obraz {filename} - błąd analizy"