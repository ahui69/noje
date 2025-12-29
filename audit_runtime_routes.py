#!/usr/bin/env python3
import sys

sys.path.insert(0, "/root/mrd")

from core.app import app

print("=== FASTAPI ROUTES RUNTIME DUMP ===\n")

total = 0
auth_routes = 0
routes_list = []

for route in app.routes:
    if not hasattr(route, "path"):
        continue
    if (
        route.path.startswith("/openapi")
        or route.path.startswith("/docs")
        or route.path.startswith("/redoc")
    ):
        continue
    if route.path == "/static":
        continue

    methods = getattr(route, "methods", set()) or set()
    methods_str = ",".join(sorted(methods)) if methods else "?"
    endpoint = getattr(route, "endpoint", None)

    module = "?"
    func = "?"
    if endpoint:
        module = getattr(endpoint, "__module__", "?")
        func = getattr(endpoint, "__name__", "?")

    has_auth = False
    if hasattr(route, "dependencies"):
        deps = route.dependencies or []
        for dep in deps:
            if hasattr(dep, "dependency"):
                dn = getattr(dep.dependency, "__name__", "")
                if "verify" in dn.lower() or "auth" in dn.lower():
                    has_auth = True
                    break

    if has_auth:
        auth_routes += 1

    total += 1
    routes_list.append((methods_str, route.path, module, func, has_auth))

for idx, (methods, path, module, func, has_auth) in enumerate(routes_list, 1):
    auth_marker = "AUTH" if has_auth else "OPEN"
    print(f"{idx:3d}. {methods:12} {path:40} {module}:{func} [{auth_marker}]")

print("\n=== SUMMARY ===")
print(f"Total routes: {total}")
print(f"Auth-protected: {auth_routes}")
print(f"Public: {total - auth_routes}")
pct = 100 * (total - auth_routes) / total if total else 0
print(f"Percent public: {pct:.1f}%")
