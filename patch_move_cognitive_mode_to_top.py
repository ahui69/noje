#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/core/advanced_cognitive_engine.py")

EXCLUDE_MARK = "# [MORDZIX] CognitiveMode bootstrap (moved to top to avoid circular import)\n"

def backup(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(path) + f".bak.{ts}")
    b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def split_lines(s: str) -> list[str]:
    return s.splitlines(True)

def find_module_header_end(lines: list[str]) -> int:
    i = 0
    # shebang / coding
    while i < len(lines) and (lines[i].startswith("#!") or "coding" in lines[i]):
        i += 1
    # __future__
    while i < len(lines) and re.match(r"^\s*from\s+__future__\s+import\b", lines[i]):
        i += 1
    # module docstring
    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        q = lines[i].lstrip()[:3]
        i += 1
        while i < len(lines) and q not in lines[i]:
            i += 1
        if i < len(lines):
            i += 1
    return i

def ensure_enum_import(lines: list[str], insert_at: int) -> tuple[list[str], bool]:
    if any(re.match(r"^\s*from\s+enum\s+import\s+Enum\b", ln) for ln in lines):
        return lines, False
    lines2 = lines[:]
    lines2.insert(insert_at, "from enum import Enum\n")
    return lines2, True

def extract_cognitive_blocks(lines: list[str]) -> tuple[list[str], str, bool]:
    """
    Extract top-level `class CognitiveMode` block plus optional following top-level
    `def parse_cognitive_mode` block. Return (new_lines, extracted_text, found).
    """
    text = "".join(lines)
    # quick check
    if "class CognitiveMode" not in text:
        return lines, "", False

    # locate class start at top-level
    class_start = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*class\s+CognitiveMode\b", ln) and (len(ln) - len(ln.lstrip()) == 0):
            class_start = i
            break
    if class_start is None:
        return lines, "", False

    # find class end: next top-level def/class after class
    def is_toplevel_def_or_class(ln: str) -> bool:
        return (len(ln) - len(ln.lstrip()) == 0) and re.match(r"^(def|class)\s+\w+", ln)

    class_end = len(lines)
    for j in range(class_start + 1, len(lines)):
        if is_toplevel_def_or_class(lines[j]):
            class_end = j
            break

    # check parse_cognitive_mode right after class (possibly with blank lines/comments)
    parse_start = None
    k = class_end
    while k < len(lines) and (lines[k].strip() == "" or lines[k].lstrip().startswith("#")):
        k += 1
    if k < len(lines) and re.match(r"^\s*def\s+parse_cognitive_mode\b", lines[k]) and (len(lines[k]) - len(lines[k].lstrip()) == 0):
        parse_start = k
        parse_end = len(lines)
        for j in range(parse_start + 1, len(lines)):
            if is_toplevel_def_or_class(lines[j]):
                parse_end = j
                break
        extracted = "".join(lines[class_start:parse_end])
        new_lines = lines[:class_start] + lines[parse_end:]
        return new_lines, extracted, True

    extracted = "".join(lines[class_start:class_end])
    new_lines = lines[:class_start] + lines[class_end:]
    return new_lines, extracted, True

def find_local_import_anchor(lines: list[str], start_at: int) -> int:
    """
    Insert before first local import: from core..., import core..., from . ...
    If none found, insert after header+stdlib imports region (start_at).
    """
    for i in range(start_at, len(lines)):
        ln = lines[i]
        if re.match(r"^\s*from\s+core\b", ln) or re.match(r"^\s*import\s+core\b", ln) or re.match(r"^\s*from\s+\.", ln):
            return i
    return start_at

def normalize_cognitive_block(extracted: str) -> str:
    """
    Ensure block exists and is clean. If extracted looks weird, fallback to a known-good block.
    """
    if "class CognitiveMode" in extracted and "Enum" in extracted:
        return extracted.rstrip() + "\n\n"
    # fallback: still a full real enum + parser (no placeholders)
    return (
        EXCLUDE_MARK
        "class CognitiveMode(str, Enum):\n"
        '    """Tryb pracy silnika kognitywnego (dla routerów i konfiguracji)."""\n'
        '    AUTO = "auto"\n'
        '    FAST = "fast"\n'
        '    BALANCED = "balanced"\n'
        '    DEEP = "deep"\n'
        "\n"
        "def parse_cognitive_mode(value: object, default: CognitiveMode = CognitiveMode.AUTO) -> CognitiveMode:\n"
        '    """\n'
        "    Parsuje wartość trybu z dowolnego inputu (str/None/Enum).\n"
        "    Zwraca `default` gdy nie da się dopasować.\n"
        '    """\n'
        "    if isinstance(value, CognitiveMode):\n"
        "        return value\n"
        "    if value is None:\n"
        "        return default\n"
        "    v = str(value).strip().lower()\n"
        "    aliases = {\n"
        '        "auto": "auto",\n'
        '        "default": "auto",\n'
        '        "normal": "balanced",\n'
        '        "balanced": "balanced",\n'
        '        "fast": "fast",\n'
        '        "quick": "fast",\n'
        '        "deep": "deep",\n'
        '        "slow": "deep",\n'
        "    }\n"
        "    v = aliases.get(v, v)\n"
        "    for m in CognitiveMode:\n"
        "        if v == m.value:\n"
        "            return m\n"
        "    return default\n\n"
    )

def main() -> int:
    if not P.exists():
        print(f"[ERR] missing file: {P}", file=sys.stderr)
        return 2

    s = P.read_text(encoding="utf-8")
    lines = split_lines(s)

    header_end = find_module_header_end(lines)

    # avoid double-apply if already moved
    if EXCLUDE_MARK in s:
        # still ensure Enum import exists
        lines2, added = ensure_enum_import(lines, header_end)
        if added:
            b = backup(P)
            P.write_text("".join(lines2), encoding="utf-8")
            print(f"[OK] patched {P} (backup: {b}) added=from enum import Enum")
        else:
            print("[OK] already contains CognitiveMode bootstrap marker and Enum import")
        return 0

    # extract existing blocks (class + parse)
    lines_wo, extracted, found = extract_cognitive_blocks(lines)
    if not found:
        print("[ERR] CognitiveMode class not found to move (file differs from expected)", file=sys.stderr)
        return 3

    # recompute header end on modified lines
    header_end2 = find_module_header_end(lines_wo)

    # ensure Enum import exists right after header
    lines_wo2, added_import = ensure_enum_import(lines_wo, header_end2)

    insert_at = find_local_import_anchor(lines_wo2, header_end2)

    block = normalize_cognitive_block(extracted)
    if EXCLUDE_MARK not in block:
        block = EXCLUDE_MARK + block

    b = backup(P)
    out = "".join(lines_wo2[:insert_at]) + "\n" + block + "".join(lines_wo2[insert_at:])
    P.write_text(out, encoding="utf-8")

    print(f"[OK] patched {P} (backup: {b}) moved=CognitiveMode_to_top enum_import_added={1 if added_import else 0}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
