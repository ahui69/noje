"""
Sports News Pro - Moduł do wyszukiwania newsów i wyników sportowych
=================================================================

Moduł zawiera funkcje do:
- Wyszukiwania aktualności sportowych
- Pobierania wyników meczów z ESPN
- Normalizacji danych sportowych

Główne funkcje:
- news_search(): Wyszukiwanie newsów sportowych
- normalize_scores(): Pobieranie i normalizacja wyników meczów
"""

import asyncio
import httpx
from typing import Dict, Any, List
from core.config import SERPAPI_KEY, HTTP_TIMEOUT

async def news_search(query: str = "top", limit: int = 6) -> Dict[str, Any]:
    """
    Wyszukiwanie aktualności sportowych

    Args:
        query: Zapytanie do wyszukania (np. "piłka nożna", "NBA")
        limit: Maksymalna liczba wyników

    Returns:
        Dict z wynikami wyszukiwania
    """
    try:
        if not SERPAPI_KEY:
            return {"ok": False, "error": "SERPAPI_KEY missing"}

        api = "https://serpapi.com/search.json"
        params = {
            "engine": "google_news",
            "q": query,
            "num": str(limit),
            "api_key": SERPAPI_KEY
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(api, params=params)
            if r.status_code >= 400:
                return {"ok": False, "error": f"API error: {r.status_code}"}

            js = r.json()
            items = []
            for it in js.get("news_results", [])[:limit]:
                items.append({
                    "title": it.get("title", ""),
                    "link": it.get("link", ""),
                    "date": it.get("date", ""),
                    "source": it.get("source", {}).get("name", "")
                })

            return {"ok": True, "items": items}

    except Exception as e:
        return {"ok": False, "error": str(e)}

def normalize_scores(kind: str = "nba", limit: int = 8) -> List[Dict[str, Any]]:
    """
    Pobieranie i normalizacja wyników meczów z ESPN

    Args:
        kind: Rodzaj sportu (nba, nfl, mlb, nhl, soccer)
        limit: Maksymalna liczba wyników

    Returns:
        Lista znormalizowanych wyników meczów
    """
    try:
        ESPN_URLS = {
            "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
            "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
            "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
            "soccer": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
        }

        base = ESPN_URLS.get(kind.lower())
        if not base:
            return []

        # Synchroniczne wywołanie dla kompatybilności
        import requests
        r = requests.get(base, timeout=HTTP_TIMEOUT)
        j = r.json()

        events = j.get("events", [])
        out = []

        for e in events[:limit]:
            comp = (e.get("competitions") or [{}])[0]
            status = (comp.get("status") or {}).get("type", {})
            short = status.get("shortDetail") or status.get("name") or ""
            teams = (comp.get("competitors") or [])

            if len(teams) == 2:
                t1 = teams[0]
                t2 = teams[1]
                out.append({
                    "home": t1.get("team", {}).get("displayName"),
                    "home_score": t1.get("score"),
                    "away": t2.get("team", {}).get("displayName"),
                    "away_score": t2.get("score"),
                    "status": short,
                    "venue": (comp.get("venue") or {}).get("fullName"),
                    "start": e.get("date"),
                    "kind": kind.upper()
                })

        return out

    except Exception as e:
        print(f"Error in normalize_scores: {e}")
        return []

# Funkcje pomocnicze dla kompatybilności
def get_sports_scores(kind: str = "nba", limit: int = 8) -> List[Dict[str, Any]]:
    """Alias dla normalize_scores dla kompatybilności wstecznej"""
    return normalize_scores(kind, limit)

def get_current_news(limit: int = 6) -> List[Dict[str, Any]]:
    """Pobieranie aktualnych newsów sportowych"""
    try:
        # Synchroniczne wywołanie dla kompatybilności
        result = asyncio.run(news_search("sports news", limit))
        if result.get("ok"):
            return result.get("items", [])
        return []
    except Exception:
        return []