#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import sys
import re
import time

TARGET = Path("/root/mrd/core/hybrid_search_endpoint.py")

CALL_HELPER_BLOCK = r'''
def _call_primary_hybrid(fn, payload):
    """
    Wywołuje 'primary' funkcję hybrid search niezależnie od jej sygnatury:
    - najpierw próbuje keyword-args (query/limit/user_id/show_breakdown/min_score jeśli istnieją)
    - potem pozycyjne warianty (query, limit, user_id) albo (query, limit)
    """
    import inspect

    if fn is None:
        return None

    # Prefer keyword call (best for richer implementations)
    try:
        sig = inspect.signature(fn)
        params = sig.parameters
        kwargs = {}
        if "query" in params:
            kwargs["query"] = payload.query
        if "limit" in params:
            kwargs["limit"] = int(payload.limit)
        if "user_id" in params:
            kwargs["user_id"] = str(payload.user_id)
        if "show_breakdown" in params:
            kwargs["show_breakdown"] = bool(payload.show_breakdown)
        if "min_score" in params:
            kwargs["min_score"] = float(payload.min_score)
        if kwargs:
            return fn(**kwargs)
    except Exception:
        # jeśli signature nie działa (np. built-in/extension) to spadamy do positional
        pass

    # Positional fallbacks
    try:
        return fn(payload.query, int(payload.limit), str(payload.user_id))
    except TypeError:
        return fn(payload.query, int(payload.limit))
'''.strip("\n") + "\n"


PICK_FUNC_REPLACEMENT = r'''
def _pick_hybrid_callable():
    """
    Zwraca najlepszą dostępną funkcję hybrydowego wyszukiwania.
    Priorytet:
      1) core.memory.ltm_search_hybrid (async)
      2) core.advanced_memory.ltm_search_enhanced (async)
      3) core.memory_store.search_memory (sync)
      4) core.memory_store.search_messages (sync)
    """
    candidates = []

    # 1) core.memory
    try:
        from core import memory as m
        for name in ("ltm_search_hybrid", "ltm_search_bm25", "memory_search"):
            fn = getattr(m, name, None)
            if callable(fn):
                candidates.append(("core.memory." + name, fn))
    except Exception:
        pass

    # 2) core.advanced_memory
    try:
        from core import advanced_memory as am
        for name in ("ltm_search_enhanced",):
            fn = getattr(am, name, None)
            if callable(fn):
                candidates.append(("core.advanced_memory." + name, fn))
    except Exception:
        pass

    # 3) core.memory_store
    try:
        from core import memory_store as ms
        for name in ("search_memory", "search_messages"):
            fn = getattr(ms, name, None)
            if callable(fn):
                candidates.append(("core.memory_store." + name, fn))
    except Exception:
        pass

    # Prefer explicit hybrid/semantic functions first
    for prefix in ("core.memory.ltm_search_hybrid", "core.advanced_memory.ltm_search_enhanced", "core.memory_store.search_memory"):
        for name, fn in candidates:
            if name == prefix:
                return fn

    # Otherwise return first callable found
    if candidates:
        return candidates[0][1]

    return None
'''.strip("\n") + "\n"


def _read() -> str:
    return TARGET.read_text(encoding="utf-8")


def _write(s: str) -> None:
    TARGET.write_text(s, encoding="utf-8")


def _backup(src: str, tag: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    b = TARGET.with_suffix(TARGET.suffix + f".bak.{tag}.{ts}")
    b.write_text(src, encoding="utf-8")
    return b


def _find_top_level_block(src: str, start_pat: re.Pattern) -> tuple[int, int]:
    m = start_pat.search(src)
    if not m:
        return (-1, -1)
    start = m.start()

    # find end: next top-level def/class/decorator/router/app or EOF
    next_pat = re.compile(r"(?m)^(def\s+|class\s+|@router\.|@app\.)")
    m2 = next_pat.search(src, m.end())
    end = m2.start() if m2 else len(src)
    return (start, end)


def _replace_pick_callable(src: str) -> str:
    start_pat = re.compile(r"(?m)^def\s+_pick_hybrid_callable\s*\(\s*\)\s*:\s*$")
    a, b = _find_top_level_block(src, start_pat)
    if a == -1:
        raise SystemExit("Nie znaleziono: def _pick_hybrid_callable():")
    return src[:a] + PICK_FUNC_REPLACEMENT + src[b:]


def _ensure_call_helper_before_route(src: str) -> str:
    if "def _call_primary_hybrid" in src:
        return src

    route_pat = re.compile(r'(?m)^@router\.post\(\s*"/hybrid"')
    m = route_pat.search(src)
    if not m:
        raise SystemExit('Nie znaleziono dekoratora: @router.post("/hybrid"...')
    insert_at = m.start()
    return src[:insert_at] + CALL_HELPER_BLOCK + "\n" + src[insert_at:]


def _replace_callsite_inside_search_hybrid(src: str) -> str:
    # locate search_hybrid function
    fn_pat = re.compile(r"(?m)^async\s+def\s+search_hybrid\s*\(.*\)\s*:\s*$")
    m = fn_pat.search(src)
    if not m:
        raise SystemExit("Nie znaleziono: async def search_hybrid(...):")
    pos = m.end()

    # from pos, find first occurrence of "raw = fn(" at indentation inside function
    idx = src.find("raw = fn(", pos)
    if idx == -1:
        # maybe already patched
        if "raw = _call_primary_hybrid(fn, payload)" in src:
            return src
        raise SystemExit("Nie znaleziono callsite: raw = fn(...")

    # replace that whole call expression, counting parentheses until it closes
    start = idx
    # find the first '(' after "raw = fn"
    p0 = src.find("(", idx)
    if p0 == -1:
        raise SystemExit("Nie znaleziono '(' w raw = fn(")

    i = p0
    depth = 0
    while i < len(src):
        ch = src[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                # include closing ')'
                end = i + 1
                break
        i += 1
    else:
        raise SystemExit("Nie domknięto nawiasów w raw = fn(...).")

    # also consume trailing whitespace/newline(s)
    while end < len(src) and src[end] in " \t\r":
        end += 1
    if end < len(src) and src[end] == "\n":
        end += 1

    # preserve indentation of the original line
    line_start = src.rfind("\n", 0, start) + 1
    indent = ""
    j = line_start
    while j < len(src) and src[j] in (" ", "\t"):
        indent += src[j]
        j += 1

    replacement = indent + "raw = _call_primary_hybrid(fn, payload)\n"
    return src[:start] + replacement + src[end:]


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Brak pliku: {TARGET}")

    src0 = _read()
    b = _backup(src0, "pre_hybrid_fix")

    src = src0
    src = _replace_pick_callable(src)
    src = _ensure_call_helper_before_route(src)
    src = _replace_callsite_inside_search_hybrid(src)

    if src == src0:
        print("Brak zmian (wygląda na to, że patch już jest).")
        print(f"Backup (pre-run): {b}")
        return

    _write(src)

    # hard compile check
    import py_compile
    py_compile.compile(str(TARGET), doraise=True)

    print(f"OK: naprawiono i spatchowano: {TARGET}")
    print(f"Backup (pre-run): {b}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", repr(e), file=sys.stderr)
        raise
