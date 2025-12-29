#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/core/writing.py")

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
    lines = s.splitlines(True)

    out: list[str] = []
    changed = 0

    # Match lines like:
    # lines.append(f"Hashtagi: #{re.sub(r'\W+', '', cat_tag)} #okazja ...")
    pat = re.compile(
        r"""^(\s*)lines\.append\(\s*f(["'])Hashtagi:\s*#\{re\.sub\(\s*r(["'])\\W\+\3\s*,\s*(["'])\4\s*,\s*cat_tag\s*\)\}\s*(.*?)\2\s*\)\s*$""",
        re.M,
    )

    for ln in lines:
        m = pat.match(ln)
        if not m:
            out.append(ln)
            continue

        indent = m.group(1)
        quote = m.group(2)  # " or '
        rest = m.group(6)   # everything after the } inside the string, up to closing quote

        # Replace with safe two-liner; regex literal is outside f-string (allowed).
        out.append(f"{indent}cat_tag_clean = re.sub(r\"\\\\W+\", \"\", cat_tag)\n")
        out.append(f"{indent}lines.append(f{quote}Hashtagi: #{{cat_tag_clean}}{rest}{quote})\n")
        changed += 1

    if not changed:
        print("[OK] nothing to patch (pattern not found)")
        return 0

    b = backup(P)
    P.write_text("".join(out), encoding="utf-8")
    print(f"[OK] patched {P} (backup: {b}) lines_fixed={changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
