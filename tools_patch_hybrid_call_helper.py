#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import re
import time
import py_compile

TARGET = Path("/root/mrd/core/hybrid_search_endpoint.py")

NEW_HELPER = r'''
def _call_primary_hybrid(fn, payload):
    """
    Best-effort wywołanie primary hybrid callable bez wywalania endpointu.
    Celowo NIE przekazuje `show_breakdown` (to debug endpointu, nie parametr wyszukiwarki).

    Zasada:
      - najpierw próba kwargs (tylko te, które funkcja przyjmuje albo **kwargs),
      - przy TypeError (np. unexpected keyword) spadamy do pozycyjnych wariantów.
    """
    import inspect

    if fn is None:
        return None

    query = payload.query
    limit = int(payload.limit)
    user_id = str(payload.user_id)
    min_score = float(payload.min_score)

    base = {
        "query": query,
        "limit": limit,
        "user_id": user_id,
        "min_score": min_score,
    }

    try:
        sig = inspect.signature(fn)
        params = sig.parameters
        has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except Exception:
        sig = None
        params = {}
        has_varkw = False

    # 1) kwargs (najczystsze)
    if has_varkw:
        try:
            return fn(**base)
        except TypeError:
            pass

    if sig is not None and params:
        filtered = {k: v for k, v in base.items() if k in params}
        if filtered:
            try:
                return fn(**filtered)
            except TypeError:
                pass

    # 2) positional fallbacks (różne spotykane sygnatury)
    candidates = [
        (query, limit, user_id, min_score),
        (query, limit, user_id),
        (query, limit),
        (query,),
    ]
    for args in candidates:
        try:
            return fn(*args)
        except TypeError:
            continue

    # 3) last resort
    return fn(query)
'''.strip("\n") + "\n\n"


def backup_text(src: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    b = TARGET.with_suffix(TARGET.suffix + f".bak.call_helper.{ts}")
    b.write_text(src, encoding="utf-8")
    return b


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Brak pliku: {TARGET}")

    src0 = TARGET.read_text(encoding="utf-8")
    b = backup_text(src0)

    pat = re.compile(
        r"(?ms)^def\s+_call_primary_hybrid\s*\(\s*fn\s*,\s*payload\s*\)\s*:\s*\n"
        r"(?:[ \t].*\n)*?\n"
    )

    m = pat.search(src0)
    if not m:
        raise SystemExit("Nie znaleziono bloku: def _call_primary_hybrid(fn, payload):")

    src1 = src0[:m.start()] + NEW_HELPER + src0[m.end():]

    if src1 == src0:
        print("Brak zmian (wygląda na to, że helper już jest taki jak trzeba).")
        print(f"Backup: {b}")
        return

    TARGET.write_text(src1, encoding="utf-8")
    py_compile.compile(str(TARGET), doraise=True)

    print(f"OK: spatchowano helper w: {TARGET}")
    print(f"Backup: {b}")


if __name__ == "__main__":
    main()
