#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

TARGET = Path("/root/mrd/core/hierarchical_memory.py")

AWAIT_METHOD = """
    def __await__(self):
        async def _coro():
            return self
        return _coro().__await__()
""".lstrip("\n")

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"[ERR] Missing file: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    # already patched?
    if re.search(r"^\s*def\s+__await__\s*\(", src, flags=re.M):
        print("[OK] __await__ already present. Nothing to do.")
        return 0

    m = re.search(r"^class\s+HierarchicalMemorySystem\b.*:\s*$", src, flags=re.M)
    if not m:
        raise SystemExit("[ERR] Could not find class HierarchicalMemorySystem in hierarchical_memory.py")

    # find insertion point: after class line + optional docstring
    start = m.end()
    rest = src[start:]

    # position in original string
    insert_at = start

    # skip whitespace/newlines
    ws = re.match(r"^\s*\n", rest)
    if ws:
        insert_at += ws.end()
        rest = src[insert_at:]

    # if docstring starts immediately
    ds = re.match(r'^(\s*)(["\']{3})', rest)
    if ds:
        indent = ds.group(1)
        quote = ds.group(2)
        # find end of docstring
        end_idx = rest.find(quote, ds.end())
        if end_idx != -1:
            end_idx += len(quote)
            # move insert point to after docstring line(s)
            insert_at += end_idx
            # also move to end-of-line if not already
            nl = src.find("\n", insert_at)
            if nl != -1:
                insert_at = nl + 1

    patched = src[:insert_at] + AWAIT_METHOD + "\n" + src[insert_at:]

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(TARGET.suffix + f".bak.{ts}")
    backup.write_text(src, encoding="utf-8")
    TARGET.write_text(patched, encoding="utf-8")

    print(f"[OK] Patched: {TARGET}")
    print(f"[BACKUP] {backup}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
