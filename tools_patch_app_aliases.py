#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import time
import py_compile

APP = Path("/root/mrd/app.py")

MARK = "# === AUTO-COMPAT (route aliases + kw compat) ==="

BLOCK = r'''
# === AUTO-COMPAT (route aliases + kw compat) ===
def _mrd__auto_alias_double_api_prefix(app):
    """
    Jeśli przez przypadek router ma prefix /api i app.include_router też ma prefix /api,
    FastAPI wystawia endpointy jako /api/api/...
    Ten blok dodaje aliasy /api/... dla istniejących /api/api/..., bez grzebania w routerach.
    """
    try:
        from fastapi.routing import APIRoute
    except Exception:
        return

    routes = [r for r in getattr(app, "routes", []) if isinstance(r, APIRoute)]
    existing = {(r.path, tuple(sorted(r.methods or []))) for r in routes}

    for r in routes:
        p = r.path or ""
        if p.startswith("/api/api/"):
            dst = "/api/" + p[len("/api/api/"):]
            key = (dst, tuple(sorted(r.methods or [])))
            if key in existing:
                continue
            try:
                app.add_api_route(
                    dst,
                    r.endpoint,
                    methods=list(r.methods or []),
                    include_in_schema=True,
                    name=(r.name + "_alias") if r.name else None,
                )
                existing.add(key)
            except Exception:
                continue


def _mrd__compat_get_automation_summary_refresh():
    """
    Start/diagnostyka woła get_automation_summary(refresh=...).
    Jeśli obecna implementacja nie przyjmuje `refresh`, to łapiemy to kompatybilnie.
    """
    try:
        import inspect
        g = globals().get("get_automation_summary")
        if g is None or not callable(g):
            return
        sig = None
        try:
            sig = inspect.signature(g)
        except Exception:
            sig = None

        if sig is not None and "refresh" in sig.parameters:
            return

        orig = g

        def get_automation_summary(*args, refresh=None, **kwargs):  # noqa: F811
            return orig(*args, **kwargs)

        globals()["get_automation_summary"] = get_automation_summary
    except Exception:
        return


try:
    _mrd__auto_alias_double_api_prefix(app)
except Exception:
    pass

_mrd__compat_get_automation_summary_refresh()
'''.strip("\n") + "\n"


def backup_text(src: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    b = APP.with_suffix(APP.suffix + f".bak.autocompat.{ts}")
    b.write_text(src, encoding="utf-8")
    return b


def main() -> None:
    if not APP.exists():
        raise SystemExit(f"Brak pliku: {APP}")

    src0 = APP.read_text(encoding="utf-8")
    b = backup_text(src0)

    if MARK in src0:
        print("Brak zmian (AUTO-COMPAT już jest w app.py).")
        print(f"Backup: {b}")
        return

    src1 = src0.rstrip("\n") + "\n\n" + BLOCK
    APP.write_text(src1, encoding="utf-8")

    py_compile.compile(str(APP), doraise=True)

    print("OK: dopięto AUTO-COMPAT do app.py")
    print(f"Backup: {b}")


if __name__ == "__main__":
    main()
