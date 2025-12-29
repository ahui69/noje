#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys

EXIT_PATTERNS = [
    re.compile(r'^\s*sys\.exit\(\s*1\s*\)\s*$', re.M),
    re.compile(r'^\s*raise\s+SystemExit\(\s*1\s*\)\s*$', re.M),
    re.compile(r'^\s*os\._exit\(\s*1\s*\)\s*$', re.M),
]

def ensure_import(s: str, module: str) -> str:
    # bardzo prosty, bezpieczny inserter importów
    imp_re = re.compile(rf'^\s*import\s+{re.escape(module)}\b', re.M)
    from_re = re.compile(r'^\s*from\s+__future__\s+import\b', re.M)
    if imp_re.search(s):
        return s
    lines = s.splitlines(True)
    insert_at = 0
    # po shebang/encoding
    while insert_at < len(lines) and (lines[insert_at].startswith("#!") or "coding" in lines[insert_at]):
        insert_at += 1
    # po future importach
    while insert_at < len(lines) and from_re.match(lines[insert_at]):
        insert_at += 1
    # po module docstring jeśli jest na górze
    if insert_at < len(lines) and lines[insert_at].lstrip().startswith(('"""', "'''")):
        q = lines[insert_at].lstrip()[:3]
        insert_at += 1
        while insert_at < len(lines) and q not in lines[insert_at]:
            insert_at += 1
        if insert_at < len(lines):
            insert_at += 1

    lines.insert(insert_at, f"import {module}\n")
    return "".join(lines)

def wrap_exit_line(line: str) -> str:
    indent = re.match(r'^(\s*)', line).group(1)
    return (
        f"{indent}if os.getenv('MRD_STRICT_ROUTERS', '0') == '1':\n"
        f"{indent}    {line.lstrip()}"
        f"{indent}else:\n"
        f"{indent}    print('[WARN] Routers failed, but MRD_STRICT_ROUTERS!=1 so continuing.')\n"
    )

def main() -> int:
    p = Path("/root/mrd/app.py")
    if not p.exists():
        print("Brak /root/mrd/app.py (uruchamiasz uvicorn app:app, więc to powinno istnieć).", file=sys.stderr)
        return 2

    s = p.read_text(encoding="utf-8")

    # upewnij się, że mamy os (i sys jeśli używasz sys.exit)
    s2 = ensure_import(s, "os")
    s2 = ensure_import(s2, "sys")

    lines = s2.splitlines(True)
    changed = False
    out = []
    for line in lines:
        replaced = False
        for pat in EXIT_PATTERNS:
            if pat.match(line):
                out.append(wrap_exit_line(line))
                changed = True
                replaced = True
                break
        if not replaced:
            out.append(line)

    if not changed:
        print("Nie znalazłem sys.exit(1)/SystemExit(1)/os._exit(1) do owinięcia w app.py.", file=sys.stderr)
        return 3

    backup = Path(str(p) + ".bak.nonfatal_" )
    backup.write_text(s, encoding="utf-8")
    p.write_text("".join(out), encoding="utf-8")
    print("OK: app.py spatchowane (exit(1) tylko gdy MRD_STRICT_ROUTERS=1).")
    print("Backup:", str(backup))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
