"""
🧠 ENDPOINTY NLP (Natural Language Processing)
=============================================

API endpoints dla przetwarzania języka naturalnego z użyciem spaCy.
Udostępnia funkcje analizy tekstu, ekstrakcji encji, analizy sentymentu itp.

Autor: Zaawansowany System Kognitywny ahui69
Data: 19 października 2025
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import time

from core.nlp_processor import get_nlp_processor
from core.config import AUTH_TOKEN
from core.helpers import log_info, log_error

# Utwórz router
router = APIRouter(prefix="/api/nlp", tags=["nlp"])

# Modele Pydantic dla request/response
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., description="Tekst do analizy", min_length=1, max_length=10000)
    use_cache: bool = Field(True, description="Czy używać cache'a dla wyników")

class BatchAnalysisRequest(BaseModel):
    texts: List[str] = Field(..., description="Lista tekstów do analizy", min_items=1, max_items=50)
    batch_size: int = Field(10, description="Rozmiar wsadu", ge=1, le=20)

class TopicExtractionRequest(BaseModel):
    texts: List[str] = Field(..., description="Lista tekstów do ekstrakcji tematów", min_items=1, max_items=100)
    num_topics: int = Field(5, description="Liczba tematów do ekstrakcji", ge=1, le=20)

class NLPAnalysisResponse(BaseModel):
    text: str
    language: str
    tokens: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    sentiment: Dict[str, float]
    key_phrases: List[str]
    pos_tags: List[Dict[str, str]]
    dependencies: List[Dict[str, Any]]
    readability_score: float
    processing_time: float

class BatchAnalysisResponse(BaseModel):
    results: List[NLPAnalysisResponse]
    total_texts: int
    total_processing_time: float

class TopicExtractionResponse(BaseModel):
    topics: List[str]
    num_texts_processed: int
    processing_time: float

class NLPStatsResponse(BaseModel):
    total_analyses: int
    cache_hits: int
    cache_size: int
    avg_processing_time: float
    language_distribution: Dict[str, int]
    models_loaded: List[str]

# Funkcje pomocnicze
def verify_auth_token(token: str):
    """Weryfikuje token autoryzacyjny"""
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token autoryzacyjny")

# Endpointy
@router.post("/analyze", response_model=NLPAnalysisResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    authorization: str = None
) -> NLPAnalysisResponse:
    """
    Przeprowadza kompleksową analizę NLP pojedynczego tekstu

    - **text**: Tekst do analizy (1-10000 znaków)
    - **use_cache**: Czy używać cache'a (domyślnie True)
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    try:
        processor = get_nlp_processor()
        result = await processor.analyze_text(request.text, request.use_cache)

        log_info(f"[NLP_ENDPOINT] Przeanalizowano tekst: {len(request.text)} znaków, język: {result.language}")
        return result

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd analizy tekstu: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd analizy tekstu: {str(e)}")

@router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_texts(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    authorization: str = None
) -> BatchAnalysisResponse:
    """
    Przeprowadza analizę NLP dla wielu tekstów wsadowo

    - **texts**: Lista tekstów (1-50 tekstów)
    - **batch_size**: Rozmiar wsadu (1-20)
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    start_time = time.time()

    try:
        processor = get_nlp_processor()
        results = await processor.batch_analyze(request.texts, request.batch_size)

        total_time = time.time() - start_time

        log_info(f"[NLP_ENDPOINT] Przeanalizowano wsadowo {len(request.texts)} tekstów w {total_time:.2f}s")
        return BatchAnalysisResponse(
            results=results,
            total_texts=len(request.texts),
            total_processing_time=total_time
        )

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd analizy wsadowej: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd analizy wsadowej: {str(e)}")

@router.post("/extract-topics", response_model=TopicExtractionResponse)
async def extract_topics(
    request: TopicExtractionRequest,
    authorization: str = None
) -> TopicExtractionResponse:
    """
    Ekstrahuje tematy z kolekcji tekstów

    - **texts**: Lista tekstów (1-100 tekstów)
    - **num_topics**: Liczba tematów do ekstrakcji (1-20)
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    start_time = time.time()

    try:
        processor = get_nlp_processor()
        topics = await processor.extract_topics(request.texts, request.num_topics)

        processing_time = time.time() - start_time

        log_info(f"[NLP_ENDPOINT] Wyekstrahowano {len(topics)} tematów z {len(request.texts)} tekstów")
        return TopicExtractionResponse(
            topics=topics,
            num_texts_processed=len(request.texts),
            processing_time=processing_time
        )

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd ekstrakcji tematów: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd ekstrakcji tematów: {str(e)}")

