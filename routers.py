"""
Routers Full - Dodatkowe endpointy API dla Mordzix AI
======================================================

Moduł zawiera dodatkowe endpointy API, które rozszerzają funkcjonalność systemu:
- Endpointy administracyjne
- Endpointy diagnostyczne
- Endpointy monitorowania
- Endpointy eksperymentalne

Główne endpointy:
- /api/routers/status - Status wszystkich routerów
- /api/routers/list - Lista dostępnych endpointów
- /api/routers/health - Sprawdzanie zdrowia systemu
- /api/routers/metrics - Metryki systemu
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import time
import os
import json

from core.config import AUTH_TOKEN
from core.auth import auth_dependency as _auth_dep

# Inicjalizacja routera
router = APIRouter(
    prefix="/api/routers",
    tags=["routers"],
    responses={404: {"description": "Not found"}},
)

# Cache dla statusu systemu
_SYSTEM_STATUS_CACHE = {}
_SYSTEM_STATUS_TS = 0.0
_CACHE_TTL = 30  # sekundy

def _get_system_status(refresh: bool = False) -> Dict[str, Any]:
    """Pobiera status systemu z cache lub odświeża"""
    global _SYSTEM_STATUS_CACHE, _SYSTEM_STATUS_TS

    current_time = time.time()
    if not refresh and _SYSTEM_STATUS_CACHE and (current_time - _SYSTEM_STATUS_TS) < _CACHE_TTL:
        return _SYSTEM_STATUS_CACHE

    # Zbieranie statusu systemu
    status = {
        "timestamp": current_time,
        "uptime": current_time,
        "version": "5.0.0",
        "environment": {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.sys.platform,
            "working_directory": os.getcwd(),
        },
        "features": {
            "auto_stm_to_ltm": True,
            "auto_learning": True,
            "context_injection": True,
            "psyche_system": True,
            "travel_search": True,
            "code_executor": True,
            "tts_stt": True,
            "file_analysis": True,
            "semantic_analysis": True,
        }
    }

    # Próba dodania statusu bazy danych
    try:
        from core.memory import _db
        conn = _db()
        c = conn.cursor()

        # Statystyki bazy danych
        db_stats = {
            "connected": True,
            "path": getattr(conn, 'db_path', 'unknown'),
        }

        # Próba pobrania liczby rekordów
        try:
            tables = ["facts", "memory", "memory_long", "psy_episode", "psy_reflection"]
            for table in tables:
                try:
                    count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    db_stats[f"{table}_count"] = count
                except:
                    pass
        except:
            pass

        conn.close()
        status["database"] = db_stats

    except Exception as e:
        status["database"] = {"connected": False, "error": str(e)}

    # Próba dodania statusu psychiki
    try:
        from core.memory import psy_get
        psyche = psy_get()
        status["psyche"] = {
            "mood": round(psyche.get("mood", 0.0), 2),
            "energy": round(psyche.get("energy", 0.6), 2),
            "focus": round(psyche.get("focus", 0.6), 2),
            "style": psyche.get("style", "neutral"),
        }
    except Exception as e:
        status["psyche"] = {"error": str(e)}

    # Próba dodania statusu systemu monitoringu
    try:
        from system_stats import init_monitor
        status["monitoring"] = {"available": True}
    except Exception as e:
        status["monitoring"] = {"available": False, "error": str(e)}

    # Cache'owanie wyniku
    _SYSTEM_STATUS_CACHE = status
    _SYSTEM_STATUS_TS = current_time

    return status

@router.get("/status")
async def get_routers_status(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Pobiera kompleksowy status wszystkich routerów i systemu

    Returns:
        Status systemu ze wszystkimi komponentami
    """
    return _get_system_status(refresh=True)

