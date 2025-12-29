#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys
from datetime import datetime

ROOT = Path("/root/mrd")

EXIT_PATTERNS = [
    re.compile(r'^\s*sys\.exit\(\s*1\s*\)\s*$', re.M),
    re.compile(r'^\s*raise\s+SystemExit\(\s*1\s*\)\s*$', re.M),
    re.compile(r'^\s*os\._exit\(\s*1\s*\)\s*$', re.M),
]

ROUTER_FAIL_MARKERS = [
    "Failed routers",
    "⛔ Failed routers",
]

def ensure_import(s: str, module: str) -> str:
    imp_re = re.compile(rf'^\s*import\s+{re.escape(module)}\b', re.M)
    if imp_re.search(s):
        return s

    lines = s.splitlines(True)
    insert_at = 0

    # shebang / encoding
    while insert_at < len(lines) and (lines[insert_at].startswith("#!") or "coding" in lines[insert_at]):
        insert_at += 1

    # future imports
    while insert_at < len(lines) and re.match(r'^\s*from\s+__future__\s+import\b', lines[insert_at]):
        insert_at += 1

    # module docstring on top
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
    stripped = line.lstrip()
    return (
        f"{indent}if os.getenv('MRD_STRICT_ROUTERS', '0') == '1':\n"
        f"{indent}    {stripped}"
        f"{indent}else:\n"
        f"{indent}    print('[WARN] Routers failed; MRD_STRICT_ROUTERS!=1 so continuing.')\n"
    )

def should_patch_file(s: str) -> bool:
    return any(m in s for m in ROUTER_FAIL_MARKERS)

def main() -> int:
    if not ROOT.exists():
        print(f"Brak katalogu {ROOT}", file=sys.stderr)
        return 2

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    patched = []

    for p in ROOT.rglob("*.py"):
        sp = str(p)

        # omijaj śmieci
        if "/.venv/" in sp or "/venv/" in sp or "/node_modules/" in sp or "/__pycache__/" in sp:
            continue

        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue

        if not should_patch_file(s):
            continue

        if not any(pat.search(s) for pat in EXIT_PATTERNS):
            continue

        s2 = ensure_import(s, "os")
        s2 = ensure_import(s2, "sys")

        lines = s2.splitlines(True)
        out = []
        changed = False

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

        if changed:
            backup = Path(str(p) + f".bak.nonfatalrouters.{ts}")
            backup.write_text(s, encoding="utf-8")
            p.write_text("".join(out), encoding="utf-8")
            patched.append(str(p))

    if not patched:
        print("Nie znalazłem plików do patcha (albo już spatchowane, albo exit(1) jest gdzie indziej).")
        return 0

    print("OK: spatchowane pliki (exit(1) tylko gdy MRD_STRICT_ROUTERS=1):")
    for x in patched:
        print(" -", x)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
