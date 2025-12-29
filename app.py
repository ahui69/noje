#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import time
import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Request
from openai_compat import router as openai_compat_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

APP_TITLE = "Mordzix AI"
APP_VERSION = "5.0.0"

ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"
LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> float:
    return time.time()


def _load_env_file(path: Path) -> None:
    # nie nadpisuje istniejących zmiennych w środowisku
    if not path.exists():
        return
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k or k in os.environ:
            continue
        if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
            v = v[1:-1]
        os.environ[k] = v


_load_env_file(ENV_PATH)
print(f"[CONFIG] Loaded .env from {ENV_PATH}")

app = FastAPI(
    title=APP_TITLE, version=APP_VERSION, docs_url="/docs", redoc_url="/redoc"
)

app.include_router(openai_compat_router)

app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=False,  # Wyłączone, jeśli nie używamy cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.get("/health")
async def health() -> Dict[str, Any]:
    # pokazuje co realnie jest w env (bez kluczy)
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "ts": _now(),
        "env": {
            "LLM_BASE_URL": (os.getenv("LLM_BASE_URL") or "").strip(),
            "LLM_MODEL": (os.getenv("LLM_MODEL") or "").strip(),
            "LLM_API_KEY_set": bool((os.getenv("LLM_API_KEY") or "").strip()),
            "AUTH_TOKEN_set": bool((os.getenv("AUTH_TOKEN") or "").strip()),
        },
    }


ROUTER_ATTR_OVERRIDES: Dict[str, Tuple[str, ...]] = {
    "writer_pro": ("writer_router", "router"),
}


def _try_import_router(modname: str) -> Tuple[Optional[Any], Optional[str]]:
    attr_order = ROUTER_ATTR_OVERRIDES.get(modname, ("router",))
    try:
        m = importlib.import_module(modname)
        for attr in attr_order:
            r = getattr(m, attr, None)
            if r is not None:
                return r, None
        return None, f"no router attr (checked: {', '.join(attr_order)})"
    except Exception as e:
        err_text = str(e).replace("\n", " | ")
        return None, f"{type(e).__name__}: {err_text[:220]}"


def _include(router_obj: Any) -> Optional[str]:
    try:
        app.include_router(router_obj)
        return None
    except Exception as e:
        return f"{type(e).__name__}: {str(e)[:220]}"


print("\n" + "=" * 70)
print("📡 LOADING ENDPOINTS")
print("=" * 70)

# root routers
root_modules = [
    ("assistant_simple", "Chat (Commercial)"),
    ("assistant_endpoint", "Chat (Legacy Cognitive)",),
    ("stt_endpoint", "STT (Speech-to-Text)"),
    ("tts_endpoint", "TTS (Text-to-Speech)"),
    ("suggestions_endpoint", "Suggestions"),
    ("internal_endpoint", "Internal"),
    ("files_endpoint", "Files (Advanced)"),
    ("research_endpoint", "Research (Legacy)"),
    ("prometheus_endpoint", "Metrics (Legacy)"),
    ("programista_endpoint", "Code Assistant"),
    ("nlp_endpoint", "NLP"),
    ("travel_endpoint", "Travel"),
    ("writing_endpoint", "Writing"),
    ("psyche_endpoint", "Psyche"),
    ("writer_pro", "Writer Pro"),
    ("routers", "Admin/Debug"),
]

loaded: List[Dict[str, Any]] = []
failed: List[Dict[str, Any]] = []

for mod, name in root_modules:
    r, err = _try_import_router(mod)
    if r is None:
        failed.append({"module": mod, "name": name, "error": err})
        print(f"⏭️  {name:30s} - {err}")
        continue
    inc_err = _include(r)
    if inc_err:
        failed.append({"module": mod, "name": name, "error": inc_err})
        print(f"⚠️  {name:30s} - include failed: {inc_err}")
        continue
    loaded.append({"module": mod, "name": name})
    print(f"✅ {name:30s}")

# core routers (opcjonalnie) – ładowane bezpiecznie; jeśli core jest popsuty, serwer i chat dalej żyje
core_modules = [
    ("core.assistant_endpoint", "Chat (Advanced) [core]"),
    ("core.memory_endpoint", "Memory [core]"),
    ("core.cognitive_endpoint", "Cognitive [core]"),
    ("core.negocjator_endpoint", "Negotiator [core]"),
    ("core.reflection_endpoint", "Reflection [core]"),
    ("core.legal_office_endpoint", "Legal Office [core]"),
    ("core.hybrid_search_endpoint", "Hybrid Search [core]"),
    ("core.batch_endpoint", "Batch Processing [core]"),
    ("core.prometheus_endpoint", "Metrics [core]"),
    ("core.suggestions_endpoint", "Suggestions [core]"),
    ("core.research_endpoint", "Research [core]"),
    ("core.admin_endpoint", "Admin [core]"),
    ("core.hacker_endpoint", "Hacker Assistant [core]"),
    ("core.psyche_endpoint", "Psyche [core]"),
    ("core.chat_advanced_endpoint", "Chat Advanced Compat [core]"),
    ("core.auction_endpoint", "Auction [core]"),
]

