
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .response_adapter import adapt
from .memory_store import add_memory, search_memory, memory_export, memory_import, memory_optimize
import os, time, json

router = APIRouter(prefix="/api/memory", tags=["memory"])

def _tenant(req: Request) -> str:
    t = (req.headers.get("X-Tenant-ID") or "default").strip() or "default"
    safe = "".join(ch for ch in t if ch.isalnum() or ch in "-_").lower()
    return safe or "default"

class AddIn(BaseModel):
    text: str
    meta: Optional[Dict[str, Any]] = None
    conf: Optional[float] = 0.6
    lang: Optional[str] = None
    source: Optional[str] = None

class SearchIn(BaseModel):
    q: str
    topk: Optional[int] = 8

class ImportIn(BaseModel):
    items: List[Dict[str, Any]]

@router.post("/add")
async def add(req: Request, body: AddIn):
    ten = _tenant(req)
    rid = add_memory(ten, body.text, meta=body.meta or {}, conf=float(body.conf or 0.6), lang=body.lang, source=body.source)
    return adapt({"text": "OK", "sources": [], "item": rid})

@router.post("/search")
async def search(req: Request, body: SearchIn):
    ten = _tenant(req)
    items = search_memory(ten, body.q, topk=int(body.topk or 8))
    return adapt({"text": f"Znaleziono {len(items)} wpisów.", "sources": [], "items": items})

@router.get("/export")
async def export(req: Request):
    ten = _tenant(req)
    data = memory_export(ten)
    return adapt({"text": f"Eksport: {data['count']} wpisów.", "sources": [], "items": data["items"]})

@router.post("/import")
async def import_(req: Request, body: ImportIn):
    ten = _tenant(req)
    n = memory_import(ten, body.items or [])
    return adapt({"text": f"Zaimportowano {n} wpisów.", "sources": []})

@router.get("/status")
async def status():
    """Status systemu pamięci"""
    try:
        from .memory_store import _connect
        from .redis_middleware import get_redis
        
        # Sprawdź bazę danych SQLite
        con = _connect()
        cur = con.cursor()
        
        conv_count = cur.execute(
            "SELECT COUNT(*) FROM conversations"
        ).fetchone()[0]
        
        users = cur.execute(
            "SELECT COUNT(DISTINCT user_id) FROM conversations"
        ).fetchone()[0]
        
        # Ostatnia wiadomość
        last_msg = cur.execute(
            "SELECT created_at FROM conversations ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        last_activity = last_msg[0] if last_msg else 0
        
        con.close()
        
        # Sprawdź Redis cache
        redis = get_redis()
        redis_ok = hasattr(redis, 'get_stats')
        redis_stats = redis.get_stats() if redis_ok else {}
        
        return {
            "ok": True,
            "status": "operational",
            "database": "sqlite",
            "cache": "redis" if redis_ok else "mock",
            "stats": {
                "conversations": conv_count,
                "users": users,
                "last_activity": last_activity,
                "redis_memory": redis_stats.get("used_memory", "N/A"),
                "cache_hit_rate": redis_stats.get("hit_rate", 0.0)
            }
        }
    except Exception as e:
        import traceback
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


@router.post("/optimize")
async def optimize(req: Request):
    memory_optimize()
    return adapt({"text": "Pamięć zoptymalizowana.", "sources": []})
