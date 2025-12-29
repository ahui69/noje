#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("/root/mrd/core/hybrid_search_endpoint.py")

INSERT_BLOCK = r'''
def _call_primary_hybrid(fn, payload):
    """
    Call primary hybrid search function with best-effort signature adaptation.
    Supports both sync and async callables (await handled by _maybe_await).
    """
    import inspect

    base = {
        "query": payload.query,
        "limit": int(payload.limit),
        "user_id": str(payload.user_id),
        "show_breakdown": bool(payload.show_breakdown),
        "min_score": float(payload.min_score),
    }

    # Signature-aware mapping
    try:
        sig = inspect.signature(fn)
        params = sig.parameters
        has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except Exception:
        sig = None
        params = {}
        has_varkw = False

    # Candidate name mapping
    mapped = dict(base)

    # query aliases
    if "query" not in params and not has_varkw:
        for alt in ("q", "text", "prompt", "term"):
            if alt in params:
                mapped[alt] = mapped["query"]
                break

    # limit aliases
    if "limit" not in params and not has_varkw:
        for alt in ("top_k", "k", "n", "max_results"):
            if alt in params:
                mapped[alt] = mapped["limit"]
                break

    # user_id aliases
    if "user_id" not in params and not has_varkw:
        for alt in ("user", "uid", "owner", "session_user"):
            if alt in params:
                mapped[alt] = mapped["user_id"]
                break

    # min_score aliases
    if "min_score" not in params and not has_varkw:
        for alt in ("threshold", "minsim", "min_similarity", "min_confidence"):
            if alt in params:
                mapped[alt] = mapped["min_score"]
                break

    # show_breakdown aliases
    if "show_breakdown" not in params and not has_varkw:
        for alt in ("breakdown", "with_breakdown", "debug"):
            if alt in params:
                mapped[alt] = mapped["show_breakdown"]
                break

    # Final kwargs
    if has_varkw:
        return fn(**mapped)

    if sig is not None:
        filtered = {k: v for k, v in mapped.items() if k in params}
        if filtered:
            return fn(**filtered)

    # Positional fallback (common patterns)
    try:
        return fn(payload.query, int(payload.limit), str(payload.user_id))
    except TypeError:
        return fn(payload.query, int(payload.limit))
'''.strip("\n") + "\n\n"


def patch_insert_after_maybe_await(src: str) -> str:
    # Find the end of async def _maybe_await(...) block, then insert helper.
    m = re.search(r"(?ms)^async\s+def\s+_maybe_await\s*\(.*?\)\s*:\s*\n(.*?)(?=^\S)", src)
    if not m:
        raise SystemExit("Nie znaleziono bloku: async def _maybe_await(...)")
    end = m.end()
    return src[:end] + "\n" + INSERT_BLOCK + src[end:]


def patch_callsite(src: str) -> str:
    # Replace the primary call raw = fn(query=..., limit=..., user_id=..., show_breakdown=..., min_score=...,)
    # with raw = _call_primary_hybrid(fn, payload)
    pat = re.compile(
        r"(?ms)"
        r"raw\s*=\s*fn\s*\(\s*"
        r"(?:query\s*=\s*payload\.query\s*,\s*)"
        r"(?:limit\s*=\s*int\(payload\.limit\)\s*,\s*)"
        r"(?:user_id\s*=\s*str\(payload\.user_id\)\s*,\s*)"
        r"(?:show_breakdown\s*=\s*bool\(payload\.show_breakdown\)\s*,\s*)"
        r"(?:min_score\s*=\s*float\(payload\.min_score\)\s*,?\s*)"
        r"\)\s*"
    )
    if not pat.search(src):
        raise SystemExit("Nie znaleziono call-site fn(query=..., limit=..., ...) do podmiany (wzorzec nie pasuje).")

    src = pat.sub("raw = _call_primary_hybrid(fn, payload)\n", src, count=1)
    return src


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Brak pliku: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if "_call_primary_hybrid" not in src:
        src = patch_insert_after_maybe_await(src)

    src2 = patch_callsite(src)

    if src2 == TARGET.read_text(encoding="utf-8"):
        print("Brak zmian (wygląda na to, że patch już jest).")
        return

    backup = TARGET.with_suffix(TARGET.suffix + ".bak.callsite")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src2, encoding="utf-8")

    print(f"OK: spatchowano {TARGET}")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
