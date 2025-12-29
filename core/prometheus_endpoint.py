#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus metrics endpoint - monitoring i statystyki
"""

import os
from fastapi import APIRouter, Response
from typing import Dict, Any

from core import metrics as core_metrics
from health_payload import build_health_payload

router = APIRouter()

@router.get("/metrics")
async def get_prometheus_metrics():
    """Endpoint dla Prometheus - metryki w formacie tekstowym"""
    core_metrics.increment_metrics_endpoint_requests()
    try:
        content = core_metrics.export_metrics()
    except Exception:
        core_metrics.record_error("metrics_export", "/api/prometheus/metrics")
        raise
    return Response(content=content, media_type="text/plain")

@router.get("/health")
async def health_check():
    """Health check dla Prometheus"""
    return build_health_payload(app_version=os.getenv("APP_VERSION", "unknown"))

@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Statystyki w formacie JSON"""
    return core_metrics.summary_stats()
