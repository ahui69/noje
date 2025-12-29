#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


TARGET = Path("/root/mrd/core/hybrid_search_endpoint.py")


NEW_FUNC = r'''
_HYBRID_CALLABLE = None

def _pick_hybrid_callable():
    """
    Resolve the primary hybrid search implementation.

    Resolution order:
      1) HYBRID_SEARCH_FUNC="module:function"
      2) hardcoded candidates (best-effort autodiscovery)

    Returns:
      callable or None
    """
    global _HYBRID_CALLABLE
    if _HYBRID_CALLABLE is not None:
        return _HYBRID_CALLABLE

    import importlib
    import inspect

    spec = (os.getenv("HYBRID_SEARCH_FUNC") or "").strip()

    candidates = []
    if spec:
        candidates.append(spec)

    # Best-effort candidates across typical MRD modules.
    candidates += [
        "core.memory:hybrid_search",
        "core.memory:search_hybrid",
        "core.memory_store:hybrid_search",
        "core.semantic:hybrid_search",
        "core.semantic:search",
        "core.hybrid_search:hybrid_search",
        "core.hierarchical_memory:hybrid_search",
        "core.advanced_memory:hybrid_search",
        "core.advanced_cognitive_engine:hybrid_search",
        "core.smart_context:hybrid_search",
        "core.hybrid_search_endpoint:hybrid_search_impl",
    ]

    this_file = __file__

    for cand in candidates:
        if ":" not in cand:
            continue
        mod_name, fn_name = cand.split(":", 1)
        mod_name = mod_name.strip()
        fn_name = fn_name.strip()
        if not mod_name or not fn_name:
            continue

        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue

        fn = getattr(mod, fn_name, None)
        if fn is None or not callable(fn):
            continue

        # Avoid picking the API endpoint itself or anything from this file named search_hybrid.
        try:
            src_file = inspect.getsourcefile(fn) or ""
        except Exception:
            src_file = ""

        if (fn.__name__ == "search_hybrid") and (src_file == this_file):
            continue

        _HYBRID_CALLABLE = fn
        return fn

    _HYBRID_CALLABLE = None
    return None
'''.lstrip("\n")


def replace_function(src: str, func_name: str, new_block: str) -> str:
    # Find "def _pick_hybrid_callable" at top-level.
    m = re.search(rf"(?m)^def\s+{re.escape(func_name)}\s*\(.*\)\s*:\s*$", src)
    if not m:
        raise SystemExit(f"Cannot find function definition: {func_name}")

    start = m.start()

    # Determine end: next top-level "def " or "class " or decorator "@"
    # after the function block.
    lines = src.splitlines(True)
    # Map absolute index -> (line_no, col)
    abs_i = 0
    start_line = None
    for i, line in enumerate(lines):
        if abs_i <= start < abs_i + len(line):
            start_line = i
            break
        abs_i += len(line)
    if start_line is None:
        raise SystemExit("Internal error locating start line")

    # We assume top-level function (no indent).
    end_line = None
    for j in range(start_line + 1, len(lines)):
        l = lines[j]
        if re.match(r"(?m)^(def\s+|class\s+|@)", l):
            end_line = j
            break
    if end_line is None:
        end_line = len(lines)

    before = "".join(lines[:start_line])
    after = "".join(lines[end_line:])

    # Ensure new block ends with exactly one blank line for cleanliness.
    nb = new_block.rstrip() + "\n\n"
    return before + nb + after


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Target file not found: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")
    out = replace_function(src, "_pick_hybrid_callable", NEW_FUNC)

    if out == src:
        print("No changes made (already patched?)")
        return

    backup = TARGET.with_suffix(TARGET.suffix + ".bak.pickhybrid")
    backup.write_text(src, encoding="utf-8")
    TARGET.write_text(out, encoding="utf-8")
    print(f"Patched: {TARGET}")
    print(f"Backup : {backup}")


if __name__ == "__main__":
    main()
