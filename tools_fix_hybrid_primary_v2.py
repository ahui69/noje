#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import ast
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


PICKER_BLOCK = r'''
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


def _read_text() -> str:
    return TARGET.read_text(encoding="utf-8")


def _write_text(s: str) -> None:
    TARGET.write_text(s, encoding="utf-8")


def _backup(src: str, tag: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    b = TARGET.with_suffix(TARGET.suffix + f".bak.{tag}.{ts}")
    b.write_text(src, encoding="utf-8")
    return b


def _find_hybrid_endpoint_node(tree: ast.AST) -> ast.AST:
    # Szukamy funkcji z dekoratorem @router.post("/hybrid", ...)
    for node in getattr(tree, "body", []):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            if not (isinstance(func, ast.Attribute) and func.attr == "post"):
                continue
            if not isinstance(func.value, ast.Name):
                continue
            if func.value.id != "router":
                continue

            # pierwszy argument "/hybrid"
            if dec.args and isinstance(dec.args[0], ast.Constant) and dec.args[0].value == "/hybrid":
                return node

            # czasem ktoś daje path keywordem, ale u Ciebie raczej nie; dodajemy na wszelki wypadek
            for kw in dec.keywords or []:
                if kw.arg in ("path",) and isinstance(kw.value, ast.Constant) and kw.value.value == "/hybrid":
                    return node
    raise SystemExit('Nie znaleziono endpointu z dekoratorem @router.post("/hybrid", ...).')


def _ensure_helpers_inserted(lines: list[str], insert_line_1_based: int) -> list[str]:
    src = "".join(lines)
    need_call = "def _call_primary_hybrid" not in src
    need_pick = "def _mrd_pick_hybrid_callable" not in src
    if not (need_call or need_pick):
        return lines

    block = ""
    if need_call:
        block += CALL_HELPER_BLOCK
    if need_pick:
        block += PICKER_BLOCK
    if not block:
        return lines

    idx = max(0, insert_line_1_based - 1)
    return lines[:idx] + [block] + lines[idx:]


def _replace_span_with_line(lines: list[str], start_line: int, end_line: int, new_line: str) -> list[str]:
    # start_line/end_line są 1-based inclusive
    a = max(0, start_line - 1)
    b = max(0, end_line)  # slice end is exclusive already if we use b as end_line
    indent = ""
    if 0 <= a < len(lines):
        s = lines[a]
        i = 0
        while i < len(s) and s[i] in (" ", "\t"):
            indent += s[i]
            i += 1
    repl = indent + new_line.rstrip("\n") + "\n"
    return lines[:a] + [repl] + lines[b:]


def _patch_endpoint_body(tree: ast.AST, lines: list[str], fn_node: ast.AST) -> list[str]:
    # podmieniamy:
    # - pierwsze przypisanie do fn  -> fn = _mrd_pick_hybrid_callable()
    # - każde raw = fn(...)         -> raw = _call_primary_hybrid(fn, payload)
    fn_assign = None
    raw_assigns = []

    for stmt in getattr(fn_node, "body", []):
        # szukamy "fn = <call>()"
        if fn_assign is None and isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id == "fn":
                    fn_assign = stmt
                    break

        # szukamy "raw = fn(...)"
        if isinstance(stmt, ast.Try):
            # try body + except bodies
            for inner in stmt.body + [s for h in stmt.handlers for s in h.body]:
                if isinstance(inner, ast.Assign):
                    if len(inner.targets) == 1 and isinstance(inner.targets[0], ast.Name) and inner.targets[0].id == "raw":
                        if isinstance(inner.value, ast.Call) and isinstance(inner.value.func, ast.Name) and inner.value.func.id == "fn":
                            raw_assigns.append(inner)

        # też łapiemy proste raw = fn(...) bez try
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == "raw":
                if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == "fn":
                    raw_assigns.append(stmt)

    # patch w kolejności od dołu do góry, żeby linie się nie rozjechały
    # raw assigny
    for ra in sorted(raw_assigns, key=lambda n: (n.lineno, n.end_lineno or n.lineno), reverse=True):
        lines = _replace_span_with_line(
            lines,
            start_line=ra.lineno,
            end_line=ra.end_lineno or ra.lineno,
            new_line="raw = _call_primary_hybrid(fn, payload)",
        )

    # fn assign
    if fn_assign is not None:
        lines = _replace_span_with_line(
            lines,
            start_line=fn_assign.lineno,
            end_line=fn_assign.end_lineno or fn_assign.lineno,
            new_line="fn = _mrd_pick_hybrid_callable()",
        )
    else:
        # jeśli nie ma fn=..., to wstrzykujemy po pierwszym raw_hits/list init lub po t0
        insert_after = None
        for i in range(fn_node.lineno, min(len(lines) + 1, (fn_node.end_lineno or fn_node.lineno) + 1)):
            if "raw_hits" in lines[i - 1] or "t0" in lines[i - 1]:
                insert_after = i
                break
        if insert_after is None:
            insert_after = fn_node.lineno + 1

        idx = max(0, insert_after)
        # indent bierzemy z linii wewnątrz funkcji
        indent = "    "
        if 0 <= (idx - 1) < len(lines):
            s = lines[idx - 1]
            # jeśli linia jest w funkcji, zwykle ma 4 spacje, ale wyciągamy dynamicznie
            j = 0
            ind = ""
            while j < len(s) and s[j] in (" ", "\t"):
                ind += s[j]
                j += 1
            if ind:
                indent = ind
        lines = lines[:idx] + [indent + "fn = _mrd_pick_hybrid_callable()\n"] + lines[idx:]

    return lines


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Brak pliku: {TARGET}")

    src0 = _read_text()
    backup = _backup(src0, "pre_primary_fix_v2")

    try:
        tree = ast.parse(src0, filename=str(TARGET))
    except SyntaxError as e:
        raise SystemExit(f"Plik ma SyntaxError przed patchem: {e}")

    fn_node = _find_hybrid_endpoint_node(tree)

    lines = src0.splitlines(keepends=True)

    # insert helper blocks przed dekoratorem endpointu
    # decorator line = najwcześniejszy lineno z decorator_list
    dec_line = None
    for dec in getattr(fn_node, "decorator_list", []):
        if hasattr(dec, "lineno"):
            dec_line = dec.lineno if dec_line is None else min(dec_line, dec.lineno)
    if dec_line is None:
        dec_line = fn_node.lineno

    lines = _ensure_helpers_inserted(lines, insert_line_1_based=dec_line)

    # re-parse po insercie, żeby line numbers się zgadzały
    src1 = "".join(lines)
    tree2 = ast.parse(src1, filename=str(TARGET))
    fn_node2 = _find_hybrid_endpoint_node(tree2)

    lines2 = src1.splitlines(keepends=True)
    lines2 = _patch_endpoint_body(tree2, lines2, fn_node2)

    src_out = "".join(lines2)

    if src_out == src0:
        print("Brak zmian (wygląda na to, że już jest OK).")
        print(f"Backup: {backup}")
        return

    _write_text(src_out)
    py_compile.compile(str(TARGET), doraise=True)

    print(f"OK: spatchowano: {TARGET}")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", repr(e), file=sys.stderr)
        raise
