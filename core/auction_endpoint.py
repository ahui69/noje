#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auction Endpoint - AI Auction Manager API
Analiza aukcji, wycena, optymalizacja opisów
"""

import os
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from .auth import check_auth
from .helpers import log_info, log_error
from .ai_auction import AIAuctionManager

router = APIRouter(prefix="/api/auction", tags=["AI Auction"])

# Initialize manager
auction_manager = AIAuctionManager()

# Auth
def _auth(req: Request):
    if not check_auth(req):
        raise HTTPException(401, "Unauthorized")


# ============================================================================
# MODELS
# ============================================================================

class AuctionAnalysisRequest(BaseModel):
    title: str
    description: str
    category: str
    price: float
    condition: str = "używany"
    platform: str = "allegro"  # allegro, olx, vinted

class PriceOptimizationRequest(BaseModel):
    item_type: str
    brand: str
    condition: str
    category: str
    current_price: Optional[float] = None
    similar_items: Optional[List[Dict]] = None

class DescriptionOptimizationRequest(BaseModel):
    title: str
    description: str
    category: str
    keywords: Optional[List[str]] = None

class MarketAnalysisRequest(BaseModel):
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    time_range: str = "30d"  # 7d, 30d, 90d


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/analyze")
async def analyze_auction(req: Request, body: AuctionAnalysisRequest):
    """Kompleksowa analiza aukcji - cena, opis, kategoria"""
    _auth(req)
    
    try:
        # Analiza tytułu
        title_score = 0
        title_issues = []
        title_suggestions = []
        
        if len(body.title) < 20:
            title_issues.append("Tytuł zbyt krótki")
            title_suggestions.append("Dodaj więcej szczegółów: rozmiar, kolor, model")
        elif len(body.title) > 100:
            title_issues.append("Tytuł zbyt długi")
            title_suggestions.append("Skróć do 60-80 znaków dla lepszej czytelności")
        else:
            title_score += 30
        
        # Sprawdź słowa kluczowe
        important_words = ["nowy", "oryginalny", "limitowany", "premium", "vintage"]
        if any(word in body.title.lower() for word in important_words):
            title_score += 20
        else:
            title_suggestions.append("Dodaj przyciągające słowa: OKAZJA, NOWY, ORYGINAŁ")
        
        # Analiza opisu
        desc_score = 0
        desc_issues = []
        desc_suggestions = []
        
        if len(body.description) < 100:
            desc_issues.append("Opis zbyt krótki")
            desc_suggestions.append("Dodaj szczegóły: wymiary, materiał, historia przedmiotu")
        elif len(body.description) > 50:
            desc_score += 25
        
        # Sprawdź strukturę opisu
        if "\n" in body.description:
            desc_score += 10  # Ma formatowanie
        else:
            desc_suggestions.append("Podziel opis na akapity dla czytelności")
        
        # Sprawdź czy zawiera wymiary
        dimension_words = ["cm", "mm", "rozmiar", "wymiar", "wysokość", "szerokość"]
        if any(word in body.description.lower() for word in dimension_words):
            desc_score += 15
        else:
            desc_suggestions.append("Dodaj dokładne wymiary produktu")
        
        # Analiza ceny
        price_analysis = {
            "current_price": body.price,
            "recommendation": "adekwatna",
            "confidence": 0.7
        }
        
        # Szacowanie na podstawie kategorii
        category_avg_prices = {
            "elektronika": 500,
            "moda": 150,
            "dom": 200,
            "sport": 180,
            "motoryzacja": 1000,
            "kolekcje": 300
        }
        
        avg_price = category_avg_prices.get(body.category.lower(), 200)
        if body.price < avg_price * 0.5:
            price_analysis["recommendation"] = "niska - rozważ podniesienie"
        elif body.price > avg_price * 2:
            price_analysis["recommendation"] = "wysoka - może odstraszyć kupujących"
        
        # Całkowity wynik
        total_score = min(100, title_score + desc_score + 30)  # +30 za podstawy
        
        grade = "A" if total_score >= 80 else "B" if total_score >= 60 else "C" if total_score >= 40 else "D"
        
        result = {
            "success": True,
            "overall_score": total_score,
            "grade": grade,
            "title_analysis": {
                "score": title_score,
                "issues": title_issues,
                "suggestions": title_suggestions
            },
            "description_analysis": {
                "score": desc_score,
                "issues": desc_issues,
                "suggestions": desc_suggestions
            },
            "price_analysis": price_analysis,
            "top_recommendations": [
                s for s in (title_suggestions + desc_suggestions)[:3]
            ] if title_suggestions or desc_suggestions else ["Aukcja wygląda dobrze!"],
            "platform_tips": {
                "allegro": "Dodaj darmową dostawę dla zwiększenia konwersji",
                "olx": "Odpowiadaj szybko na wiadomości - to buduje zaufanie",
                "vinted": "Oznacz jako 'negocjowalne' dla więcej zainteresowanych"
            }.get(body.platform, "Bądź aktywny i odpowiadaj na pytania")
        }
        
        log_info(f"[AUCTION] Analyzed: {body.title[:50]}... Score: {total_score}")
        return result
        
    except Exception as e:
        log_error(f"[AUCTION] analyze error: {e}")
        raise HTTPException(500, str(e))


@router.post("/optimize-price")
async def optimize_price(req: Request, body: PriceOptimizationRequest):
    """Optymalizacja ceny na podstawie rynku"""
    _auth(req)
    
    try:
        # Bazowe ceny według kategorii i marki
        base_prices = {
            "elektronika": {"apple": 3000, "samsung": 2000, "xiaomi": 800, "default": 500},
            "moda": {"gucci": 2000, "nike": 400, "zara": 100, "default": 150},
            "sport": {"specialized": 5000, "trek": 4000, "default": 500},
        }
        
        category_prices = base_prices.get(body.category.lower(), {"default": 200})
        base = category_prices.get(body.brand.lower(), category_prices["default"])
        
        # Mnożnik stanu
        condition_multipliers = {
            "nowy": 1.0,
            "jak nowy": 0.9,
            "bardzo dobry": 0.75,
            "dobry": 0.6,
            "używany": 0.5,
            "do naprawy": 0.2
        }
        
        multiplier = condition_multipliers.get(body.condition.lower(), 0.6)
        
        optimal_price = int(base * multiplier)
        min_price = int(optimal_price * 0.8)
        max_price = int(optimal_price * 1.2)
        
        # Strategia cenowa
        if body.current_price:
            if body.current_price < min_price:
                strategy = "Za niska cena! Możesz stracić pieniądze."
            elif body.current_price > max_price:
                strategy = "Cena może być za wysoka - rozważ obniżkę lub negocjacje."
            else:
                strategy = "Cena w optymalnym zakresie."
        else:
            strategy = "Zacznij od środka zakresu, bądź otwarty na negocjacje."
        
        log_info(f"[AUCTION] Price optimization: {body.brand} {body.item_type} -> {optimal_price} PLN")
        
        return {
            "success": True,
            "optimal_price": optimal_price,
            "price_range": {
                "min": min_price,
                "max": max_price
            },
            "current_price": body.current_price,
            "strategy": strategy,
            "tips": [
                "Ustaw cenę 'do negocjacji' aby przyciągnąć więcej osób",
                "Pierwsza cena powinna być 10-15% wyższa niż minimalna akceptowalna",
                "Obserwuj konkurencję i dostosowuj cenę"
            ]
        }
        
    except Exception as e:
        log_error(f"[AUCTION] optimize-price error: {e}")
        raise HTTPException(500, str(e))


@router.post("/optimize-description")
async def optimize_description(req: Request, body: DescriptionOptimizationRequest):
    """Optymalizacja opisu aukcji pod SEO i konwersję"""
    _auth(req)
    
    try:
        # Analiza obecnego opisu
        original_words = len(body.description.split())
        has_formatting = "\n" in body.description
        has_emoji = any(ord(c) > 127 for c in body.description)
        
        # Sugestie poprawy
        improvements = []
        
        if original_words < 50:
            improvements.append({
                "type": "content",
                "suggestion": "Rozbuduj opis - dodaj więcej szczegółów o produkcie",
                "priority": "high"
            })
        
        if not has_formatting:
            improvements.append({
                "type": "formatting",
                "suggestion": "Podziel tekst na sekcje: Stan, Szczegóły, Wymiary, Wysyłka",
                "priority": "medium"
            })
        
        if not has_emoji:
            improvements.append({
                "type": "visual",
                "suggestion": "Dodaj emoji dla lepszej czytelności: ✅ ⭐ 📦 🚚",
                "priority": "low"
            })
        
        # Sugerowane słowa kluczowe
        suggested_keywords = body.keywords or []
        category_keywords = {
            "elektronika": ["sprawny", "komplet", "gwarancja", "oryginalne", "pudełko"],
            "moda": ["oryginalny", "metka", "limitowany", "vintage", "premium"],
            "dom": ["stan idealny", "jak nowy", "design", "jakość", "solidny"],
        }
        
        for cat, kws in category_keywords.items():
            if cat in body.category.lower():
                suggested_keywords.extend(kws)
        
        # Generuj ulepszony tytuł
        optimized_title = body.title.upper() if len(body.title) < 50 else body.title
        if not any(word in body.title.lower() for word in ["okazja", "polecam", "super"]):
            optimized_title = f"🔥 {body.title} 🔥"
        
        log_info(f"[AUCTION] Description optimization: {len(improvements)} suggestions")
        
        return {
            "success": True,
            "original_stats": {
                "word_count": original_words,
                "has_formatting": has_formatting,
                "has_emoji": has_emoji
            },
            "optimized_title": optimized_title,
            "improvements": improvements,
            "suggested_keywords": list(set(suggested_keywords))[:10],
            "template": f"""
