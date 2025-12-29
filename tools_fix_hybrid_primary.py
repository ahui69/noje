#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import re
import sys
import time
import py_compile

TARGET = Path("/root/mrd/core/hybrid_search_endpoint.py")

CALL_HELPER_BLOCK = r'''
def _call_primary_hybrid(fn, payload):
    """
    Wywołuje primary hybrid callable niezależnie od sygnatury.
    _maybe_await dalej robi await jeśli fn zwróci coroutine.
    """
    import inspect

    if fn is None:
        return None

    base = {
        "query": payload.query,
        "limit": int(payload.limit),
        "user_id": str(payload.user_id),
        "show_breakdown": bool(payload.show_breakdown),
        "min_score": float(payload.min_score),
    }

    try:
        sig = inspect.signature(fn)
        params = sig.parameters
        has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except Exception:
        sig = None
        params = {}
        has_varkw = False

    if has_varkw:
        return fn(**base)

    if sig is not None and params:
        filtered = {k: v for k, v in base.items() if k in params}
        if filtered:
            return fn(**filtered)

    try:
        return fn(payload.query, int(payload.limit), str(payload.user_id))
    except TypeError:
        return fn(payload.query, int(payload.limit))
'''.strip("\n") + "\n\n"


PICKER_IMPL = r'''
def _mrd_pick_hybrid_callable():
    """
    Zwraca najlepszą dostępną funkcję hybrydowego wyszukiwania.
    Priorytet:
      1) core.memory.ltm_search_hybrid (async)
      2) core.advanced_memory.ltm_search_enhanced (async)
      3) core.memory_store.search_memory (sync)
      4) core.memory_store.search_messages (sync)
    """
    # 1) core.memory
    try:
        from core import memory as m
        fn = getattr(m, "ltm_search_hybrid", None)
        if callable(fn):
            return fn
    except Exception:
        pass

    # 2) core.advanced_memory
    try:
        from core import advanced_memory as am
        fn = getattr(am, "ltm_search_enhanced", None)
        if callable(fn):
            return fn
    except Exception:
        pass

    # 3) core.memory_store
    try:
        from core import memory_store as ms
        for name in ("search_memory", "search_messages"):
            fn = getattr(ms, name, None)
            if callable(fn):
                return fn
    except Exception:
        pass

    return None
'''.strip("\n") + "\n\n"


def _read() -> str:
    return TARGET.read_text(encoding="utf-8")


def _write(s: str) -> None:
    TARGET.write_text(s, encoding="utf-8")


def _backup(src: str, tag: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    b = TARGET.with_suffix(TARGET.suffix + f".bak.{tag}.{ts}")
    b.write_text(src, encoding="utf-8")
    return b


def _extract_picker_name_from_search_hybrid(src: str) -> str | None:
    # Szuka w ciele search_hybrid linii: fn = SOMETHING()
    # i wyciąga SOMETHING
    m = re.search(r"(?ms)^async\s+def\s+search_hybrid\s*\(.*?\)\s*:\s*\n(.*?)(?=^\S)", src)
    if not m:
        return None
    body = m.group(1)
    m2 = re.search(r"(?m)^\s*fn\s*=\s*([A-Za-z_]\w*)\s*\(\s*\)\s*$", body)
    if not m2:
        return None
    return m2.group(1)


def _insert_helpers_before_route(src: str) -> str:
    # Wkładamy helper + picker tuż przed @router.post("/hybrid"...), to jest bezpieczne dla składni.
    if "def _mrd_pick_hybrid_callable" in src and "def _call_primary_hybrid" in src:
        return src

    route_pat = re.compile(r'(?m)^@router\.post\(\s*"/hybrid"')
    m = route_pat.search(src)
    if not m:
        raise SystemExit('Nie znaleziono dekoratora: @router.post("/hybrid"...')

    insert_at = m.start()
    block = ""
    if "def _call_primary_hybrid" not in src:
        block += CALL_HELPER_BLOCK
    if "def _mrd_pick_hybrid_callable" not in src:
        block += PICKER_IMPL

    return src[:insert_at] + block + src[insert_at:]


def _replace_fn_assignment_to_our_picker(src: str, detected_picker: str | None) -> str:
    # Zamienia "fn = <coś>()" na "fn = _mrd_pick_hybrid_callable()"
    # Jeśli nie wykryto, próbuje kilka standardów.
    if "fn = _mrd_pick_hybrid_callable()" in src:
        return src

    candidates = []
    if detected_picker:
        candidates.append(detected_picker)
    candidates += ["_pick_hybrid_callable", "_pick_hybrid_search_callable", "_pick_callable", "_get_hybrid_callable"]

    for name in candidates:
        pat = re.compile(rf"(?m)^(\s*)fn\s*=\s*{re.escape(name)}\s*\(\s*\)\s*$")
        if pat.search(src):
            return pat.sub(r"\1fn = _mrd_pick_hybrid_callable()", src, count=1)

    # fallback: jeśli w ogóle nie ma linii fn = ...(), dokładamy ją po deklaracji raw_hits
    m = re.search(r"(?m)^\s*raw_hits:\s*List\[Dict\[str,\s*Any\]\]\s*=\s*\[\]\s*$", src)
    if m:
        insert_at = m.end()
        return src[:insert_at] + "\n\n    fn = _mrd_pick_hybrid_callable()\n" + src[insert_at:]

    raise SystemExit("Nie udało się znaleźć ani podmienić linii 'fn = ...()' w search_hybrid.")


def _replace_callsite_raw_fn_to_helper(src: str) -> str:
    # W search_hybrid znajduje pierwsze "raw = fn(" i podmienia cały call expr na "raw = _call_primary_hybrid(fn, payload)"
    if "raw = _call_primary_hybrid(fn, payload)" in src:
        return src

    fn_pat = re.compile(r"(?m)^async\s+def\s+search_hybrid\s*\(.*\)\s*:\s*$")
    m = fn_pat.search(src)
    if not m:
        raise SystemExit("Nie znaleziono: async def search_hybrid(...):")
    pos = m.end()

    idx = src.find("raw = fn(", pos)
    if idx == -1:
        raise SystemExit("Nie znaleziono callsite: raw = fn(...")

    start = idx
    p0 = src.find("(", idx)
    if p0 == -1:
        raise SystemExit("Nie znaleziono '(' po 'raw = fn'.")

    i = p0
    depth = 0
    end = None
    while i < len(src):
        ch = src[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    if end is None:
        raise SystemExit("Nie domknięto nawiasów w raw = fn(...).")

    while end < len(src) and src[end] in " \t\r":
        end += 1
    if end < len(src) and src[end] == "\n":
        end += 1

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
    b = _backup(src0, "pre_primary_fix")

    picker = _extract_picker_name_from_search_hybrid(src0)

    src = src0
    src = _insert_helpers_before_route(src)
    src = _replace_fn_assignment_to_our_picker(src, picker)
    src = _replace_callsite_raw_fn_to_helper(src)

    if src == src0:
        print("Brak zmian (wygląda na to, że już jest OK).")
        print(f"Backup: {b}")
        return

    _write(src)
    py_compile.compile(str(TARGET), doraise=True)

    print(f"OK: spatchowano: {TARGET}")
    print(f"Backup: {b}")
    if picker:
        print(f"Wykryty picker w search_hybrid: {picker}")
    else:
        print("Nie wykryto pickera po nazwie (zrobiono fallback).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", repr(e), file=sys.stderr)
        raise
