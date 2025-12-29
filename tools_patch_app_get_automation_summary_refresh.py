#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import re
import time
import py_compile

TARGET = Path("/root/mrd/app.py")

FUNC_BLOCK = r'''
def get_automation_summary(refresh: bool = False, **_kwargs) -> dict:
    """
    Funkcja kompatybilności dla narzędzi/bootstrapa, które wywołują:
        get_automation_summary(refresh=...)
    `refresh` i dodatkowe kwargs są akceptowane, żeby nie wywalać startu.
    """
    import os
    info = {
        "refresh": bool(refresh),
        "loaded_env_file": os.getenv("ENV_FILE") or os.getenv("DOTENV_PATH") or None,
        "has_auth_token": bool(os.getenv("AUTH_TOKEN")),
        "host": os.getenv("HOST", None),
        "port": int(os.getenv("PORT", "8000")),
        "pythonpath": os.getenv("PYTHONPATH", None),
        "venv": os.getenv("VIRTUAL_ENV", None),
    }

    app_obj = globals().get("app")
    try:
        routes = getattr(app_obj, "routes", None)
        info["routes_count"] = len(routes) if routes is not None else None
    except Exception:
        info["routes_count"] = None

    return info
'''.strip("\n") + "\n"

def backup_text(src: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    b = TARGET.with_suffix(TARGET.suffix + f".bak.get_automation_summary_refresh.{ts}")
    b.write_text(src, encoding="utf-8")
    return b

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Brak pliku: {TARGET}")

    src0 = TARGET.read_text(encoding="utf-8")
    b = backup_text(src0)

    # 1) Jeśli funkcja istnieje — podmieniamy cały jej blok.
    pat = re.compile(
        r"(?ms)^\s*def\s+get_automation_summary\s*\([^)]*\)\s*->\s*dict\s*:\s*\n"
        r"(?:[ \t].*\n)*?(?=^\S|\Z)"
    )
    m = pat.search(src0)

    if m:
        src1 = src0[:m.start()] + FUNC_BLOCK + src0[m.end():]
        if src1 == src0:
            print("Brak zmian (wygląda na to, że funkcja już jest kompatybilna).")
            print(f"Backup: {b}")
            return
        TARGET.write_text(src1, encoding="utf-8")
        py_compile.compile(str(TARGET), doraise=True)
        print(f"OK: podmieniono get_automation_summary w: {TARGET}")
        print(f"Backup: {b}")
        return

    # 2) Jeśli nie ma funkcji — dopisujemy na końcu pliku.
    src1 = src0.rstrip() + "\n\n" + FUNC_BLOCK
    TARGET.write_text(src1, encoding="utf-8")
    py_compile.compile(str(TARGET), doraise=True)
    print(f"OK: dopisano get_automation_summary do: {TARGET}")
    print(f"Backup: {b}")

if __name__ == "__main__":
    main()
