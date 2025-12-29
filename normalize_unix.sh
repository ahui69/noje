#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"

export DEBIAN_FRONTEND=noninteractive
if ! command -v dos2unix >/dev/null 2>&1; then
  apt-get update -y >/dev/null
  apt-get install -y dos2unix >/dev/null
fi

# 1) .gitattributes żeby git nie wpychał CRLF
cat > "$ROOT/.gitattributes" <<'ATTR'
* text=auto eol=lf
*.sh text eol=lf
*.py text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.js text eol=lf
*.jsx text eol=lf
*.json text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.env text eol=lf
ATTR

git config core.autocrlf false 2>/dev/null || true
git config core.eol lf 2>/dev/null || true

# 2) Konwersja CRLF->LF + usunięcie UTF-8 BOM dla plików tekstowych
#    Omijamy ciężkie katalogi
prune_dirs=(
  -name .git -o -name node_modules -o -name dist -o -name build -o -name .venv -o -name venv
  -o -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache -o -name .idea -o -name .vscode
)

while IFS= read -r -d '' f; do
  # pomijanie binarek
  if ! grep -Iq . "$f" 2>/dev/null; then
    continue
  fi

  # CRLF -> LF tylko jeśli jest \r
  if LC_ALL=C grep -q $'\r' "$f" 2>/dev/null; then
    dos2unix -q "$f" || true
  fi

  # usuń UTF-8 BOM (EF BB BF)
  python3 - "$f" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
b = p.read_bytes()
if b.startswith(b"\xEF\xBB\xBF"):
    p.write_bytes(b[3:])
PY

done < <(
  find "$ROOT" \
    \( "${prune_dirs[@]}" \) -prune -o \
    -type f -print0
)

# 3) Ustaw +x na skryptach
find "$ROOT" \
  \( "${prune_dirs[@]}" \) -prune -o \
  -type f \( -name "*.sh" -o -name "*.bash" \) -print0 \
| xargs -0r chmod +x

echo "OK: CRLF->LF, BOM removed, +x for *.sh, .gitattributes set"