@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Prosty health check systemu (bez autoryzacji dla monitoringu)

    Returns:
        Podstawowy status zdrowia systemu
    """
    try:
        status = _get_system_status()
        return {
            "status": "healthy",
            "timestamp": status["timestamp"],
            "version": status["version"],
            "database_connected": status.get("database", {}).get("connected", False),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
        }

@router.get("/list")
async def list_all_endpoints(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Lista wszystkich dostępnych endpointów w systemie

    Returns:
        Kompletna lista endpointów ze wszystkich routerów
    """
    from fastapi.routing import APIRoute

    # Import aplikacji FastAPI (zakładamy, że jest dostępna globalnie)
    try:
        from app import app
    except ImportError:
        return {"error": "Cannot access main FastAPI app"}

    endpoints = []
    seen = set()

    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api"):
            methods = sorted([m for m in route.methods if m not in {"HEAD", "OPTIONS"}])
            identifier = (route.path, tuple(methods))

            if identifier not in seen:
                endpoints.append({
                    "path": route.path,
                    "methods": methods,
                    "name": route.name or "",
                    "tags": list(route.tags) if route.tags else [],
                    "summary": route.summary or "",
                    "deprecated": route.deprecated or False,
                })
                seen.add(identifier)

    endpoints.sort(key=lambda e: (e["path"], ",".join(e["methods"])))

    return {
        "ok": True,
        "count": len(endpoints),
        "endpoints": endpoints,
        "timestamp": time.time(),
    }

