#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MORDZIX AI - Unified Application
Wersja 5.0.0 - Zunifikowana architektura z pełną automatyzacją
"""

import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

from core.metrics import (
    PROMETHEUS_AVAILABLE,
    record_error,
    record_request,
)

try:
    import uvicorn  # type: ignore[import]
except ImportError:  # pragma: no cover - fallback dla środowisk bez uvicorn
    uvicorn = None

# ═══════════════════════════════════════════════════════════════════
# KONFIGURACJA ŚRODOWISKA
# ═══════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.absolute()
os.environ.setdefault("AUTH_TOKEN", "ssjjMijaja6969")
os.environ.setdefault("WORKSPACE", str(BASE_DIR))
os.environ.setdefault("MEM_DB", str(BASE_DIR / "mem.db"))

# Lista endpointów wymagających ręcznej akceptacji (spójna z frontendem)
MANUAL_TOOL_ENDPOINTS: List[Dict[str, str]] = [
    {
        "name": "code_write",
        "endpoint": "POST /api/code/write",
        "reason": "Zapisuje pliki w repozytorium i wymaga świadomego potwierdzenia."
    },
    {
        "name": "code_deps_install",
        "endpoint": "POST /api/code/deps/install",
        "reason": "Instaluje zależności i modyfikuje środowisko uruchomieniowe."
    },
    {
        "name": "code_docker_build",
        "endpoint": "POST /api/code/docker/build",
        "reason": "Buduje obraz Dockera – operacja zasobożerna."
    },
    {
        "name": "code_docker_run",
        "endpoint": "POST /api/code/docker/run",
        "reason": "Uruchamia kontener Dockera, wymaga nadzoru operatora."
    },
    {
        "name": "code_git",
        "endpoint": "POST /api/code/git",
        "reason": "Wysyła polecenia git zmieniające historię repozytorium."
    },
    {
        "name": "code_init",
        "endpoint": "POST /api/code/init",
        "reason": "Tworzy nową strukturę projektu na dysku i może nadpisać pliki."
    },
]

_AUTOMATION_SUMMARY_CACHE: Dict[str, Any] = {}
_AUTOMATION_SUMMARY_TS: float = 0.0

# Czy logować podczas importu (przy np. narzędziach CLI ustawiamy flagę by wyciszyć)
_SUPPRESS_IMPORT_LOGS = os.environ.get("MORDZIX_SUPPRESS_STARTUP_LOGS") == "1"

# ═══════════════════════════════════════════════════════════════════
# AUTOMATION SUMMARY HELPERS
# ═══════════════════════════════════════════════════════════════════


def _load_fast_path_handlers() -> Dict[str, Any]:
    """Zwróć listę nazw handlerów fast path (bezpośrednie regexy)."""

    try:
        from core.intent_dispatcher import FAST_PATH_HANDLERS  # type: ignore[import]

        handlers = [handler.__name__ for handler in FAST_PATH_HANDLERS]
        return {
            "available": True,
            "handlers": handlers,
            "count": len(handlers)
        }
    except Exception as exc:  # pragma: no cover - środowiska bez modułu
        if not _SUPPRESS_IMPORT_LOGS:
            print(f"[WARN] Fast path handlers unavailable: {exc}")
        return {
            "available": True,
            "handlers": [],
            "count": 0,
            "error": str(exc)
        }


def _load_tool_registry() -> Dict[str, Any]:
    """Zwróć listę narzędzi routera LLM."""

    try:
        from core.tools_registry import get_all_tools  # type: ignore[import]

        tools = get_all_tools()
        tool_names = [tool.get("name", "") for tool in tools if tool.get("name")]
        categories_counter = Counter(
            name.split("_", 1)[0] if "_" in name else name for name in tool_names
        )
        categories = [
            {"name": key, "count": categories_counter[key]}
            for key in sorted(categories_counter, key=lambda item: (-categories_counter[item], item))
        ]

        return {
            "available": True,
            "count": len(tools),
            "tools": tools,
            "names": tool_names,
            "categories": categories
        }
    except Exception as exc:  # pragma: no cover
        if not _SUPPRESS_IMPORT_LOGS:
            print(f"[WARN] Tool registry unavailable: {exc}")
        return {
            "available": True,
            "count": 0,
            "tools": [],
            "names": [],
            "categories": [],
            "error": str(exc)
        }


def _build_automation_summary() -> Dict[str, Any]:
    """Zbuduj podsumowanie automatyzacji (fast path + router)."""

    fast_path = _load_fast_path_handlers()
    tools = _load_tool_registry()

    fast_count = fast_path.get("count", 0)
    tool_count = tools.get("count", 0)
    manual_count = len(MANUAL_TOOL_ENDPOINTS)

    totals_automations = fast_count + tool_count
    totals_automatic = max(totals_automations - manual_count, 0)

    return {
        "generated_at": time.time(),
        "fast_path": fast_path,
        "tools": {
            "available": tools.get("available", True),
            "count": tool_count,
            "categories": tools.get("categories", []),
            "sample": tools.get("names", [])[:15],
        },
        "manual": {
            "count": manual_count,
            "endpoints": MANUAL_TOOL_ENDPOINTS
        },
        "totals": {
            "automations": totals_automations,
            "automatic": totals_automatic
        }
    }


def get_automation_summary(refresh: bool = False) -> Dict[str, Any]:
    """Pobierz (opcjonalnie odśwież) cache z podsumowaniem automatyzacji."""

    global _AUTOMATION_SUMMARY_CACHE, _AUTOMATION_SUMMARY_TS

    if refresh or not _AUTOMATION_SUMMARY_CACHE:
        _AUTOMATION_SUMMARY_CACHE = _build_automation_summary()
        _AUTOMATION_SUMMARY_TS = _AUTOMATION_SUMMARY_CACHE.get("generated_at", time.time())
    else:
        # Dołącz timestamp do cache (może być potrzebny przy monitoringu)
        _AUTOMATION_SUMMARY_CACHE["generated_at"] = _AUTOMATION_SUMMARY_TS

    return _AUTOMATION_SUMMARY_CACHE

# Prometheus middleware korzysta z core.metrics (jeśli dostępne)

# ═══════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════
app = FastAPI(
    title="Mordzix AI",
    version="5.0.0",
    description="Zaawansowany system AI z pamięcią, uczeniem i pełną automatyzacją",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus middleware
if PROMETHEUS_AVAILABLE:
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        start_time = time.time()
        endpoint = request.url.path
        method = request.method
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code

            return response
        except Exception as exc:
            status_code = getattr(exc, "status_code", 500)
            error_label = exc.__class__.__name__
            record_error(error_label, endpoint)
            raise
        finally:
            duration = time.time() - start_time
            record_request(method, endpoint, status_code, duration)

# ═══════════════════════════════════════════════════════════════════
# INCLUDE ROUTERS - Wszystkie endpointy
# ═══════════════════════════════════════════════════════════════════

if not _SUPPRESS_IMPORT_LOGS:
    print("\n" + "="*70)
    print("MORDZIX AI - INICJALIZACJA ENDPOINTÓW")
    print("="*70 + "\n")

# 1. ASSISTANT (główny chat z AI)
try:
    import assistant_endpoint
    app.include_router(assistant_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Assistant endpoint      /api/chat/assistant")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Assistant endpoint: {e}")

# 2. PSYCHE (stan psychiczny AI)
try:
    import psyche_endpoint
    app.include_router(psyche_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Psyche endpoint         /api/psyche/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Psyche endpoint: {e}")

# 3. PROGRAMISTA (wykonywanie kodu)
try:
    import programista_endpoint
    app.include_router(programista_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Programista endpoint    /api/code/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Programista endpoint: {e}")

# 4. FILES (upload, analiza plików)
try:
    import files_endpoint
    app.include_router(files_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Files endpoint          /api/files/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Files endpoint: {e}")

# 5. TRAVEL (wyszukiwanie podróży)
try:
    import travel_endpoint
    app.include_router(travel_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Travel endpoint         /api/travel/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Travel endpoint: {e}")

# 6. ADMIN (statystyki, cache)
try:
    import admin_endpoint
    app.include_router(admin_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Admin endpoint          /api/admin/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Admin endpoint: {e}")

# 7. CAPTCHA (rozwiązywanie captcha)
try:
    import captcha_endpoint
    app.include_router(captcha_endpoint.router, prefix="/api/captcha", tags=["captcha"])
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Captcha endpoint        /api/captcha/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Captcha endpoint: {e}")

# 8. PROMETHEUS (metryki)
try:
    import prometheus_endpoint
    app.include_router(prometheus_endpoint.router, prefix="/api/prometheus", tags=["monitoring"])
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Prometheus endpoint     /api/prometheus/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Prometheus endpoint: {e}")

# 9. TTS (text-to-speech)
try:
    import tts_endpoint
    app.include_router(tts_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ TTS endpoint            /api/tts/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ TTS endpoint: {e}")

# 10. STT (speech-to-text)
try:
    import stt_endpoint
    app.include_router(stt_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ STT endpoint            /api/stt/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ STT endpoint: {e}")

# 11. WRITING (generowanie tekstów)
try:
    import writing_endpoint
    app.include_router(writing_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Writing endpoint        /api/writing/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Writing endpoint: {e}")

# 12. SUGGESTIONS (proaktywne sugestie)
try:
    import suggestions_endpoint
    app.include_router(suggestions_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Suggestions endpoint    /api/suggestions/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Suggestions endpoint: {e}")

# 13. BATCH (przetwarzanie wsadowe)
try:
    import batch_endpoint
    app.include_router(batch_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Batch endpoint          /api/batch/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Batch endpoint: {e}")

# 14. RESEARCH (web search - DuckDuckGo, Wikipedia, SERPAPI)
try:
    import research_endpoint
    app.include_router(research_endpoint.router)
    if not _SUPPRESS_IMPORT_LOGS:
        print("✓ Research endpoint       /api/research/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"✗ Research endpoint: {e}")

if not _SUPPRESS_IMPORT_LOGS:
    print("\n" + "="*70 + "\n")

# ═══════════════════════════════════════════════════════════════════
# BASIC ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.get("/api")
@app.get("/status")
async def api_status():
    """Status API"""
    return {
        "ok": True,
        "app": "Mordzix AI",
        "version": "5.0.0",
        "features": {
            "auto_stm_to_ltm": True,
            "auto_learning": True,
            "context_injection": True,
            "psyche_system": True,
            "travel_search": True,
            "code_executor": True,
            "tts_stt": True,
            "file_analysis": True
        },
        "endpoints": {
            "chat": "/api/chat/assistant",
            "chat_stream": "/api/chat/assistant/stream",
            "psyche": "/api/psyche/status",
            "travel": "/api/travel/search",
            "code": "/api/code/exec",
            "files": "/api/files/upload",
            "admin": "/api/admin/stats",
            "tts": "/api/tts/speak",
            "stt": "/api/stt/transcribe"
        },
        "automation": get_automation_summary()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/api/endpoints/list")
async def list_endpoints():
    """Lista wszystkich endpointów API"""
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
                    "name": route.name,
                    "tags": list(route.tags) if route.tags else [],
                    "summary": route.summary or ""
                })
                seen.add(identifier)
    
    endpoints.sort(key=lambda e: (e["path"], ",".join(e["methods"])))
    return {"ok": True, "count": len(endpoints), "endpoints": endpoints}


@app.get("/api/automation/status")
async def automation_status():
    """Podsumowanie automatycznych narzędzi i fast path."""

    summary = get_automation_summary()
    return {"ok": True, **summary}

# ═══════════════════════════════════════════════════════════════════
# FRONTEND ROUTES - ANGULAR APP
# ═══════════════════════════════════════════════════════════════════

FRONTEND_DIST = BASE_DIR / "frontend" / "dist" / "mordzix-ai"

# Serwowanie statycznych plików z Angular dist/ (tylko jeśli istnieją)
assets_dir = FRONTEND_DIST / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@app.get("/", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
async def serve_frontend():
    """Główny interfejs czatu - Angular SPA"""
    # Próbujemy załadować Angular dist
    angular_index = FRONTEND_DIST / "index.html"
    if angular_index.exists():
        return HTMLResponse(content=angular_index.read_text(encoding="utf-8"))
    
    # Fallback: stary index.html (dla dev bez builda)
    fallback_index = BASE_DIR / "index.html"
    if fallback_index.exists():
        return HTMLResponse(content=fallback_index.read_text(encoding="utf-8"))
    
    # Brak frontendu
    return HTMLResponse(
        content="""
        <h1>🚧 Frontend Not Built</h1>
        <p>Run: <code>cd frontend && npm install && npm run build:prod</code></p>
        <p>Or use API directly: <a href="/docs">/docs</a></p>
        """,
        status_code=404
    )

# Catch-all dla Angular routing (musi być na końcu!)
@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
async def angular_catch_all(full_path: str):
    """Przekieruj wszystkie nieznane ścieżki do Angular SPA (dla routingu)"""
    # Ignoruj ścieżki API
    if full_path.startswith("api/") or full_path.startswith("health"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Zwróć Angular index.html (SPA obsłuży routing)
    angular_index = FRONTEND_DIST / "index.html"
    if angular_index.exists():
        return HTMLResponse(content=angular_index.read_text(encoding="utf-8"))
    
    raise HTTPException(status_code=404, detail="Frontend not found")

# PWA Assets
@app.get("/sw.js", include_in_schema=False)
@app.get("/ngsw-worker.js", include_in_schema=False)
async def serve_service_worker(request: Request):
    """Service worker (Angular PWA lub legacy)."""
    candidates = [
        FRONTEND_DIST / "ngsw-worker.js",
        FRONTEND_DIST / "sw.js",
        BASE_DIR / "dist" / "ngsw-worker.js",
        BASE_DIR / "dist" / "sw.js",
        BASE_DIR / "ngsw-worker.js",
        BASE_DIR / "sw.js",
    ]
    for path in candidates:
        if path.exists():
            return FileResponse(path, media_type="application/javascript")
    return HTMLResponse(status_code=404, content="service worker not found")

@app.get("/manifest.webmanifest", include_in_schema=False)
async def serve_manifest():
    """Web App Manifest"""
    candidates = [
        FRONTEND_DIST / "manifest.webmanifest",
        FRONTEND_DIST / "assets" / "manifest.webmanifest",
        BASE_DIR / "dist" / "manifest.webmanifest",
        BASE_DIR / "manifest.webmanifest",
    ]
    for path in candidates:
        if path.exists():
            return FileResponse(path, media_type="application/manifest+json")
    return HTMLResponse(status_code=404, content="manifest not found")

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    """Favicon"""
    paths = [
        FRONTEND_DIST / "favicon.ico",
        BASE_DIR / "dist" / "favicon.ico",
        BASE_DIR / "favicon.ico",
        BASE_DIR / "icons" / "favicon.ico"
    ]
    for path in paths:
        if path.exists():
            return FileResponse(path, media_type="image/x-icon")
    return HTMLResponse(status_code=404)

# Static files (assets, icons)
if (BASE_DIR / "icons").exists():
    app.mount("/icons", StaticFiles(directory=str(BASE_DIR / "icons")), name="icons")

# ═══════════════════════════════════════════════════════════════════
# STARTUP & SHUTDOWN
# ═══════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Inicjalizacja przy starcie"""
    print("\n" + "="*70)
    print("MORDZIX AI - STARTED")
    print("="*70)
    print("\n[INFO] Funkcje:")
    print("  ✓ Auto STM→LTM transfer")
    print("  ✓ Auto-learning (Google + scraping)")
    print("  ✓ Context injection (LTM w prompt)")
    print("  ✓ Psyche system (nastrój AI)")
    print("  ✓ Travel (hotele/restauracje/atrakcje)")
    print("  ✓ Code executor (shell/git/docker)")
    print("  ✓ TTS/STT (ElevenLabs + Whisper)")
    print("\n[INFO] Endpoints:")
    print("  [API] Chat:      POST /api/chat/assistant")
    print("  [API] Stream:    POST /api/chat/assistant/stream")
    print("  [API] Psyche:    GET  /api/psyche/status")
    print("  [API] Travel:    GET  /api/travel/search")
    print("  [API] Code:      POST /api/code/exec")
    print("  [API] Files:     POST /api/files/upload")
    print("  [API] TTS:       POST /api/tts/speak")
    print("  [API] STT:       POST /api/stt/transcribe")
    print("\n[INFO] Interfejs:")
    print("  [WEB] Frontend:  http://localhost:8080/")
    print("  [WEB] Docs:      http://localhost:8080/docs")
    print("\n" + "="*70 + "\n")

    summary = get_automation_summary(refresh=True)
    fast_count = summary.get("fast_path", {}).get("count", 0)
    tool_count = summary.get("tools", {}).get("count", 0)
    manual_count = summary.get("manual", {}).get("count", 0)
    automatic_total = summary.get("totals", {}).get("automatic", 0)

    print("[INFO] Automatyzacja:")
    print(f"  ✓ Fast path handlers : {fast_count}")
    print(f"  ✓ Router tools       : {tool_count}")
    print(f"  ✓ Manual approvals   : {manual_count}")
    print(f"  ✓ Auto executables   : {automatic_total}")
    
    # Inicjalizacja bazy danych i pamięci
    try:
        from core.memory import _init_db, load_ltm_to_memory
        _init_db()
        load_ltm_to_memory()
        print("[OK] Pamięć LTM załadowana")
    except Exception as e:
        print(f"[WARN] Błąd inicjalizacji pamięci: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup przy wyłączeniu"""
    print("\n[INFO] Shutting down Mordzix AI...")

# ═══════════════════════════════════════════════════════════════════
# MAIN - Uruchomienie serwera
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    if uvicorn is None:
        raise RuntimeError("Uvicorn nie jest zainstalowany. Uruchom 'pip install uvicorn' w środowisku aplikacji.")
    
    parser = argparse.ArgumentParser(description='Mordzix AI Server')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port (default: 8080)')
    parser.add_argument('-H', '--host', default="0.0.0.0", help='Host (default: 0.0.0.0)')
    parser.add_argument('--reload', action='store_true', help='Auto-reload on code changes')
    args = parser.parse_args()
    
    print(f"\n[INFO] Starting server on http://{args.host}:{args.port}")
    print(f"[INFO] API Docs: http://localhost:{args.port}/docs")
    print(f"[INFO] Frontend: http://localhost:{args.port}/\n")
    
    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
