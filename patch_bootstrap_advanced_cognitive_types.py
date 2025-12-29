#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/core/advanced_cognitive_engine.py")

MARK = "# [MORDZIX] ADV_COG bootstrap types (avoid circular imports)\n"

def backup(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(path) + f".bak.{ts}")
    b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def find_insert_at(lines: list[str]) -> int:
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

def main() -> int:
    if not P.exists():
        print(f"[ERR] missing file: {P}", file=sys.stderr)
        return 2

    s = P.read_text(encoding="utf-8")
    if MARK in s:
        print("[OK] bootstrap marker already present")
        return 0

    lines = s.splitlines(True)
    insert_at = find_insert_at(lines)

    block = (
        "\n"
        + MARK +
        "from enum import Enum\n"
        "from typing import Any, Dict, Optional\n"
        "\n"
        "from pydantic import BaseModel, Field\n"
        "\n"
        "class CognitiveMode(str, Enum):\n"
        '    """Tryb pracy silnika kognitywnego (wsteczna zgodność dla routerów)."""\n'
        '    AUTO = "auto"\n'
        '    FAST = "fast"\n'
        '    BALANCED = "balanced"\n'
        '    DEEP = "deep"\n'
        "\n"
        "def parse_cognitive_mode(value: object, default: CognitiveMode = CognitiveMode.AUTO) -> CognitiveMode:\n"
        '    """Parsuje tryb z inputu (str/None/Enum). Zwraca default gdy brak dopasowania."""\n'
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
        "    return default\n"
        "\n"
        "class CognitiveRequest(BaseModel):\n"
        '    """Minimalny kontrakt wejścia dla routerów Chat (Advanced)."""\n'
        "    prompt: str = Field(default=\"\")\n"
        "    mode: Optional[str] = Field(default=None, description=\"auto/fast/balanced/deep\")\n"
        "    context: Dict[str, Any] = Field(default_factory=dict)\n"
        "\n"
        "    def parsed_mode(self) -> CognitiveMode:\n"
        "        return parse_cognitive_mode(self.mode)\n"
        "\n"
        "class CognitiveResult(BaseModel):\n"
        '    """Minimalny kontrakt wyniku dla routerów Chat (Advanced)."""\n'
        "    ok: bool = Field(default=True)\n"
        "    mode: str = Field(default=\"auto\")\n"
        "    output: str = Field(default=\"\")\n"
        "    data: Dict[str, Any] = Field(default_factory=dict)\n"
        "    error: Optional[str] = Field(default=None)\n"
        "\n"
        "    def as_dict(self) -> Dict[str, Any]:\n"
        "        if hasattr(self, \"model_dump\"):\n"
        "            return self.model_dump()  # pydantic v2\n"
        "        return self.dict()  # pydantic v1\n"
        "\n"
    )

    b = backup(P)
    out = "".join(lines[:insert_at]) + block + "".join(lines[insert_at:])
    P.write_text(out, encoding="utf-8")
    print(f"[OK] patched {P} (backup: {b}) added=bootstrap_types")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