✨ {body.title.upper()} ✨

📋 OPIS:
{body.description}

📦 STAN: [uzupełnij]
📏 WYMIARY: [uzupełnij]
🚚 WYSYŁKA: Paczkomat / Kurier

✅ Sprawdź moje inne aukcje!
            """.strip()
        }
        
    except Exception as e:
        log_error(f"[AUCTION] optimize-description error: {e}")
        raise HTTPException(500, str(e))


@router.post("/market-analysis")
async def market_analysis(req: Request, body: MarketAnalysisRequest):
    """Analiza rynku dla danej kategorii"""
    _auth(req)
    
    try:
        # Symulowane dane rynkowe
        market_data = {
            "elektronika": {
                "avg_price": 650,
                "listings_count": 15420,
                "trend": "stabilny",
                "best_selling_brands": ["Apple", "Samsung", "Xiaomi", "Sony"],
                "peak_hours": ["18:00-21:00", "weekendy"],
                "competition": "wysoka"
            },
            "moda": {
                "avg_price": 120,
                "listings_count": 89450,
                "trend": "wzrostowy",
                "best_selling_brands": ["Nike", "Adidas", "Zara", "H&M"],
                "peak_hours": ["19:00-22:00", "niedziele"],
                "competition": "bardzo wysoka"
            },
            "sport": {
                "avg_price": 340,
                "listings_count": 12300,
                "trend": "sezonowy",
                "best_selling_brands": ["Decathlon", "Nike", "Adidas"],
                "peak_hours": ["17:00-20:00"],
                "competition": "średnia"
            }
        }
        
        data = market_data.get(body.category.lower(), {
            "avg_price": 200,
            "listings_count": 5000,
            "trend": "stabilny",
            "best_selling_brands": [],
            "peak_hours": ["18:00-21:00"],
            "competition": "średnia"
        })
        
        # Rekomendacje
        recommendations = [
            f"Najlepsze godziny publikacji: {', '.join(data['peak_hours'])}",
            f"Konkurencja: {data['competition']} - {'wyróżnij się zdjęciami' if data['competition'] == 'bardzo wysoka' else 'skup się na jakości opisu'}",
        ]
        
        if body.brand and body.brand.lower() in [b.lower() for b in data.get("best_selling_brands", [])]:
            recommendations.append(f"✅ {body.brand} to popularna marka w tej kategorii!")
        
        log_info(f"[AUCTION] Market analysis for {body.category}")
        
        return {
            "success": True,
            "category": body.category,
            "time_range": body.time_range,
            "market_data": data,
            "recommendations": recommendations,
            "best_time_to_post": "Niedziela 19:00-21:00" if body.category.lower() == "moda" else "Sobota 10:00-12:00"
        }
        
    except Exception as e:
        log_error(f"[AUCTION] market-analysis error: {e}")
        raise HTTPException(500, str(e))


@router.get("/categories")
async def get_categories(req: Request):
    """Lista dostępnych kategorii aukcyjnych"""
    _auth(req)
    
    return {
        "success": True,
        "categories": [
            {"id": "elektronika", "name": "Elektronika", "subcategories": ["telefony", "komputery", "tv", "audio"]},
            {"id": "moda", "name": "Moda", "subcategories": ["damska", "męska", "dziecięca", "buty", "torebki"]},
            {"id": "dom", "name": "Dom i Ogród", "subcategories": ["meble", "dekoracje", "narzędzia", "ogród"]},
            {"id": "sport", "name": "Sport", "subcategories": ["fitness", "rowery", "outdoor", "sporty zimowe"]},
            {"id": "motoryzacja", "name": "Motoryzacja", "subcategories": ["części", "akcesoria", "opony"]},
            {"id": "kolekcje", "name": "Kolekcje", "subcategories": ["karty", "monety", "znaczki", "vintage"]},
        ]
    }
