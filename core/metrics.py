#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared Prometheus metrics utilities."""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

PROMETHEUS_AVAILABLE = False
try:  # pragma: no cover - optional dependency
    from prometheus_client import (  # type: ignore[import]
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback if prometheus_client missing
    CollectorRegistry = None  # type: ignore[assignment]
    Counter = None  # type: ignore[assignment]
    Gauge = None  # type: ignore[assignment]
    Histogram = None  # type: ignore[assignment]
    generate_latest = None  # type: ignore[assignment]

APP_START_TIME = time.time()
registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None

if PROMETHEUS_AVAILABLE:
    REQUESTS_TOTAL = Counter(
        "mordzix_requests_total",
        "Total requests",
        ["method", "endpoint", "status"],
        registry=registry,
    )
    REQUEST_DURATION = Histogram(
        "mordzix_request_duration_seconds",
        "Request duration",
        ["method", "endpoint"],
        registry=registry,
    )
    ERRORS_TOTAL = Counter(
        "mordzix_errors_total",
        "Total errors",
        ["type", "endpoint"],
        registry=registry,
    )
    UPTIME_GAUGE = Gauge(
        "mordzix_uptime_seconds",
        "Application uptime",
        registry=registry,
    )
    LLM_CACHE_SIZE = Gauge(
        "mordzix_llm_cache_size",
        "LLM cache size",
        registry=registry,
    )
    LLM_CACHE_HITS = Counter(
        "mordzix_llm_cache_hits_total",
        "LLM cache hits",
        registry=registry,
    )
    LLM_CACHE_MISSES = Counter(
        "mordzix_llm_cache_misses_total",
        "LLM cache misses",
        registry=registry,
    )
    EMBED_CACHE_SIZE = Gauge(
        "mordzix_embed_cache_size",
        "Embedding cache size",
        registry=registry,
    )
    EMBED_CACHE_HITS = Counter(
        "mordzix_embed_cache_hits_total",
        "Embedding cache hits",
        registry=registry,
    )
    EMBED_CACHE_MISSES = Counter(
        "mordzix_embed_cache_misses_total",
        "Embedding cache misses",
        registry=registry,
    )
    STM_MESSAGES = Gauge(
        "mordzix_stm_messages",
        "Number of STM messages",
        ["user_id"],
        registry=registry,
    )
    LTM_FACTS = Gauge(
        "mordzix_ltm_facts",
        "Number of LTM facts",
        registry=registry,
    )
    PSYCHE_MOOD = Gauge(
        "mordzix_psyche_mood",
        "Current psyche mood",
        registry=registry,
    )
    PSYCHE_ENERGY = Gauge(
        "mordzix_psyche_energy",
        "Current psyche energy",
        registry=registry,
    )
    PSYCHE_FOCUS = Gauge(
        "mordzix_psyche_focus",
        "Current psyche focus",
        registry=registry,
    )
else:  # pragma: no cover - ensure names exist for importers
    REQUESTS_TOTAL = None
    REQUEST_DURATION = None
    ERRORS_TOTAL = None
    UPTIME_GAUGE = None
    LLM_CACHE_SIZE = None
    LLM_CACHE_HITS = None
    LLM_CACHE_MISSES = None
    EMBED_CACHE_SIZE = None
    EMBED_CACHE_HITS = None
    EMBED_CACHE_MISSES = None
    STM_MESSAGES = None
    LTM_FACTS = None
    PSYCHE_MOOD = None
    PSYCHE_ENERGY = None
    PSYCHE_FOCUS = None

_METRICS_ENDPOINT_REQUESTS = 0
_METRICS_ENDPOINT_ERRORS = 0


def record_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """Record request counters if Prometheus is enabled."""

    if not PROMETHEUS_AVAILABLE or REQUESTS_TOTAL is None or REQUEST_DURATION is None:
        return

    REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_error(error_type: str, endpoint: str) -> None:
    """Record an error occurrence."""

    global _METRICS_ENDPOINT_ERRORS
    _METRICS_ENDPOINT_ERRORS += 1

    if not PROMETHEUS_AVAILABLE or ERRORS_TOTAL is None:
        return

    ERRORS_TOTAL.labels(type=error_type, endpoint=endpoint).inc()


def increment_metrics_endpoint_requests() -> None:
    """Track how many times the metrics endpoint was queried."""

    global _METRICS_ENDPOINT_REQUESTS
    _METRICS_ENDPOINT_REQUESTS += 1


def update_llm_cache_size(size: int) -> None:
    if PROMETHEUS_AVAILABLE and LLM_CACHE_SIZE is not None:
        LLM_CACHE_SIZE.set(size)


def record_llm_cache_hit() -> None:
    if PROMETHEUS_AVAILABLE and LLM_CACHE_HITS is not None:
        LLM_CACHE_HITS.inc()


def record_llm_cache_miss() -> None:
    if PROMETHEUS_AVAILABLE and LLM_CACHE_MISSES is not None:
        LLM_CACHE_MISSES.inc()


def update_embed_cache_size(size: int) -> None:
    if PROMETHEUS_AVAILABLE and EMBED_CACHE_SIZE is not None:
        EMBED_CACHE_SIZE.set(size)


def record_embed_cache_hit() -> None:
    if PROMETHEUS_AVAILABLE and EMBED_CACHE_HITS is not None:
        EMBED_CACHE_HITS.inc()


def record_embed_cache_miss() -> None:
    if PROMETHEUS_AVAILABLE and EMBED_CACHE_MISSES is not None:
        EMBED_CACHE_MISSES.inc()


def _collect_db_stats() -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    db_path = os.getenv("MEM_DB")
    if not db_path:
        workspace = os.getenv("WORKSPACE")
        if workspace:
            db_path = str(Path(workspace) / "mem.db")
        else:
            db_path = "mem.db"

    if not os.path.exists(db_path):
        return result

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ltm")
        result["ltm_facts"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM files")
        result["files_uploaded"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM psyche")
        result["psyche_entries"] = cursor.fetchone()[0]
        conn.close()
    except Exception as exc:  # pragma: no cover - diagnostics only
        result["db_error"] = str(exc)

    return result


def _fallback_metrics() -> str:
    lines = []
    uptime = time.time() - APP_START_TIME
    lines.append("# HELP mordzix_uptime_seconds Application uptime")
    lines.append("# TYPE mordzix_uptime_seconds gauge")
    lines.append(f"mordzix_uptime_seconds {uptime:.0f}")
    lines.append("")

    db_stats = _collect_db_stats()
    if "db_error" in db_stats:
        lines.append(f"# Database error: {db_stats['db_error']}")
        lines.append("")
    else:
        if "ltm_facts" in db_stats:
            lines.append("# HELP mordzix_ltm_facts Number of LTM facts")
            lines.append("# TYPE mordzix_ltm_facts gauge")
            lines.append(f"mordzix_ltm_facts {db_stats['ltm_facts']}")
            lines.append("")
        if "files_uploaded" in db_stats:
            lines.append("# HELP mordzix_files_uploaded Number of uploaded files")
            lines.append("# TYPE mordzix_files_uploaded gauge")
            lines.append(f"mordzix_files_uploaded {db_stats['files_uploaded']}")
            lines.append("")
        if "psyche_entries" in db_stats:
            lines.append("# HELP mordzix_psyche_entries Psyche entries count")
            lines.append("# TYPE mordzix_psyche_entries gauge")
            lines.append(f"mordzix_psyche_entries {db_stats['psyche_entries']}")
            lines.append("")

    try:  # pragma: no cover - optional dependency
        import psutil  # type: ignore[import]

        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        lines.append("# HELP mordzix_memory_mb Memory usage in MB")
        lines.append("# TYPE mordzix_memory_mb gauge")
        lines.append(f"mordzix_memory_mb {mem_mb:.2f}")
        lines.append("")
    except Exception:
        pass

    return "\n".join(lines)


def export_metrics() -> str:
    """Return metrics in Prometheus text format."""

    if PROMETHEUS_AVAILABLE and registry is not None and generate_latest is not None:
        if UPTIME_GAUGE is not None:
            UPTIME_GAUGE.set(time.time() - APP_START_TIME)
        return generate_latest(registry).decode("utf-8")

    return _fallback_metrics()


def health_payload() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "uptime": time.time() - APP_START_TIME,
        "timestamp": time.time(),
        "prometheus": PROMETHEUS_AVAILABLE,
    }


def summary_stats() -> Dict[str, Any]:
    stats: Dict[str, Any] = {
        "uptime_seconds": time.time() - APP_START_TIME,
        "requests_total": _METRICS_ENDPOINT_REQUESTS,
        "errors_total": _METRICS_ENDPOINT_ERRORS,
        "prometheus": PROMETHEUS_AVAILABLE,
    }
    stats.update(_collect_db_stats())
    return stats


def reset_metrics_for_tests() -> None:
    """Utility for tests to reset counters."""

    global _METRICS_ENDPOINT_REQUESTS, _METRICS_ENDPOINT_ERRORS
    _METRICS_ENDPOINT_REQUESTS = 0
    _METRICS_ENDPOINT_ERRORS = 0

    if not PROMETHEUS_AVAILABLE:
        return

    if REQUESTS_TOTAL is not None:
        REQUESTS_TOTAL.clear()  # type: ignore[attr-defined]
    if REQUEST_DURATION is not None:
        REQUEST_DURATION.clear()  # type: ignore[attr-defined]
    if ERRORS_TOTAL is not None:
        ERRORS_TOTAL.clear()  # type: ignore[attr-defined]
    if LLM_CACHE_SIZE is not None:
        LLM_CACHE_SIZE.set(0)
    if LLM_CACHE_HITS is not None:
        LLM_CACHE_HITS._value.set(0)  # type: ignore[attr-defined]
    if LLM_CACHE_MISSES is not None:
        LLM_CACHE_MISSES._value.set(0)  # type: ignore[attr-defined]
    if EMBED_CACHE_SIZE is not None:
        EMBED_CACHE_SIZE.set(0)
    if EMBED_CACHE_HITS is not None:
        EMBED_CACHE_HITS._value.set(0)  # type: ignore[attr-defined]
    if EMBED_CACHE_MISSES is not None:
        EMBED_CACHE_MISSES._value.set(0)  # type: ignore[attr-defined]
    if STM_MESSAGES is not None:
        STM_MESSAGES.clear()  # type: ignore[attr-defined]
    if LTM_FACTS is not None:
        LTM_FACTS.set(0)
    if PSYCHE_MOOD is not None:
        PSYCHE_MOOD.set(0)
    if PSYCHE_ENERGY is not None:
        PSYCHE_ENERGY.set(0)
    if PSYCHE_FOCUS is not None:
        PSYCHE_FOCUS.set(0)


__all__ = [
    "PROMETHEUS_AVAILABLE",
    "registry",
    "REQUESTS_TOTAL",
    "REQUEST_DURATION",
    "ERRORS_TOTAL",
    "record_request",
    "record_error",
    "increment_metrics_endpoint_requests",
    "record_llm_cache_hit",
    "record_llm_cache_miss",
    "update_llm_cache_size",
    "record_embed_cache_hit",
    "record_embed_cache_miss",
    "update_embed_cache_size",
    "export_metrics",
    "health_payload",
    "summary_stats",
]
