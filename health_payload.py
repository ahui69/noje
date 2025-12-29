#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spójny payload healthcheck współdzielony przez wszystkie routery."""
from __future__ import annotations

import os
import time
from typing import Any, Dict

try:
    from core import metrics as core_metrics
except Exception:
    core_metrics = None  # type: ignore


def _ts() -> float:
    return time.time()


def build_health_payload(app_version: str) -> Dict[str, Any]:
    """
    Zwraca zunifikowaną strukturę zdrowia aplikacji wraz z metadanymi środowiskowymi.
    """
    payload: Dict[str, Any] = {
        "status": "healthy",
        "version": app_version,
        "ts": _ts(),
        "env": {
            "LLM_BASE_URL": (os.getenv("LLM_BASE_URL") or "").strip(),
            "LLM_MODEL": (os.getenv("LLM_MODEL") or "").strip(),
            "LLM_API_KEY_set": bool((os.getenv("LLM_API_KEY") or "").strip()),
            "AUTH_TOKEN_set": bool((os.getenv("AUTH_TOKEN") or "").strip()),
            "REDIS_URL_set": bool((os.getenv("REDIS_URL") or "").strip()),
        },
    }

    if core_metrics is not None:
        try:
            payload["metrics"] = core_metrics.summary_stats()
        except Exception:
            payload["metrics"] = {"status": "error", "detail": "metrics_unavailable"}

    return payload
