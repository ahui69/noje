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

    # jeśli już istnieje - nic nie rób
    if re.search(r"(?m)^\s*def\s+get_advanced_cognitive_engine\s*\(", s):
        print("[OK] get_advanced_cognitive_engine() already exists")
        return 0

    # wymagamy, żeby get_engine istniał (bo to jest singleton)
    m = re.search(r"(?m)^\s*def\s+get_engine\s*\(\s*\)\s*->\s*AdvancedCognitiveEngine\s*:\s*$", s)
    if not m:
        # fallback: spróbuj znaleźć def get_engine( w ogóle
        m2 = re.search(r"(?m)^\s*def\s+get_engine\s*\(", s)
        if not m2:
            print("[ERR] cannot find get_engine() in advanced_cognitive_engine.py", file=sys.stderr)
            return 3
        insert_at = m2.end()
    else:
        insert_at = m.end()

    # wstawiamy alias funkcji tuż po definicji get_engine (albo po linii def jeśli regex nie złapał typu)
    # znajdź koniec bloku get_engine przez pierwszą linię bez wcięcia (następny top-level def/class/if)
    lines = s.splitlines(True)
    # wyliczamy numer linii startowej get_engine
    start_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*def\s+get_engine\s*\(", ln):
            start_idx = i
            break
    if start_idx is None:
        print("[ERR] cannot locate get_engine() line index", file=sys.stderr)
        return 4

    # znajdź miejsce po bloku get_engine
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        ln = lines[j]
        if re.match(r"^(def|class)\s+\w+", ln) or re.match(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:", ln):
            end_idx = j
            break

    # jeśli między get_engine a następnym def jest już dużo kodu – i tak wstawiamy tuż po bloku
    insert = (
        "\n\n"
        "def get_advanced_cognitive_engine() -> AdvancedCognitiveEngine:\n"
        '    """\n'
        "    Zgodność wsteczna dla routerów/importów.\n"
        "    Zwraca singleton AdvancedCognitiveEngine (to samo co get_engine()).\n"
        '    """\n'
        "    return get_engine()\n"
        "\n"
    )

    # nie wstawiaj 2 razy jeśli ktoś dopisał inną nazwę niż regex wykrywa
    if "return get_engine()" in s and "def get_advanced_cognitive_engine" in s:
        print("[OK] looks already patched")
        return 0

    b = backup(P)
    out = "".join(lines[:end_idx]) + insert + "".join(lines[end_idx:])
    P.write_text(out, encoding="utf-8")
    print(f"[OK] patched {P} (backup: {b}) added=get_advanced_cognitive_engine")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
