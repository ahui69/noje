#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
FRONTEND_DIR="$ROOT_DIR/frontend"
PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"
LOG_DIR="$ROOT_DIR/logs"
ENV_FILE="$ROOT_DIR/.env"

mkdir -p "$LOG_DIR"

info() { printf "\033[0;36m[INFO]\033[0m %s\n" "$*"; }
success() { printf "\033[0;32m[SUCCESS]\033[0m %s\n" "$*"; }
error() { printf "\033[0;31m[ERROR]\033[0m %s\n" "$*"; }

info "ROOT: $ROOT_DIR"

if [ -f "$ENV_FILE" ]; then
  info "Ładuję zmienne z $ENV_FILE"
  set -a
  source "$ENV_FILE"
  set +a
else
  info "Brak pliku .env – używam zmiennych środowiskowych bieżącej sesji"
fi

if [ ! -d "$VENV_DIR" ]; then
  info "Tworzę wirtualne środowisko Python (.venv)"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

info "Instaluję zależności backendu (requirements.txt)"
pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt"

if [ "${SKIP_FRONTEND:-0}" != "1" ]; then
  export VITE_API_BASE="${VITE_API_BASE:-http://$HOST:$PORT}"
  info "Buduję frontend z bazowym API=$VITE_API_BASE"
  info "Instaluję zależności frontendu (npm ci)"
  (cd "$FRONTEND_DIR" && npm ci --no-audit)

  info "Buduję frontend (npm run build)"
  (cd "$FRONTEND_DIR" && npm run build)
else
  info "Pominięto build frontendu (SKIP_FRONTEND=1)"
fi

FRONT_DIST="$FRONTEND_DIR/dist"
if [ ! -f "$FRONT_DIST/index.html" ]; then
  error "Brak zbudowanego frontendu w $FRONT_DIST – usuń SKIP_FRONTEND lub uruchom npm run build"
  exit 1
fi

if command -v lsof >/dev/null 2>&1; then
  if lsof -Pi :"$PORT" -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    info "Zabijam procesy nasłuchujące na porcie $PORT"
    kill -9 $(lsof -t -i:"$PORT") || true
  fi
elif command -v fuser >/dev/null 2>&1; then
  fuser -k "$PORT"/tcp 2>/dev/null || true
fi

export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"

info "Startuję FastAPI na http://$HOST:$PORT"
exec "$VENV_DIR/bin/python" -m uvicorn app:app --host "$HOST" --port "$PORT" --log-level info
