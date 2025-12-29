#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/deploy.py")

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

    needle = 'DEPLOY_CMD.replace("`", "\\\\`").replace("$", "\\\\$")'
    changed = 0
    out: list[str] = []

    for ln in lines:
        if needle in ln:
            indent = re.match(r"^(\s*)", ln).group(1)

            # Wstaw precompute przed f.write(...)
            out.append(f'{indent}escaped_cmd = DEPLOY_CMD.replace("`", r"\\`").replace("$", r"\\$")\n')

            # Zamień wyrażenie w f-stringu na {escaped_cmd}
            ln2 = ln.replace(needle, "escaped_cmd")

            out.append(ln2)
            changed += 1
        else:
            out.append(ln)

    if changed == 0:
        print("[OK] nothing to patch (pattern not found)")
        return 0

    b = backup(P)
    P.write_text("".join(out), encoding="utf-8")
    print(f"[OK] patched {P} (backup: {b}) fixes={changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
