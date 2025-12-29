#!/usr/bin/env python3
"""Internal endpoints for UI helpers.

Provides a gated `/api/internal/ui_token` that returns the AUTH_TOKEN only when
the server explicitly allows it via env `UI_EXPOSE_TOKEN=1` or the request
comes from localhost. This lets the frontend fetch a token without hardcoding it.
"""
from fastapi import APIRouter, Request, HTTPException
import os

router = APIRouter(prefix="/api/internal")


@router.get("/ui_token")
async def ui_token(req: Request):
    """Return the AUTH_TOKEN only if UI_EXPOSE_TOKEN=1 or request is local."""
    expose_flag = os.getenv("UI_EXPOSE_TOKEN", "0") == "1"
    token = os.getenv("AUTH_TOKEN", "ssjjMijaja6969")

    # Determine client IP (may be None in some test contexts)
    client_host = None
    try:
        client_host = req.client.host
    except Exception:
        client_host = None

    is_local = client_host in ("127.0.0.1", "::1", "localhost")

    if expose_flag or is_local:
        return {"ok": True, "token": token}

    raise HTTPException(status_code=403, detail="UI token not exposed")
