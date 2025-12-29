#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/core/advanced_cognitive_engine.py")

FUT_RE = re.compile(r"^\s*from\s+__future__\s+import\b.*$", re.M)

def backup(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(path) + f".bak.{ts}")
    b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def split_lines(s: str) -> list[str]:
    return s.splitlines(True)

def find_after_header_and_docstring(lines: list[str]) -> int:
    i = 0
    # shebang / coding comments
    while i < len(lines) and (lines[i].startswith("#!") or "coding" in lines[i]):
        i += 1

    # module docstring (must remain before __future__)
    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        q = lines[i].lstrip()[:3]
        i += 1
        while i < len(lines) and q not in lines[i]:
            i += 1
        if i < len(lines):
            i += 1

    return i

def main() -> int:
    if not P.exists():
        print(f"[ERR] missing file: {P}", file=sys.stderr)
        return 2

    s = P.read_text(encoding="utf-8")
    lines = split_lines(s)

    # collect all future-import lines (preserve order, de-dup exact lines)
    future_lines: list[str] = []
    seen = set()
    for ln in lines:
        if FUT_RE.match(ln):
            norm = ln.strip()
            if norm and norm not in seen:
                seen.add(norm)
                future_lines.append(norm)

    # remove all future import lines from file
    kept: list[str] = []
    removed = 0
    for ln in lines:
        if FUT_RE.match(ln):
            removed += 1
            continue
        kept.append(ln)

    insert_at = find_after_header_and_docstring(kept)

    # if no future imports existed, keep at least annotations (safe default)
    if not future_lines:
        future_lines = ["from __future__ import annotations"]

    block = "".join(f"{x}\n" for x in future_lines)

    # avoid double insert if someone already has future at correct place
    # (we removed all, so this is safe)
    out = "".join(kept[:insert_at]) + block + "".join(kept[insert_at:])

    b = backup(P)
    P.write_text(out, encoding="utf-8")

    print(f"[OK] patched {P} (backup: {b}) removed_future_lines={removed} inserted={len(future_lines)} at={insert_at}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
