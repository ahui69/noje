#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/core/advanced_cognitive_engine.py")

EXCLUDE_PARTS = (
    "/.venv/",
    "/venv/",
    "/node_modules/",
    "/__pycache__/",
    "/.git/",
)

def backup(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(path) + f".bak.{ts}")
    b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def find_insertion_index(lines: list[str]) -> int:
    """
    Wstawka po:
    - shebang/coding
    - __future__
    - module docstring
    """
    i = 0
    while i < len(lines) and (lines[i].startswith("#!") or "coding" in lines[i]):
        i += 1

    while i < len(lines) and re.match(r"^\s*from\s+__future__\s+import\b", lines[i]):
        i += 1

    # docstring
    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        q = lines[i].lstrip()[:3]
        i += 1
        while i < len(lines) and q not in lines[i]:
            i += 1
        if i < len(lines):
            i += 1

    # po docstringu zwykle idą importy; wstawimy po blokach importów jeśli istnieją
    j = i
    while j < len(lines):
        ln = lines[j]
        if re.match(r"^\s*(import|from)\s+\w", ln) or ln.strip() == "":
            j += 1
            continue
        break
    return j

def ensure_enum_import(lines: list[str]) -> tuple[list[str], int]:
    text = "".join(lines)
    if re.search(r"(?m)^\s*from\s+enum\s+import\s+Enum\s*$", text):
        return lines, 0

    # znaleźć pierwszy sensowny import (nie future), i tam wstawić
    insert_at = 0
    while insert_at < len(lines) and (lines[insert_at].startswith("#!") or "coding" in lines[insert_at]):
        insert_at += 1
    while insert_at < len(lines) and re.match(r"^\s*from\s+__future__\s+import\b", lines[insert_at]):
        insert_at += 1

    # pominąć docstring
    if insert_at < len(lines) and lines[insert_at].lstrip().startswith(('"""', "'''")):
        q = lines[insert_at].lstrip()[:3]
        insert_at += 1
        while insert_at < len(lines) and q not in lines[insert_at]:
            insert_at += 1
        if insert_at < len(lines):
            insert_at += 1

    # jeśli od razu są importy, wstaw po pierwszym “import/from” (żeby nie rozwalać stylu)
    j = insert_at
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    if j < len(lines) and re.match(r"^\s*(import|from)\s+\w", lines[j]):
        # wstawiamy po nim
        lines.insert(j + 1, "from enum import Enum\n")
        return lines, 1

    # inaczej wstawiamy w tym miejscu
    lines.insert(insert_at, "from enum import Enum\n")
    return lines, 1

def main() -> int:
    if not P.exists():
        print(f"[ERR] missing file: {P}", file=sys.stderr)
        return 2

    s = P.read_text(encoding="utf-8")

    if re.search(r"(?m)^\s*class\s+CognitiveMode\s*\(", s):
        print("[OK] CognitiveMode already present")
        return 0

    lines = s.splitlines(True)

    lines, added_import = ensure_enum_import(lines)

    block = (
        "\n"
        "class CognitiveMode(str, Enum):\n"
        '    """Tryb pracy silnika/endpointu (stabilny kontrakt importów)."""\n'
        "    AUTO = \"auto\"\n"
        "    STANDARD = \"standard\"\n"
        "    ADVANCED = \"advanced\"\n"
        "    ANALYTICAL = \"analytical\"\n"
        "    CREATIVE = \"creative\"\n"
        "    FAST = \"fast\"\n"
        "\n"
        "DEFAULT_COGNITIVE_MODE = CognitiveMode.AUTO\n"
        "\n"
        "def parse_cognitive_mode(value: object, default: CognitiveMode = DEFAULT_COGNITIVE_MODE) -> CognitiveMode:\n"
        '    """\n'
        "    Bezpieczna normalizacja trybu z requestów/env/JSON.\n"
        "    Akceptuje: None/bool/str/Enum.\n"
        "    - None -> default\n"
        "    - True -> ADVANCED\n"
        "    - False -> STANDARD\n"
        "    - str -> dopasowanie po nazwie lub wartości (case-insensitive)\n"
        "    - CognitiveMode -> as-is\n"
        '    """\n'
        "    if value is None:\n"
        "        return default\n"
        "    if isinstance(value, CognitiveMode):\n"
        "        return value\n"
        "    if isinstance(value, bool):\n"
        "        return CognitiveMode.ADVANCED if value else CognitiveMode.STANDARD\n"
        "    if isinstance(value, (int, float)):\n"
        "        return CognitiveMode.ADVANCED if value else CognitiveMode.STANDARD\n"
        "    if isinstance(value, str):\n"
        "        v = value.strip().lower()\n"
        "        if not v:\n"
        "            return default\n"
        "        # po wartości\n"
        "        for m in CognitiveMode:\n"
        "            if v == m.value:\n"
        "                return m\n"
        "        # po nazwie\n"
        "        for m in CognitiveMode:\n"
        "            if v == m.name.lower():\n"
        "                return m\n"
        "        # aliasy\n"
        "        aliases = {\n"
        "            \"default\": CognitiveMode.STANDARD,\n"
        "            \"normal\": CognitiveMode.STANDARD,\n"
        "            \"std\": CognitiveMode.STANDARD,\n"
        "            \"pro\": CognitiveMode.ADVANCED,\n"
        "            \"adv\": CognitiveMode.ADVANCED,\n"
        "            \"analysis\": CognitiveMode.ANALYTICAL,\n"
        "            \"analytic\": CognitiveMode.ANALYTICAL,\n"
        "            \"creative\": CognitiveMode.CREATIVE,\n"
        "            \"fast\": CognitiveMode.FAST,\n"
        "            \"auto\": CognitiveMode.AUTO,\n"
        "        }\n"
        "        return aliases.get(v, default)\n"
        "    return default\n"
        "\n"
    )

    insert_at = find_insertion_index(lines)

    b = backup(P)
    out = "".join(lines[:insert_at]) + block + "".join(lines[insert_at:])
    P.write_text(out, encoding="utf-8")

    print(f"[OK] patched {P} (backup: {b}) added=CognitiveMode parse_cognitive_mode import_added={added_import}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
