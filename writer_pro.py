"""
Writer Pro - Zaawansowane narzędzia do pisania i tworzenia treści
================================================================

Moduł zawiera endpointy API dla zaawansowanych funkcji pisarskich:
- Generowanie kreatywnych tekstów
- Tworzenie opisów produktów (Vinted, aukcje)
- Pisanie postów społecznościowych
- Artykuły mistrzowskie
- Opisy sprzedażowe
- Dokumentacja techniczna

Router: writer_router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import time

from core.config import AUTH_TOKEN
from core.auth import auth_dependency as _auth_dep

# Import funkcji z core.writing
from core.writing import (
    write_creative_boost,
    write_vinted,
    write_social,
    write_auction,
    write_auction_pro,
    write_masterpiece_article,
    write_sales_masterpiece,
    write_technical_masterpiece,
    analyze_fashion_text,
    auction_kb_learn,
    auction_kb_fetch,
    suggest_tags_for_auction,
)

# Modele Pydantic dla request/response
class CreativeWritingRequest(BaseModel):
    topic: str
    tone: str = "inspirujący"
    style: str = "kreatywny"
    length: str = "średni"
    web_context: str = ""

class ProductDescriptionRequest(BaseModel):
    title: str
    description: str
    price: Optional[float] = None
    platform: str = "vinted"  # vinted, auction, general
    web_context: str = ""

class SocialMediaRequest(BaseModel):
    platform: str
    topic: str
    tone: str = "dynamiczny"
    hashtags: int = 6
    variants: int = 3
    web_context: str = ""

class AuctionProRequest(BaseModel):
    title: str
    description: str
    price: Optional[float] = None
    web_context: str = ""
    tone: str = "sprzedażowy"
    length: str = "średni"
    creative: bool = False

class MasterpieceArticleRequest(BaseModel):
    topic: str
    style: str = "zaangażowany"
    length: str = "długi"
    target_audience: str = "ogólny"
    seo_optimized: bool = True

class SalesMasterpieceRequest(BaseModel):
    product_name: str
    product_description: str
    target_price: Optional[float] = None
    audience: str = "ogólny"
    urgency: str = "normalna"

class TechnicalMasterpieceRequest(BaseModel):
    topic: str
    difficulty: str = "średni"
    include_examples: bool = True
    include_code: bool = True

class AuctionLearningRequest(BaseModel):
    items: List[Dict[str, Any]]

# Inicjalizacja routera
writer_router = APIRouter(
    prefix="/api/writer",
    tags=["writing"],
    responses={404: {"description": "Not found"}},
)

@writer_router.get("/status")
async def get_writer_status(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Status modułu Writer Pro

    Returns:
        Informacje o dostępności funkcji pisarskich
    """
    return {
        "ok": True,
        "module": "writer_pro",
        "version": "1.0.0",
        "features": [
            "creative_writing",
            "product_descriptions",
            "social_media_posts",
            "auction_descriptions",
            "masterpiece_articles",
            "sales_copy",
            "technical_documentation",
            "fashion_analysis",
            "auction_knowledge_base",
        ],
        "timestamp": time.time(),
    }

