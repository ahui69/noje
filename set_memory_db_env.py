#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ENV_PATH = Path("/root/mrd/.env")
TARGET = "/root/mrd/mem.db"

KEYS = [
    "MEMORY_DB_PATH",
    "MEM_DB",
    "DB_PATH",
]

def upsert_env(path: Path, kv: dict[str, str]) -> None:
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    out: list[str] = []
    seen = set()

    for line in lines:
        raw = line
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            out.append(raw)
            continue

        k, v = s.split("=", 1)
        k = k.strip()
        if k in kv:
            out.append(f"{k}={kv[k]}")
            seen.add(k)
        else:
            out.append(raw)

    for k, v in kv.items():
        if k not in seen:
            out.append(f"{k}={v}")

    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

def main() -> int:
    kv = {k: TARGET for k in KEYS}
    upsert_env(ENV_PATH, kv)
    print(f"[OK] Updated {ENV_PATH} -> {TARGET}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
