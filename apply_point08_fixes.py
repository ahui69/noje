#!/usr/bin/env python3
"""
Apply Point 08 fixes:
1. Add auth middleware to app.py (before first @app.middleware)
2. Change AUTH_TOKEN to fail-fast in assistant_endpoint.py (repo root)
Usage: python3 apply_point08_fixes.py --repo /root/mrd
"""

import sys
import os
import argparse

# Parse args: allow --repo to specify repository root (required for remote runs)
parser = argparse.ArgumentParser(description="Apply Point 08 fixes to MRD repo")
parser.add_argument(
    "--repo",
    help="Path to repository root (e.g. /root/mrd). If omitted, uses current working directory.",
)
args = parser.parse_args()

# Repo root (use provided or current working dir)
REPO_ROOT = os.path.abspath(args.repo) if args.repo else os.path.abspath(os.getcwd())

# Paths (built from repo root)
APP_PY = os.path.join(REPO_ROOT, "app.py")
ASSISTANT_PY = os.path.join(REPO_ROOT, "assistant_endpoint.py")


def fix_auth_token():
    """Fix AUTH_TOKEN fail-fast in assistant_endpoint.py"""
    print("[*] Fixing AUTH_TOKEN in assistant_endpoint.py...")

    with open(ASSISTANT_PY, "r") as f:
        content = f.read()

    # Find and replace line 43
    old = 'AUTH_TOKEN = os.getenv("AUTH_TOKEN", "ssjjMijaja6969")'
    new = """# Fail-fast on startup - no default value
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
if not AUTH_TOKEN or not AUTH_TOKEN.strip():
    raise RuntimeError(
        "CRITICAL: AUTH_TOKEN environment variable not set or empty. "
        "Cannot start application without valid authentication token. "
        "Set: export AUTH_TOKEN='your-secure-token-here'"
    )"""

    if old in content:
        content = content.replace(old, new)
        with open(ASSISTANT_PY, "w") as f:
            f.write(content)
        print(f"✅ AUTH_TOKEN fail-fast check added to assistant_endpoint.py")
        return True
    else:
        print(f"❌ Could not find original AUTH_TOKEN line")
        return False


def fix_app_middleware():
    """Add auth middleware to app.py before other middleware"""
    print(f"[*] Adding auth middleware to {APP_PY}...")

    with open(APP_PY, "r") as f:
        lines = f.readlines()

    # Check if auth_middleware already exists
    for line in lines:
        if "def auth_middleware" in line:
            print("ℹ️ auth_middleware already exists")
            return True

    # Find first @app.middleware("http") decorator
    first_middleware_idx = None
    for i, line in enumerate(lines):
        if '@app.middleware("http")' in line:
            first_middleware_idx = i
            break

    if first_middleware_idx is None:
        print("❌ Could not find any @app.middleware decorator")
        return False

    # Add imports if needed (check for JSONResponse import)
    content_str = "".join(lines)

    # Check for Request import
    if (
        "from fastapi import Request" not in content_str
        and "from fastapi import" in content_str
        and ", Request" not in content_str
    ):
        # Find the line with "from fastapi import" and add Request if needed
        for i, line in enumerate(lines):
            if "from fastapi import" in line and "Request" not in line:
                # Add Request to this import line
                # Example: "from fastapi import APIRouter, HTTPException" -> add Request
                lines[i] = line.rstrip("\n").rstrip() + ", Request\n"
                print("✅ Request import added to fastapi imports")
                break
    elif "from fastapi import Request" not in content_str:
        # No fastapi import line at all, add it after os/sys imports
        for i, line in enumerate(lines):
            if "import os" in line or "import sys" in line:
                lines.insert(i + 1, "from fastapi import Request\n")
                print("✅ New Request import added")
                break

    # Check for JSONResponse import
    if "from fastapi.responses import JSONResponse" not in content_str:
        # Find import section - look for last 'from fastapi' line
        last_fastapi_import = None
        for i, line in enumerate(lines):
            if line.startswith("from fastapi"):
                last_fastapi_import = i

        if last_fastapi_import is not None:
            lines.insert(
                last_fastapi_import + 1, "from fastapi.responses import JSONResponse\n"
            )
        else:
            # Insert after os import if no fastapi imports found
            for i, line in enumerate(lines):
                if "import os" in line:
                    lines.insert(i + 1, "from fastapi.responses import JSONResponse\n")
                    break

    # Auth middleware code - CORRECT VERSION
    auth_middleware = '''# ═══════════════════════════════════════════════════════════════════
# AUTH MIDDLEWARE - Authorization required for all /api/* routes.
# Frontend SPA deep-linking: allow GET/HEAD for non-/api/* (public), protect all /api/* with Bearer.
# If you want frontend protected as well, change policy accordingly (see report).
# ═══════════════════════════════════════════════════════════════════

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Policy implemented by script:
    - All paths under /api/ require Authorization: Bearer <token>.
    - Exact public paths (/, /health, /status, etc.) and static prefixes are allowed.
    - Non-/api/ GET and HEAD requests are allowed to support SPA deep-linking.
    - Other non-GET non-HEAD requests to non-/api/ paths require auth.
    """

    path = request.url.path
    method = request.method.upper()

    # Exact public paths (no children)
    exact_public_paths = [
        "/",
        "/health",
        "/status",
        "/openapi.json",
        "/favicon.ico",
        "/manifest.webmanifest",
        "/sw.js",
        "/ngsw-worker.js",
    ]

    public_prefixes = ["/static", "/assets"]

    # Allow exact public paths
    if path in exact_public_paths:
        return await call_next(request)

    # Allow static asset prefixes (with trailing "/")
    if any(path.startswith(p + "/") for p in public_prefixes):
        return await call_next(request)

    # If this is an API path -> require Bearer
    if path.startswith("/api/") or path == "/api":
        auth_header = request.headers.get("Authorization", "").strip()
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header", "error": "unauthorized"})
        token = auth_header[7:]
        expected_token = os.getenv("AUTH_TOKEN")
        if token != expected_token:
            return JSONResponse(status_code=403, content={"detail": "Invalid token", "error": "forbidden"})
        return await call_next(request)

    # Non-API paths: allow GET/HEAD for SPA deep-linking
    if method in ("GET", "HEAD"):
        return await call_next(request)

    # Other methods on non-API paths require auth (POST/PUT/DELETE)
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header", "error": "unauthorized"})
    token = auth_header[7:]
    expected_token = os.getenv("AUTH_TOKEN")
    if token != expected_token:
        return JSONResponse(status_code=403, content={"detail": "Invalid token", "error": "forbidden"})
    return await call_next(request)

'''

    # Insert auth middleware BEFORE first middleware
    lines.insert(first_middleware_idx, auth_middleware)

    with open(APP_PY, "w") as f:
        f.writelines(lines)

    print(f"✅ Auth middleware added before existing middleware")
    return True


if __name__ == "__main__":
    success = True
    success = fix_auth_token() and success
    success = fix_app_middleware() and success

    if success:
        print("\n✅ Point 08 fixes applied successfully")
        sys.exit(0)
    else:
        print("\n❌ Some fixes failed")
        sys.exit(1)