@router.get("/stats", response_model=NLPStatsResponse)
async def get_nlp_stats(authorization: str = None) -> NLPStatsResponse:
    """
    Zwraca statystyki procesora NLP

    - Statystyki użycia, wydajności i modeli językowych
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    try:
        processor = get_nlp_processor()
        stats = processor.get_stats()

        return NLPStatsResponse(**stats)

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd pobierania statystyk: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd pobierania statystyk: {str(e)}")

@router.post("/entities")
async def extract_entities(
    request: TextAnalysisRequest,
    authorization: str = None
) -> Dict[str, Any]:
    """
    Ekstrahuje encje nazwane z tekstu

    - **text**: Tekst do analizy
    - **use_cache**: Czy używać cache'a
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    try:
        processor = get_nlp_processor()
        result = await processor.analyze_text(request.text, request.use_cache)

        return {
            "text": request.text,
            "language": result.language,
            "entities": result.entities,
            "entity_count": len(result.entities),
            "processing_time": result.processing_time
        }

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd ekstrakcji encji: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd ekstrakcji encji: {str(e)}")

@router.post("/sentiment")
async def analyze_sentiment(
    request: TextAnalysisRequest,
    authorization: str = None
) -> Dict[str, Any]:
    """
    Analizuje sentyment tekstu

    - **text**: Tekst do analizy
    - **use_cache**: Czy używać cache'a
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    try:
        processor = get_nlp_processor()
        result = await processor.analyze_text(request.text, request.use_cache)

        return {
            "text": request.text,
            "language": result.language,
            "sentiment": result.sentiment,
            "processing_time": result.processing_time
        }

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd analizy sentymentu: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd analizy sentymentu: {str(e)}")

@router.post("/key-phrases")
async def extract_key_phrases(
    request: TextAnalysisRequest,
    authorization: str = None
) -> Dict[str, Any]:
    """
    Ekstrahuje frazy kluczowe z tekstu

    - **text**: Tekst do analizy
    - **use_cache**: Czy używać cache'a
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    try:
        processor = get_nlp_processor()
        result = await processor.analyze_text(request.text, request.use_cache)

        return {
            "text": request.text,
            "language": result.language,
            "key_phrases": result.key_phrases,
            "phrase_count": len(result.key_phrases),
            "processing_time": result.processing_time
        }

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd ekstrakcji fraz kluczowych: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd ekstrakcji fraz kluczowych: {str(e)}")

@router.post("/readability")
async def calculate_readability(
    request: TextAnalysisRequest,
    authorization: str = None
) -> Dict[str, Any]:
    """
    Oblicza ocenę czytelności tekstu

    - **text**: Tekst do analizy
    - **use_cache**: Czy używać cache'a
    """
    if authorization:
        token = authorization.replace("Bearer ", "")
        verify_auth_token(token)

    try:
        processor = get_nlp_processor()
        result = await processor.analyze_text(request.text, request.use_cache)

        return {
            "text": request.text,
            "language": result.language,
            "readability_score": result.readability_score,
            "processing_time": result.processing_time
        }

    except Exception as e:
        log_error(f"[NLP_ENDPOINT] Błąd obliczania czytelności: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd obliczania czytelności: {str(e)}")

# Log inicjalizacji
log_info("[NLP_ENDPOINT] Zarejestrowano endpointy NLP: /api/nlp/*")