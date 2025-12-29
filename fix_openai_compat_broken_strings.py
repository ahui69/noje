#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys

def _count_unescaped_double_quotes(s: str) -> int:
    # liczy tylko nie-escaped "
    cnt = 0
    esc = False
    for ch in s:
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            cnt += 1
    return cnt

def main() -> int:
    p = Path("/root/mrd/openai_compat.py")
    s = p.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    out: list[str] = []
    i = 0
    changed = False

    re_hard = re.compile(r'^(?P<indent>[ \t]*)boundary_hard\s*=')
    re_soft = re.compile(r'^(?P<indent>[ \t]*)boundary_soft\s*=')

    while i < len(lines):
        line = lines[i]

        m = re_hard.match(line)
        if m:
            indent = m.group("indent")
            # jeżeli linia wygląda na rozjechaną (otwarty " bez zamknięcia), to zgarniamy blok aż się " domknie
            block = line
            q = _count_unescaped_double_quotes(block)
            j = i
            while (q % 2) == 1 and (j + 1) < len(lines):
                j += 1
                block += lines[j]
                q = _count_unescaped_double_quotes(block)

            # podmień cały blok na poprawny literal (bezpiecznie single-quote)
            out.append(f"{indent}boundary_hard = '.!?\\n'\n")
            changed = True
            i = j + 1
            continue

        m = re_soft.match(line)
        if m:
            indent = m.group("indent")
            block = line
            q = _count_unescaped_double_quotes(block)
            j = i
            while (q % 2) == 1 and (j + 1) < len(lines):
                j += 1
                block += lines[j]
                q = _count_unescaped_double_quotes(block)

            # to jest string z “miękkimi” granicami; w single-quote łatwo zapisać również "
            out.append(f"{indent}boundary_soft = ',;:)]\"\\''\n")
            changed = True
            i = j + 1
            continue

        out.append(line)
        i += 1

    if not changed:
        print("Nie wykryłem do naprawy boundary_hard/boundary_soft jako rozwalonego stringa. Pokaż wycinek 118-140.", file=sys.stderr)
        return 2

    backup = Path(str(p) + ".bak.fixstrings")
    backup.write_text(s, encoding="utf-8")
    p.write_text("".join(out), encoding="utf-8")
    print("OK: naprawione boundary_hard/boundary_soft w openai_compat.py")
    print("Backup:", str(backup))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
