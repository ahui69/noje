#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

ROOT = Path("/root/mrd")

EXCLUDE_PARTS = (
    "/.venv/",
    "/venv/",
    "/node_modules/",
    "/__pycache__/",
    "/.git/",
)

def backup(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(path) + f".bak.{ts}")
    b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def should_skip(p: Path) -> bool:
    sp = str(p)
    return any(part in sp for part in EXCLUDE_PARTS)

DECOR_RE = re.compile(
    r"(?m)^(\s*)@([A-Za-z_]\w*router\w*)\.exception_handler\((.*?)\)\s*$"
)

CALL_RE = re.compile(
    r"([A-Za-z_]\w*router\w*)\.exception_handler\("
)

def patch_text(s: str) -> tuple[str, int]:
    changed = 0
    s2 = s

    # decorators
    def _dec_sub(m: re.Match) -> str:
        nonlocal changed
        indent, var, inside = m.group(1), m.group(2), m.group(3)
        changed += 1
        return f'{indent}# @{var}.exception_handler({inside})  # disabled: APIRouter has no exception_handler'

    s2 = DECOR_RE.sub(_dec_sub, s2)

    # calls (do not touch app.exception_handler)
    out_lines = []
    for ln in s2.splitlines(True):
        if "exception_handler" in ln and "app.exception_handler" not in ln and CALL_RE.search(ln):
            ln2 = CALL_RE.sub(r"# \1.exception_handler(", ln)
            if ln2 != ln:
                changed += 1
                out_lines.append(ln2)
                continue
        out_lines.append(ln)

    return "".join(out_lines), changed

def main() -> int:
    if not ROOT.exists():
        print(f"[ERR] missing root: {ROOT}", file=sys.stderr)
        return 2

    patched_files = 0
    for p in ROOT.rglob("*.py"):
        if should_skip(p):
            continue
        s = p.read_text(encoding="utf-8")
        s2, ch = patch_text(s)
        if ch:
            b = backup(p)
            p.write_text(s2, encoding="utf-8")
            patched_files += 1
            print(f"[OK] patched {p} (backup: {b}) changes={ch}")

    print(f"[DONE] files patched: {patched_files}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