@router.get("/metrics")
async def get_system_metrics(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Pobiera metryki systemu

    Returns:
        Metryki wydajności i użycia systemu
    """
    metrics = {
        "timestamp": time.time(),
        "uptime_seconds": time.time(),
    }

    # Próba dodania metryk z Prometheus
    try:
        from core.metrics import get_metrics
        prometheus_metrics = get_metrics()
        metrics["prometheus"] = prometheus_metrics
    except Exception as e:
        metrics["prometheus"] = {"error": str(e)}

    # Próba dodania metryk systemu
    try:
        from system_stats import system_stats
        system_metrics = system_stats()
        metrics["system"] = system_metrics
    except Exception as e:
        metrics["system"] = {"error": str(e)}

    # Metryki aplikacji
    try:
        from core.config import get_config_summary
        config = get_config_summary()
        metrics["config"] = {
            "version": config.get("version", "unknown"),
            "features_enabled": len(config.get("features", {})),
            "llm_model": config.get("llm_model", "unknown"),
        }
    except Exception as e:
        metrics["config"] = {"error": str(e)}

    return metrics

@router.get("/config")
async def get_system_config(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Pobiera podsumowanie konfiguracji systemu

    Returns:
        Podsumowanie ustawień konfiguracyjnych
    """
    try:
        from core.config import get_config_summary
        config = get_config_summary()
        return {
            "ok": True,
            "config": config,
            "timestamp": time.time(),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "timestamp": time.time(),
        }

@router.get("/endpoints/summary")
async def get_endpoints_summary(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Podsumowanie endpointów pogrupowane według kategorii

    Returns:
        Podsumowanie endpointów w grupach
    """
    try:
        from app import app
    except ImportError:
        raise HTTPException(status_code=500, detail="Cannot access main FastAPI app")

    from fastapi.routing import APIRoute
    from collections import defaultdict

    endpoints_by_tag = defaultdict(list)
    total_endpoints = 0

    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api"):
            methods = [m for m in route.methods if m not in {"HEAD", "OPTIONS"}]
            if methods:
                total_endpoints += 1
                tags = list(route.tags) if route.tags else ["untagged"]

                for tag in tags:
                    endpoints_by_tag[tag].append({
                        "path": route.path,
                        "methods": sorted(methods),
                        "name": route.name or "",
                    })

    # Statystyki
    summary = {
        "total_endpoints": total_endpoints,
        "categories": {},
        "timestamp": time.time(),
    }

    for tag, endpoints in endpoints_by_tag.items():
        summary["categories"][tag] = {
            "count": len(endpoints),
            "endpoints": sorted(endpoints, key=lambda x: x["path"]),
        }

    return summary

@router.get("/debug/info")
async def get_debug_info(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Informacje debug dla deweloperów

    Returns:
        Szczegółowe informacje o środowisku i konfiguracji
    """
    debug_info = {
        "timestamp": time.time(),
        "environment": dict(os.environ),
        "python": {
            "version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.sys.platform,
            "executable": os.sys.executable,
            "path": os.sys.path[:5],  # Pierwsze 5 ścieżek
        },
        "working_directory": os.getcwd(),
        "files_in_root": os.listdir(".") if os.path.exists(".") else [],
    }

    # Próba dodania informacji o bazie danych
    try:
        from core.memory import _db
        conn = _db()
        c = conn.cursor()

        # Lista tabel
        tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        debug_info["database"] = {
            "tables": [table[0] for table in tables],
            "path": getattr(conn, 'db_path', 'unknown'),
        }

        conn.close()
    except Exception as e:
        debug_info["database"] = {"error": str(e)}

    # Próba dodania informacji o konfiguracji
    try:
        from core.config import get_config_summary
        debug_info["config"] = get_config_summary()
    except Exception as e:
        debug_info["config"] = {"error": str(e)}

    return debug_info

@router.post("/cache/clear")
async def clear_system_cache(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Czyści cache systemu

    Returns:
        Status operacji czyszczenia cache
    """
    try:
        # Czyszczenie cache statusu systemu
        global _SYSTEM_STATUS_CACHE, _SYSTEM_STATUS_TS
        _SYSTEM_STATUS_CACHE = {}
        _SYSTEM_STATUS_TS = 0.0

        # Próba czyszczenia innych cache'y
        try:
            from core.memory import LTM_FACTS_CACHE, LTM_CACHE_LOADED
            LTM_FACTS_CACHE.clear()
            LTM_CACHE_LOADED = False
        except:
            pass

        return {
            "ok": True,
            "message": "System cache cleared successfully",
            "timestamp": time.time(),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "timestamp": time.time(),
        }

@router.get("/version")
async def get_version_info() -> Dict[str, Any]:
    """
    Informacje o wersji systemu (publiczne)

    Returns:
        Informacje o wersji i build
    """
    return {
        "version": "5.0.0",
        "name": "Mordzix AI",
        "description": "Zaawansowany system AI z pamięcią, uczeniem i pełną automatyzacją",
        "build": "unified-architecture",
        "features": [
            "Hierarchical Memory (STM/LTM)",
            "Auto Learning & Research",
            "Context Injection",
            "Psyche System",
            "Multi-modal Processing",
            "Code Execution",
            "TTS/STT Integration",
            "Advanced Semantic Analysis",
        ],
        "timestamp": time.time(),
    }

# Eksperymentalne endpointy (mogą być usunięte w przyszłości)
@router.get("/experimental/features")
async def get_experimental_features(_=Depends(_auth_dep)) -> Dict[str, Any]:
    """
    Lista eksperymentalnych funkcji systemu

    Returns:
        Lista funkcji eksperymentalnych
    """
    return {
        "features": [
            {
                "name": "semantic_analysis",
                "description": "Zaawansowana analiza semantyczna tekstu",
                "status": "active",
                "endpoint": "/api/nlp/analyze",
            },
            {
                "name": "auto_learning",
                "description": "Automatyczne uczenie się z internetu",
                "status": "active",
                "endpoint": "/api/research/autolearn",
            },
            {
                "name": "psyche_system",
                "description": "System psychiczny AI z nastrojami",
                "status": "active",
                "endpoint": "/api/psyche/status",
            },
            {
                "name": "vision_analysis",
                "description": "Analiza obrazów i dokumentów",
                "status": "beta",
                "endpoint": "/api/vision/analyze",
            },
        ],
        "timestamp": time.time(),
    }