for mod, name in core_modules:
    r, err = _try_import_router(mod)
    if r is None:
        failed.append({"module": mod, "name": name, "error": err})
        print(f"⏭️  {name:30s} - {err}")
        continue
    inc_err = _include(r)
    if inc_err:
        failed.append({"module": mod, "name": name, "error": inc_err})
        print(f"⚠️  {name:30s} - include failed: {inc_err}")
        continue
    loaded.append({"module": mod, "name": name})
    print(f"✅ {name:30s}")

print("=" * 70)
print(f"✅ Loaded routers: {len(loaded)}")
print(f"⛔ Failed routers: {len(failed)}")
print("=" * 70 + "\n")


@app.get("/api/routers/status")
async def routers_status() -> Dict[str, Any]:
    return {"loaded": loaded, "failed": failed, "ts": _now()}


@app.get("/api/endpoints/list")
async def endpoints_list() -> Dict[str, Any]:
    out = []
    for rt in app.router.routes:
        path = getattr(rt, "path", None)
        methods = getattr(rt, "methods", None)
        if path and methods:
            out.append({"path": path, "methods": sorted(list(methods))})
    out.sort(key=lambda x: x["path"])
    return {"count": len(out), "items": out, "ts": _now()}


# static frontend (best-effort)
def _mount_frontend() -> None:
    candidates = [
        ROOT_DIR / "frontend" / "dist",
        ROOT_DIR / "frontend" / "dist" / "browser",
        ROOT_DIR / "frontend-premium" / "dist",
        ROOT_DIR / "dist",
    ]
    for c in candidates:
        if c.exists() and c.is_dir() and (c / "index.html").exists():
            app.mount("/", StaticFiles(directory=str(c), html=True), name="frontend")
            print(f"✅ Frontend mounted from: {c}")
            return


_mount_frontend()


@app.exception_handler(Exception)
async def any_exc(_, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)[:800]},
    )


def get_automation_summary(refresh: bool = False, **_kwargs) -> dict:
    """
    Funkcja kompatybilności dla narzędzi/bootstrapa, które wywołują:
        get_automation_summary(refresh=...)
    `refresh` i dodatkowe kwargs są akceptowane, żeby nie wywalać startu.
    """
    import os

    info = {
        "refresh": bool(refresh),
        "loaded_env_file": os.getenv("ENV_FILE") or os.getenv("DOTENV_PATH") or None,
        "has_auth_token": bool(os.getenv("AUTH_TOKEN")),
        "host": os.getenv("HOST", None),
        "port": int(os.getenv("PORT", "8000")),
        "pythonpath": os.getenv("PYTHONPATH", None),
        "venv": os.getenv("VIRTUAL_ENV", None),
    }

    app_obj = globals().get("app")
    try:
        routes = getattr(app_obj, "routes", None)
        info["routes_count"] = len(routes) if routes is not None else None
    except Exception:
        info["routes_count"] = None

    return info


# === AUTO-COMPAT (route aliases + kw compat) ===
def _mrd__auto_alias_double_api_prefix(app):
    """
    Jeśli przez przypadek router ma prefix /api i app.include_router też ma prefix /api,
    FastAPI wystawia endpointy jako /api/api/...
    Ten blok dodaje aliasy /api/... dla istniejących /api/api/..., bez grzebania w routerach.
    """
    try:
        from fastapi.routing import APIRoute
    except Exception:
        return

    routes = [r for r in getattr(app, "routes", []) if isinstance(r, APIRoute)]
    existing = {(r.path, tuple(sorted(r.methods or []))) for r in routes}

    for r in routes:
        p = r.path or ""
        if p.startswith("/api/api/"):
            dst = "/api/" + p[len("/api/api/") :]
            key = (dst, tuple(sorted(r.methods or [])))
            if key in existing:
                continue
            try:
                app.add_api_route(
                    dst,
                    r.endpoint,
                    methods=list(r.methods or []),
                    include_in_schema=True,
                    name=(r.name + "_alias") if r.name else None,
                )
                existing.add(key)
            except Exception:
                continue


def _mrd__compat_get_automation_summary_refresh():
    """
    Start/diagnostyka woła get_automation_summary(refresh=...).
    Jeśli obecna implementacja nie przyjmuje `refresh`, to łapiemy to kompatybilnie.
    """
    try:
        import inspect

        g = globals().get("get_automation_summary")
        if g is None or not callable(g):
            return
        sig = None
        try:
            sig = inspect.signature(g)
        except Exception:
            sig = None

        if sig is not None and "refresh" in sig.parameters:
            return

        orig = g

        def get_automation_summary(*args, refresh=None, **kwargs):  # noqa: F811
            return orig(*args, **kwargs)

        globals()["get_automation_summary"] = get_automation_summary
    except Exception:
        return


try:
    _mrd__auto_alias_double_api_prefix(app)
except Exception:
    pass

_mrd__compat_get_automation_summary_refresh()