@writer_router.post("/creative")
async def create_creative_text(request: CreativeWritingRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Generuj kreatywny tekst na zadany temat

    Args:
        request: Parametry tekstu kreatywnego

    Returns:
        Wygenerowany tekst kreatywny
    """
    try:
        result = write_creative_boost(
            topic=request.topic,
            tone=request.tone,
            styl=request.style,
            dlugosc=request.length,
            web_ctx=request.web_context
        )

        return {
            "ok": True,
            "result": result,
            "params": {
                "topic": request.topic,
                "tone": request.tone,
                "style": request.style,
                "length": request.length,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating creative text: {str(e)}")

@writer_router.post("/product")
async def create_product_description(request: ProductDescriptionRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Generuj opis produktu dla różnych platform

    Args:
        request: Parametry opisu produktu

    Returns:
        Opis produktu
    """
    try:
        if request.platform.lower() == "vinted":
            result = write_vinted(
                title=request.title,
                desc=request.description,
                price=request.price,
                web_ctx=request.web_context
            )
        elif request.platform.lower() in ["auction", "aukcja"]:
            result = write_auction(
                title=request.title,
                desc=request.description,
                price=request.price,
                web_ctx=request.web_context
            )
        else:
            # Ogólny opis produktu
            result = write_vinted(
                title=request.title,
                desc=request.description,
                price=request.price,
                web_ctx=request.web_context
            )

        return {
            "ok": True,
            "result": result,
            "platform": request.platform,
            "params": {
                "title": request.title,
                "price": request.price,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating product description: {str(e)}")

@writer_router.post("/social")
async def create_social_media_post(request: SocialMediaRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Generuj posty na media społecznościowe

    Args:
        request: Parametry posta społecznościowego

    Returns:
        Lista wariantów postów
    """
    try:
        result = write_social(
            platform=request.platform,
            topic=request.topic,
            tone=request.tone,
            hashtags=request.hashtags,
            variants=request.variants,
            web_ctx=request.web_context
        )

        return {
            "ok": True,
            "result": result,
            "platform": request.platform,
            "params": {
                "topic": request.topic,
                "tone": request.tone,
                "hashtags": request.hashtags,
                "variants": request.variants,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating social media post: {str(e)}")

@writer_router.post("/auction/pro")
async def create_auction_pro_description(request: AuctionProRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Zaawansowane generowanie opisu aukcji

    Args:
        request: Parametry zaawansowanego opisu aukcji

    Returns:
        Profesjonalny opis aukcji
    """
    try:
        result = write_auction_pro(
            title=request.title,
            desc=request.description,
            price=request.price,
            web_ctx=request.web_context,
            tone=request.tone,
            length=request.length,
            kreatywny=request.creative
        )

        return {
            "ok": True,
            "result": result,
            "params": {
                "title": request.title,
                "tone": request.tone,
                "length": request.length,
                "creative": request.creative,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating auction description: {str(e)}")

@writer_router.post("/article/masterpiece")
async def create_masterpiece_article(request: MasterpieceArticleRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Generuj mistrzowski artykuł

    Args:
        request: Parametry artykułu

    Returns:
        Kompletny artykuł
    """
    try:
        result = write_masterpiece_article(
            topic=request.topic,
            style=request.style,
            length=request.length,
            target_audience=request.target_audience,
            seo_optimized=request.seo_optimized
        )

        return {
            "ok": True,
            "result": result,
            "params": {
                "topic": request.topic,
                "style": request.style,
                "length": request.length,
                "audience": request.target_audience,
                "seo": request.seo_optimized,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating masterpiece article: {str(e)}")

@writer_router.post("/sales/masterpiece")
async def create_sales_masterpiece(request: SalesMasterpieceRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Generuj mistrzowski tekst sprzedażowy

    Args:
        request: Parametry tekstu sprzedażowego

    Returns:
        Profesjonalny tekst sprzedażowy
    """
    try:
        result = write_sales_masterpiece(
            product_name=request.product_name,
            product_desc=request.product_description,
            target_price=request.target_price,
            audience=request.audience,
            urgency=request.urgency
        )

        return {
            "ok": True,
            "result": result,
            "params": {
                "product": request.product_name,
                "audience": request.audience,
                "urgency": request.urgency,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sales copy: {str(e)}")

@writer_router.post("/technical/masterpiece")
async def create_technical_masterpiece(request: TechnicalMasterpieceRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Generuj mistrzowską dokumentację techniczną

    Args:
        request: Parametry dokumentacji technicznej

    Returns:
        Kompletna dokumentacja techniczna
    """
    try:
        result = write_technical_masterpiece(
            topic=request.topic,
            difficulty=request.difficulty,
            include_examples=request.include_examples,
            include_code=request.include_code
        )

        return {
            "ok": True,
            "result": result,
            "params": {
                "topic": request.topic,
                "difficulty": request.difficulty,
                "examples": request.include_examples,
                "code": request.include_code,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating technical documentation: {str(e)}")

@writer_router.post("/fashion/analyze")
async def analyze_fashion_content(
    text: str = Query(..., description="Tekst do analizy"),
    _=Depends(_auth_dep)
) -> Dict[str, Any]:
    """
    Analizuj tekst pod kątem mody i stylu

    Args:
        text: Tekst do analizy

    Returns:
        Analiza modowa tekstu
    """
    try:
        result = analyze_fashion_text(text)

        return {
            "ok": True,
            "analysis": result,
            "text_length": len(text),
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing fashion text: {str(e)}")

@writer_router.get("/auction/tags")
async def get_auction_tags(
    title: str = Query(..., description="Tytuł aukcji"),
    description: str = Query("", description="Opis aukcji"),
    _=Depends(_auth_dep)
) -> Dict[str, Any]:
    """
    Sugeruj tagi dla aukcji

    Args:
        title: Tytuł aukcji
        description: Opis aukcji

    Returns:
        Sugerowane tagi
    """
    try:
        tags = suggest_tags_for_auction(title, description)

        return {
            "ok": True,
            "tags": tags,
            "count": len(tags),
            "params": {
                "title": title,
                "description_length": len(description),
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting auction tags: {str(e)}")

@writer_router.get("/auction/knowledge")
async def get_auction_knowledge(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Pobierz wiedzę aukcyjną z bazy

    Returns:
        Wiedza aukcyjna pogrupowana tematycznie
    """
    try:
        knowledge = auction_kb_fetch()

        return {
            "ok": True,
            "knowledge": knowledge,
            "categories": list(knowledge.keys()),
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching auction knowledge: {str(e)}")

@writer_router.post("/auction/learn")
async def learn_auction_knowledge(request: AuctionLearningRequest, _=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Naucz system wiedzy aukcyjnej

    Args:
        request: Elementy wiedzy aukcyjnej do nauczenia

    Returns:
        Status nauki
    """
    try:
        learned_count = auction_kb_learn(request.items)

        return {
            "ok": True,
            "learned_items": learned_count,
            "total_items": len(request.items),
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error learning auction knowledge: {str(e)}")

@writer_router.get("/templates")
async def get_writing_templates(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Pobierz dostępne szablony pisarskie

    Returns:
        Lista dostępnych szablonów i ich parametrów
    """
    templates = {
        "creative": {
            "description": "Kreatywne pisanie na zadany temat",
            "params": ["topic", "tone", "style", "length", "web_context"],
            "tones": ["inspirujący", "refleksyjny", "dynamiczny", "poetycki"],
            "styles": ["kreatywny", "analityczny", "narracyjny", "perswazyjny"],
            "lengths": ["krótki", "średni", "długi"],
        },
        "product": {
            "description": "Opisy produktów dla różnych platform",
            "platforms": ["vinted", "auction", "general"],
            "params": ["title", "description", "price", "platform", "web_context"],
        },
        "social": {
            "description": "Posty na media społecznościowe",
            "platforms": ["facebook", "instagram", "twitter", "linkedin", "tiktok"],
            "params": ["platform", "topic", "tone", "hashtags", "variants", "web_context"],
        },
        "auction_pro": {
            "description": "Zaawansowane opisy aukcji",
            "params": ["title", "description", "price", "web_context", "tone", "length", "creative"],
            "tones": ["sprzedażowy", "informacyjny", "kreatywny", "profesjonalny"],
        },
        "article": {
            "description": "Mistrzowskie artykuły",
            "params": ["topic", "style", "length", "target_audience", "seo_optimized"],
            "styles": ["zaangażowany", "edukacyjny", "rozrywkowy", "analityczny"],
            "audiences": ["ogólny", "specjalistyczny", "młodzieżowy", "biznesowy"],
        },
        "sales": {
            "description": "Mistrzowskie teksty sprzedażowe",
            "params": ["product_name", "product_description", "target_price", "audience", "urgency"],
            "urgencies": ["normalna", "wysoka", "krytyczna"],
        },
        "technical": {
            "description": "Dokumentacja techniczna",
            "params": ["topic", "difficulty", "include_examples", "include_code"],
            "difficulties": ["początkujący", "średni", "zaawansowany"],
        },
    }

    return {
        "ok": True,
        "templates": templates,
        "count": len(templates),
        "timestamp": time.time(),
    }