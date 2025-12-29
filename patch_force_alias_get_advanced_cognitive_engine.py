#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/core/advanced_cognitive_engine.py")

def backup(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(path) + f".bak.{ts}")
    b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def main() -> int:
    if not P.exists():
        print(f"[ERR] missing file: {P}", file=sys.stderr)
        return 2

    s = P.read_text(encoding="utf-8")

    if re.search(r"(?m)^\s*get_advanced_cognitive_engine\s*=\s*get_engine\s*$", s):
        print("[OK] alias get_advanced_cognitive_engine = get_engine already present")
        return 0

    if not re.search(r"(?m)^\s*def\s+get_engine\s*\(", s):
        print("[ERR] get_engine() not found in advanced_cognitive_engine.py", file=sys.stderr)
        return 3

    insert = (
        "\n\n"
        "# Backward-compatible alias required by routers/imports\n"
        "get_advanced_cognitive_engine = get_engine\n"
        "\n"
    )

    lines = s.splitlines(True)

    # wstaw przed __main__ jeśli istnieje
    idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*if\s+__name__\s*==\s*[\"']__main__[\"']\s*:", ln):
            idx = i
            break

    b = backup(P)
    if idx is None:
        out = s + insert
    else:
        out = "".join(lines[:idx]) + insert + "".join(lines[idx:])

    P.write_text(out, encoding="utf-8")
    print(f"[OK] patched {P} (backup: {b}) added alias get_advanced_cognitive_engine = get_engine")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
