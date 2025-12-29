#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

ROOT = Path("/root/mrd")

EXCLUDE_PARTS = ("/.venv/", "/venv/", "/node_modules/", "/__pycache__/", "/.git/")

def is_excluded(p: Path) -> bool:
    sp = str(p)
    return any(x in sp for x in EXCLUDE_PARTS)

def backup(p: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(p) + f".bak.{ts}")
    b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def patch_fstring_webctx_newlines(s: str) -> tuple[str, int]:
    """
    Fixuje źródło typu:
      'Kontekst:\' + chr(10) + web_ctx
      "[Źródła]\" + chr(10) + web_ctx
    na:
      'Kontekst:' + chr(10) + web_ctx
      "[Źródła]" + chr(10) + web_ctx

    Dzięki temu znika backslash w ekspresji f-stringa.
    """
    before = s
    # '...\' + chr(10) + web_ctx  lub  "...\" + chr(10) + web_ctx
    pat = re.compile(r"(['\"])([^'\"]*?)\\n\1(\s*\+\s*web_ctx\b)")
    s = pat.sub(r"\1\2\1 + chr(10)\3", s)
    return s, (0 if s == before else 1)

def patch_router_exception_handler_usage(s: str) -> tuple[str, int]:
    """
    Wyłącza tylko dekoratory/metody exception_handler na zmiennych kończących się na 'router'.
    Np:
# @# router.exception_handler(...)  # disabled: APIRouter has no exception_handler
      # @tts_# router.exception_handler(...)  # disabled: APIRouter has no exception_handler
      # tts_# router.exception_handler(...)
    """
    before = s

    # Dekorator: @<name># router.exception_handler(...)
    s = re.sub(
        r"(?m)^(\s*)@([A-Za-z_][A-Za-z0-9_]*router)\.exception_handler\((.*?)\)\s*$",
        r"\1# @\2.exception_handler(\3)  # disabled: APIRouter has no exception_handler",
        s,
    )

    # Wywołanie: <name># router.exception_handler(
    s = re.sub(
        r"(?m)^(\s*)([A-Za-z_][A-Za-z0-9_]*router)\.exception_handler\(",
        r"\1# \2.exception_handler(",
        s,
    )

    return s, (0 if s == before else 1)

def patch_file(p: Path) -> bool:
    try:
        s = p.read_text(encoding="utf-8")
    except Exception:
        return False

    changed = 0

    s2, c1 = patch_fstring_webctx_newlines(s)
    changed += c1

    s3, c2 = patch_router_exception_handler_usage(s2)
    changed += c2

    if changed:
        b = backup(p)
        p.write_text(s3, encoding="utf-8")
        print(f"[OK] patched {p} (backup: {b})")
        return True

    return False

def main() -> int:
    if not ROOT.exists():
        print(f"[ERR] Brak katalogu {ROOT}", file=sys.stderr)
        return 2

    patched = 0
    for p in ROOT.rglob("*.py"):
        if is_excluded(p):
            continue
        if patch_file(p):
            patched += 1

    print(f"[DONE] files patched: {patched}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
