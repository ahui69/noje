#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys

def main() -> int:
    p = Path("/root/mrd/openai_compat.py")
    s = p.read_text(encoding="utf-8")

    # Naprawa: boundary_hard rozjechane na 2 linie przez wstrzyknięty newline w stringu
    pat = re.compile(
        r'(?m)^(?P<indent>[ \t]*)boundary_hard\s*=\s*"\.\!\?\s*$\n^(?P=indent)"\s*$'
    )

    if not pat.search(s):
        print("Nie znalazłem rozjechanego boundary_hard do naprawy.", file=sys.stderr)
        return 2

    s2 = pat.sub(r'\g<indent>boundary_hard = ".!?\\n"', s, count=1)
    p.write_text(s2, encoding="utf-8")
    print("OK: boundary_hard naprawione w openai_compat.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
