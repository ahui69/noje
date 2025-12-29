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
    for part in EXCLUDE_PARTS:
        if part in sp:
            return True
    return False

def patch_file(p: Path) -> int:
    s = p.read_text(encoding="utf-8")
    if "@router.exception_handler" not in s and "# router.exception_handler(" not in s:
        return 0

    s2 = s

    # 1) decorator -> komentarz (APIRouter nie ma exception_handler)
    s2 = re.sub(
        r"(?m)^\s*@router\.exception_handler\((.*?)\)\s*$",
        r"# @# router.exception_handler(\1)  # disabled: APIRouter has no exception_handler",
        s2,
    )

    # 2) wywołania -> komentarz
    # (robimy prosto: każdy "# router.exception_handler(" w linii zamieniamy na "# # router.exception_handler(")
    s2 = s2.replace("# router.exception_handler(", "# # router.exception_handler(")

    if s2 == s:
        return 0

    b = backup(p)
    p.write_text(s2, encoding="utf-8")
    print(f"[OK] disabled router.exception_handler in {p} (backup: {b})")
    return 1

def main() -> int:
    if not ROOT.exists():
        print(f"[ERR] missing root: {ROOT}", file=sys.stderr)
        return 2

    changed = 0
    for p in ROOT.rglob("*.py"):
        if should_skip(p):
            continue
        changed += patch_file(p)

    print(f"[DONE] files patched: {changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
