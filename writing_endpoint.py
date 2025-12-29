#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
writing_endpoint.py - Endpointy do funkcji pisania kreatywnego i komercyjnego.
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

import os
from core.writing import (
    write_creative_boost,
    write_vinted,
    write_social,
    write_auction,
    write_auction_pro,
    analyze_fashion_text,
    suggest_tags_for_auction,
    auction_kb_learn,
    auction_kb_fetch,
    write_masterpiece_article,
    write_sales_masterpiece,
    write_technical_masterpiece
)

router = APIRouter(prefix="/api/writing")

# Auth - zgodnie z innymi endpointami
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "ssjjMijaja6969")
def _auth(req: Request):
    if (req.headers.get("Authorization","") or "").replace("Bearer ","").strip() != AUTH_TOKEN:
        raise HTTPException(401, "unauthorized")


# --- MODELE DANYCH ---

class CreativeRequest(BaseModel):
    topic: str
    tone: Optional[str] = "naturalny"
    style: Optional[str] = "klarowny"
    length: Optional[str] = "średni"
    web_ctx: Optional[str] = ""

class CreativeResponse(BaseModel):
    ok: bool
    text: str
    metadata: Dict[str, Any] = {}

class VintedRequest(BaseModel):
    title: str
    description: str
    price: Optional[float] = None
    web_ctx: Optional[str] = ""

class SocialRequest(BaseModel):
    platform: str
    topic: str
    tone: Optional[str] = "dynamiczny"
    hashtags: Optional[int] = 6
    variants: Optional[int] = 3
    web_ctx: Optional[str] = ""

class AuctionRequest(BaseModel):
    title: str
    description: str
    price: Optional[float] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    web_ctx: Optional[str] = ""

class AuctionProRequest(BaseModel):
    title: str
    description: str
    price: Optional[float] = None
    web_ctx: Optional[str] = ""
    tone: Optional[str] = "sprzedażowy"
    length: Optional[str] = "średni"
    creative: Optional[bool] = False

class FashionAnalysisRequest(BaseModel):
    text: str

class AuctionKBLearnRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(...)

class MasterpieceArticleRequest(BaseModel):
    topic: str
    style: Optional[str] = "zaangażowany"
    length: Optional[str] = "długi"
    target_audience: Optional[str] = "ogólny"
    seo_optimized: Optional[bool] = True

class SalesMasterpieceRequest(BaseModel):
    product_name: str
    product_desc: str
    target_price: Optional[float] = None
    audience: Optional[str] = "ogólny"
    urgency: Optional[str] = "normalna"

class TechnicalMasterpieceRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "średni"
    include_examples: Optional[bool] = True
    include_code: Optional[bool] = True

# --- ENDPOINTY PISANIA ---

@router.post("/creative", response_model=CreativeResponse)
async def creative_writing(body: CreativeRequest, req: Request, _=Depends(_auth)):
    """Kreatywne pisanie artykułów, esejów i tekstów."""
    try:
        text = write_creative_boost(
            topic=body.topic,
            tone=body.tone,
            styl=body.style,
            dlugosc=body.length,
            web_ctx=body.web_ctx
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "topic": body.topic,
                "tone": body.tone,
                "style": body.style,
                "length": body.length,
                "has_web_context": bool(body.web_ctx)
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania tekstu kreatywnego: {str(e)}",
            metadata={"error": str(e)}
        )

@router.post("/vinted", response_model=CreativeResponse)
async def vinted_description(body: VintedRequest, req: Request, _=Depends(_auth)):
    """Generator opisów dla Vinted."""
    try:
        text = write_vinted(
            title=body.title,
            desc=body.description,
            price=body.price,
            web_ctx=body.web_ctx
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "title": body.title,
                "has_price": body.price is not None
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania opisu Vinted: {str(e)}",
            metadata={"error": str(e)}
        )

