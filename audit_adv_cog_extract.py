#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable
import re
import sys

ROOT = Path("/root/mrd")
TARGET = Path("/root/mrd/core/advanced_cognitive_engine.py")

EXCLUDE_PARTS = (
    "/.venv/",
    "/venv/",
    "/node_modules/",
    "/__pycache__/",
    "/.git/",
)

IMPORT_RE = re.compile(r"^\s*from\s+core\.advanced_cognitive_engine\s+import\s+(.+?)\s*$")
IMPORT_RE2 = re.compile(r"^\s*import\s+core\.advanced_cognitive_engine\b")
NAME_DEF_RE = re.compile(r"^\s*(class|def)\s+([A-Za-z_]\w*)\b")
FUTURE_RE = re.compile(r"^\s*from\s+__future__\s+import\b")

@dataclass
class ImportUse:
    file: Path
    lineno: int
    raw: str
    names: List[str]

@dataclass
class DefHit:
    file: Path
    lineno: int
    kind: str
    name: str
    line: str

def should_skip(p: Path) -> bool:
    sp = str(p)
    return any(part in sp for part in EXCLUDE_PARTS)

def iter_py_files() -> Iterable[Path]:
    for p in ROOT.rglob("*.py"):
        if should_skip(p):
            continue
        yield p

def parse_import_names(chunk: str) -> List[str]:
    # handles: a, b as c, (a, b)
    s = chunk.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    parts = [x.strip() for x in s.split(",") if x.strip()]
    out = []
    for p in parts:
        # strip "as alias"
        out.append(p.split(" as ", 1)[0].strip())
    return out

def scan_imports() -> List[ImportUse]:
    uses: List[ImportUse] = []
    for p in iter_py_files():
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, ln in enumerate(lines, start=1):
            m = IMPORT_RE.match(ln)
            if m:
                names = parse_import_names(m.group(1))
                uses.append(ImportUse(p, i, ln, names))
            elif IMPORT_RE2.match(ln):
                uses.append(ImportUse(p, i, ln, []))
    return uses

def scan_defs(names: Tuple[str, ...]) -> List[DefHit]:
    hits: List[DefHit] = []
    for p in iter_py_files():
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, ln in enumerate(lines, start=1):
            m = NAME_DEF_RE.match(ln)
            if not m:
                continue
            kind, name = m.group(1), m.group(2)
            if name in names:
                hits.append(DefHit(p, i, kind, name, ln.rstrip()))
    return hits

def check_future_position(p: Path) -> Tuple[bool, str]:
    """
    True if OK, else False with message.
    Rule: __future__ must appear after (optional) shebang/coding, after docstring start-end, but before any other code/import.
    """
    try:
        lines = p.read_text(encoding="utf-8").splitlines(True)
    except Exception as e:
        return False, f"cannot read: {e}"

    i = 0
    # shebang/coding
    while i < len(lines) and (lines[i].startswith("#!") or "coding" in lines[i]):
        i += 1

    # docstring
    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        q = lines[i].lstrip()[:3]
        i += 1
        while i < len(lines) and q not in lines[i]:
            i += 1
        if i < len(lines):
            i += 1

    # now any __future__ must be in a contiguous block here, before other imports/code
    saw_future = False
    j = i
    while j < len(lines):
        ln = lines[j]
        if FUTURE_RE.match(ln):
            saw_future = True
            j += 1
            continue
        # allow blank/comment between future lines
        if saw_future and (ln.strip() == "" or ln.lstrip().startswith("#")):
            j += 1
            continue
        break

    # if future exists later after j -> bad
    for k in range(j, len(lines)):
        if FUTURE_RE.match(lines[k]):
            return False, f"__future__ appears late at line {k+1}"
    return True, "ok"

def main() -> int:
    if not ROOT.exists():
        print(f"[ERR] missing root: {ROOT}", file=sys.stderr)
        return 2

    uses = scan_imports()
    print("======================================================================")
    print("IMPORTS OF core.advanced_cognitive_engine")
    print("======================================================================")
    if not uses:
        print("(none)")
    else:
        for u in uses:
            if u.names:
                print(f"{u.file}:{u.lineno}: imports {', '.join(u.names)}")
            else:
                print(f"{u.file}:{u.lineno}: {u.raw.strip()}")

    # names that usually break builds
    key_names = (
        "CognitiveMode",
        "parse_cognitive_mode",
        "CognitiveRequest",
        "CognitiveResult",
        "AdvancedCognitiveEngine",
        "AdvancedCognitiveResult",
        "get_engine",
        "get_advanced_cognitive_engine",
    )

    hits = scan_defs(key_names)
    by_name: Dict[str, List[DefHit]] = {}
    for h in hits:
        by_name.setdefault(h.name, []).append(h)

    print("\n======================================================================")
    print("DUPLICATE DEFINITIONS (high-risk for import errors)")
    print("======================================================================")
    any_dup = False
    for name in key_names:
        hs = by_name.get(name, [])
        if len(hs) > 1:
            any_dup = True
            print(f"\n{name}: {len(hs)} hits")
            for h in hs:
                print(f"  - {h.file}:{h.lineno}: {h.kind} {h.name}  |  {h.line}")
    if not any_dup:
        print("(no duplicates among key symbols)")

    print("\n======================================================================")
    print("CHECK __future__ POSITION IN core/advanced_cognitive_engine.py")
    print("======================================================================")
    if TARGET.exists():
        ok, msg = check_future_position(TARGET)
        print(f"{TARGET}: {'OK' if ok else 'BAD'} — {msg}")
    else:
        print(f"(missing) {TARGET}")

    print("\n======================================================================")
    print("SUMMARY")
    print("======================================================================")
    print(f"import sites: {len(uses)}")
    print(f"def hits: {len(hits)}")
    print("If duplicates exist in advanced_cognitive_engine.py, façade+impl split will fix it cleanly.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
