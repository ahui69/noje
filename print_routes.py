#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import sys

CANDIDATES = [
    ("app", "app"),
    ("core.app", "app"),
]

def load_app():
    last_err = None
    for mod_name, var_name in CANDIDATES:
        try:
            mod = importlib.import_module(mod_name)
            app = getattr(mod, var_name, None)
            if app is not None:
                return app, f"{mod_name}:{var_name}"
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Could not import FastAPI app from candidates {CANDIDATES}. last_err={last_err!r}")

def main() -> int:
    app, src = load_app()
    routes = []
    for r in getattr(app, "routes", []):
        methods = sorted(getattr(r, "methods", []) or [])
        path = getattr(r, "path", "")
        name = getattr(r, "name", "")
        if path:
            routes.append((path, ",".join(methods), name))
    routes.sort(key=lambda x: x[0])

    print(f"[OK] Loaded app from {src}")
    print(f"[OK] routes={len(routes)}")
    for path, methods, name in routes:
        print(f"{methods:12s} {path:40s} {name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
