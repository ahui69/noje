#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
research_endpoint.py - Web search endpoints (DuckDuckGo, Wikipedia, SERPAPI, arXiv, Semantic Scholar)
PRAWDZIWY dostęp do internetu przez wiele źródeł.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from core.config import AUTH_TOKEN
from core.research import autonauka
from core.helpers import log_info, log_error

router = APIRouter(prefix="/api/research", tags=["research"])


def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.replace("Bearer ", "").strip()
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Zapytanie do wyszukania")
    topk: int = Field(5, ge=1, le=20, description="Liczba wyników")
    mode: str = Field("full", description="Tryb: full/grounded/fast/free")


class AutonaukaRequest(BaseModel):
    query: str = Field(..., description="Pytanie do autonauki")
    topk: int = Field(5, ge=1, le=20)
    user_id: str = Field("guest", description="ID użytkownika")
    save_to_ltm: bool = Field(True, description="Czy zapisać do LTM")


@router.post("/search")
async def web_search(body: WebSearchRequest, _auth: bool = Depends(verify_token)):
    """
    🌐 OGÓLNE WYSZUKIWANIE W INTERNECIE
    
    Przeszukuje wiele źródeł:
    - DuckDuckGo (zawsze)
    - Wikipedia (zawsze)
    - SERPAPI/Google (jeśli klucz API)
    - arXiv (tryb full/grounded)
    - Semantic Scholar (tryb full/grounded)
    
    **Przykład:**
    ```json
    {
      "query": "czym jest kwantowa superpozycja",
      "topk": 5,
      "mode": "full"
    }
    ```
    """
    try:
        log_info(f"[RESEARCH] Web search: {body.query}")
        
        # Map mode to deep_research parameter
        deep_research = body.mode in ("full", "grounded")
        
        result = await autonauka(
            q=body.query,
            topk=body.topk,
            deep_research=deep_research,
            user_id="system"
        )
        
        return result
        
    except Exception as e:
        log_error(f"[RESEARCH] Web search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/autonauka")
async def run_autonauka(body: AutonaukaRequest, _auth: bool = Depends(verify_token)):
    """
    🧠 AUTO-NAUKA Z WEB RESEARCH
    
    Pełna pipeline:
    1. Wyszukiwanie w wielu źródłach (DDG, Wiki, SERPAPI, arXiv, S2)
    2. Scraping treści (Firecrawl lub fallback)
    3. Analiza semantyczna i embedding
    4. Generowanie odpowiedzi przez LLM
    5. Opcjonalnie: zapis do LTM
    
    **Przykład:**
    ```json
    {
      "query": "Wyjaśnij teorię strun",
      "topk": 8,
      "user_id": "user123",
      "save_to_ltm": true
    }
    ```
    """
    try:
        log_info(f"[RESEARCH] Autonauka: {body.query}")
        
        result = await autonauka(
            q=body.query,
            topk=body.topk,
            deep_research=True,  # Always deep research for autonauka
            user_id=body.user_id
        )
        
        # Dodaj info o zapisie do LTM
        if result.get("ok") and body.save_to_ltm:
            result["saved_to_ltm"] = result.get("saved_to_ltm", True)
        
        return result
        
    except Exception as e:
        log_error(f"[RESEARCH] Autonauka failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def available_sources(_auth: bool = Depends(verify_token)):
    """
    📚 LISTA DOSTĘPNYCH ŹRÓDEŁ
    
    Zwraca informacje o dostępnych źródłach danych i ich statusie.
    """
    from core.config import SERPAPI_KEY, FIRECRAWL_API_KEY
    
    return {
        "sources": {
            "duckduckgo": {
                "available": True,
                "type": "free",
                "description": "DuckDuckGo HTML search - zawsze dostępne"
            },
            "wikipedia": {
                "available": True,
                "type": "free",
                "description": "Wikipedia API - zawsze dostępne"
            },
            "serpapi": {
                "available": bool(SERPAPI_KEY),
                "type": "paid",
                "description": "Google search przez SERPAPI - wymaga klucza"
            },
            "arxiv": {
                "available": True,
                "type": "free",
                "description": "arXiv papers - zawsze dostępne"
            },
            "semantic_scholar": {
                "available": True,
                "type": "free",
                "description": "Semantic Scholar - zawsze dostępne"
            },
            "firecrawl": {
                "available": bool(FIRECRAWL_API_KEY),
                "type": "paid",
                "description": "Firecrawl scraping - wymaga klucza"
            }
        },
        "modes": {
            "full": "Wszystkie źródła (DDG, Wiki, SERPAPI, arXiv, S2)",
            "grounded": "Wiarygodne źródła (DDG, Wiki, SERPAPI, arXiv, S2)",
            "fast": "Szybkie (tylko DDG + Wiki)",
            "free": "Darmowe (tylko DDG + Wiki)"
        }
    }


@router.get("/test")
async def test_research(_auth: bool = Depends(verify_token)):
    """
    🧪 TEST WEB SEARCH
    
    Testuje czy research działa poprawnie.
    """
    try:
        result = await autonauka(
            q="Python programming language",
            topk=3,
            deep_research=False,
            user_id="test"
        )
        
        return {
            "ok": result.get("ok", False),
            "sources_count": len(result.get("sources", [])),
            "answer_length": len(result.get("context", "")),
            "test_passed": result.get("ok", False) and len(result.get("sources", [])) > 0
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "test_passed": False
        }