@router.post("/social", response_model=CreativeResponse)
async def social_media_post(body: SocialRequest, req: Request, _=Depends(_auth)):
    """Generator postów do mediów społecznościowych."""
    try:
        text = write_social(
            platform=body.platform,
            topic=body.topic,
            tone=body.tone,
            hashtags=body.hashtags,
            variants=body.variants,
            web_ctx=body.web_ctx
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "platform": body.platform,
                "topic": body.topic,
                "hashtags": body.hashtags,
                "variants": body.variants
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania postu społecznościowego: {str(e)}",
            metadata={"error": str(e)}
        )

@router.post("/auction", response_model=CreativeResponse)
async def auction_description(body: AuctionRequest, req: Request, _=Depends(_auth)):
    """Generator opisów aukcyjnych."""
    try:
        text = write_auction(
            title=body.title,
            desc=body.description,
            price=body.price,
            tags=body.tags,
            web_ctx=body.web_ctx
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "title": body.title,
                "has_price": body.price is not None,
                "tags_count": len(body.tags)
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania opisu aukcji: {str(e)}",
            metadata={"error": str(e)}
        )

@router.post("/auction/pro", response_model=CreativeResponse)
async def auction_pro_description(body: AuctionProRequest, req: Request, _=Depends(_auth)):
    """Generator profesjonalnych opisów aukcyjnych z wersją A/B."""
    try:
        text = write_auction_pro(
            title=body.title,
            desc=body.description,
            price=body.price,
            web_ctx=body.web_ctx,
            tone=body.tone,
            length=body.length,
            kreatywny=body.creative
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "title": body.title,
                "has_price": body.price is not None,
                "tone": body.tone,
                "length": body.length,
                "creative": body.creative
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania profesjonalnego opisu aukcji: {str(e)}",
            metadata={"error": str(e)}
        )

@router.post("/fashion/analyze")
async def fashion_analysis(body: FashionAnalysisRequest, req: Request, _=Depends(_auth)):
    """Analiza tekstu pod kątem elementów mody."""
    try:
        result = analyze_fashion_text(body.text)
        return {
            "ok": True,
            "analysis": result,
            "metadata": {
                "text_length": len(body.text),
                "brands_found": len(result.get("brands", [])),
                "categories_found": len(result.get("categories", [])),
                "colors_found": len(result.get("colors", []))
            }
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


# --- INTERNAL HELPERS UŻYWANE PRZEZ FAST PATH ---

def _derive_platform(source_text: str) -> str:
    text = (source_text or "").lower()
    for platform in ["instagram", "facebook", "linkedin", "twitter", "x", "tiktok"]:
        if platform in text:
            return "twitter" if platform == "x" else platform
    return "instagram"


def _derive_title(prompt: str) -> str:
    cleaned = (prompt or "").strip()
    if not cleaned:
        return "Nowy wpis"
    if len(cleaned) <= 80:
        return cleaned.capitalize()
    return cleaned[:77].rstrip() + "…"


async def generate_content(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Uniwersalny generator treści wykorzystywany przez fast path w dispatcherze."""
    if not isinstance(payload, dict):
        raise ValueError("Payload musi być dict")

    content_type = str(payload.get("type", "general") or "general").lower()
    prompt = (payload.get("prompt") or payload.get("topic") or "").strip()
    source_text = payload.get("source_text") or prompt

    try:
        if content_type == "vinted":
            title = payload.get("title") or _derive_title(prompt)
            description = payload.get("description") or prompt
            text = write_vinted(
                title=title,
                desc=description,
                price=payload.get("price"),
                web_ctx=payload.get("web_ctx", "")
            )
            metadata = {"mode": "vinted", "title": title}

        elif content_type == "social":
            platform = payload.get("platform") or _derive_platform(source_text)
            text = write_social(
                platform=platform,
                topic=prompt or source_text,
                tone=payload.get("tone", "dynamiczny"),
                hashtags=payload.get("hashtags", 6),
                variants=payload.get("variants", 3),
                web_ctx=payload.get("web_ctx", "")
            )
            metadata = {"mode": "social", "platform": platform}

        elif content_type == "auction":
            title = payload.get("title") or _derive_title(prompt)
            description = payload.get("description") or prompt
            tags = payload.get("tags") or []
            text = write_auction(
                title=title,
                desc=description,
                price=payload.get("price"),
                tags=tags,
                web_ctx=payload.get("web_ctx", "")
            )
            metadata = {"mode": "auction", "title": title, "tags": tags}

        else:
            text = write_creative_boost(
                topic=prompt or source_text,
                tone=payload.get("tone", "naturalny"),
                styl=payload.get("style", "klarowny"),
                dlugosc=payload.get("length", "średni"),
                web_ctx=payload.get("web_ctx", "")
            )
            metadata = {"mode": "general", "topic": prompt or source_text[:120]}

        return {
            "ok": True,
            "type": content_type,
            "content": text,
            "metadata": metadata
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc)
        }

@router.post("/auction/suggest-tags")
async def suggest_auction_tags(body: AuctionRequest, req: Request, _=Depends(_auth)):
    """Sugeruj tagi dla aukcji."""
    try:
        tags = suggest_tags_for_auction(body.title, body.description)
        return {
            "ok": True,
            "tags": tags,
            "count": len(tags)
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

@router.post("/auction/kb/learn")
async def learn_auction_kb(body: AuctionKBLearnRequest, req: Request, _=Depends(_auth)):
    """Naucz bazę wiedzy aukcyjnej nowych elementów."""
    try:
        count = auction_kb_learn(body.items)
        return {
            "ok": True,
            "added": count,
            "total_items": len(body.items)
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

@router.get("/auction/kb/fetch")
async def fetch_auction_kb(req: Request, _=Depends(_auth)):
    """Pobierz bazę wiedzy aukcyjnej."""
    try:
        kb = auction_kb_fetch()
        # Konwertuj zbiory na listy, aby można je było serializować do JSON
        serializable_kb = {k: list(v) for k, v in kb.items()}
        return {
            "ok": True,
            "kb": serializable_kb,
            "categories": len(serializable_kb),
            "entries_total": sum(len(v) for v in serializable_kb.values())
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

# --- ENDPOINTY DLA FUNKCJI MISTRZOWSKICH ---

@router.post("/masterpiece/article", response_model=CreativeResponse)
async def masterpiece_article(body: MasterpieceArticleRequest, req: Request, _=Depends(_auth)):
    """Generator mistrzowskich artykułów."""
    try:
        text = write_masterpiece_article(
            topic=body.topic,
            style=body.style,
            length=body.length,
            target_audience=body.target_audience,
            seo_optimized=body.seo_optimized
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "topic": body.topic,
                "style": body.style,
                "length": body.length,
                "target_audience": body.target_audience,
                "seo_optimized": body.seo_optimized
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania mistrzowskiego artykułu: {str(e)}",
            metadata={"error": str(e)}
        )

@router.post("/masterpiece/sales", response_model=CreativeResponse)
async def sales_masterpiece(body: SalesMasterpieceRequest, req: Request, _=Depends(_auth)):
    """Generator mistrzowskich tekstów sprzedażowych."""
    try:
        text = write_sales_masterpiece(
            product_name=body.product_name,
            product_desc=body.product_desc,
            target_price=body.target_price,
            audience=body.audience,
            urgency=body.urgency
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "product_name": body.product_name,
                "has_price": body.target_price is not None,
                "audience": body.audience,
                "urgency": body.urgency
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania mistrzowskiego tekstu sprzedażowego: {str(e)}",
            metadata={"error": str(e)}
        )

@router.post("/masterpiece/technical", response_model=CreativeResponse)
async def technical_masterpiece(body: TechnicalMasterpieceRequest, req: Request, _=Depends(_auth)):
    """Generator mistrzowskich wyjaśnień technicznych."""
    try:
        text = write_technical_masterpiece(
            topic=body.topic,
            difficulty=body.difficulty,
            include_examples=body.include_examples,
            include_code=body.include_code
        )
        return CreativeResponse(
            ok=True,
            text=text,
            metadata={
                "topic": body.topic,
                "difficulty": body.difficulty,
                "include_examples": body.include_examples,
                "include_code": body.include_code
            }
        )
    except Exception as e:
        return CreativeResponse(
            ok=False,
            text=f"Błąd podczas generowania mistrzowskiego wyjaśnienia technicznego: {str(e)}",
            metadata={"error": str(e)}
        )