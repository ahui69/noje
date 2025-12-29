#!/bin/bash
set -euo pipefail

# Kolory ANSI
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🚀 MORDZIX AI SYSTEM STARTUP                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Universal start script for Mordzix AI (Linux/macOS)
# - Creates / activates venv
# - Installs requirements.txt
# - Runs scripts/check_requirements.py to report missing deps
# - Loads .env into environment if present
# - Kills previous uvicorn processes using known uvicorn/gunicorn/python patterns
# - Starts uvicorn app:app

TOTAL_STEPS=10
FRONTEND_DIR="frontend"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$FRONTEND_DIR/dist/mordzix-ai"
VENV_DIR="$ROOT_DIR/.venv"
REQ_FILE="$ROOT_DIR/requirements.txt"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            🔥 MORDZIX AI - STARTER 🔥                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "Root: $ROOT_DIR"

# ═══════════════════════════════════════════════════════════════════
# 1. SPRAWDŹ PYTHON
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/${TOTAL_STEPS}] Sprawdzam Python...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 nie znaleziony!${NC}"
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    else
        echo -e "${RED}Zainstaluj python3/python3-venv ręcznie i uruchom ponownie.${NC}"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION}${NC}"

# ═══════════════════════════════════════════════════════════════════
# 2. ZABIJ STARE SESJE
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/${TOTAL_STEPS}] Zabijam stare sesje...${NC}"

if command -v lsof >/dev/null 2>&1; then
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        kill -9 "$(lsof -t -i:8080)" 2>/dev/null || true
        sleep 1
    fi
elif command -v fuser >/dev/null 2>&1; then
    fuser -k 8080/tcp 2>/dev/null || true
fi

pkill -9 -f "uvicorn.*app:app" 2>/dev/null || true
pkill -9 -f "python.*app.py" 2>/dev/null || true

echo -e "${GREEN}✅ Stare sesje zakończone${NC}"

# ═══════════════════════════════════════════════════════════════════
# 3. SPRAWDŹ NODE.JS ORAZ NPM
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/${TOTAL_STEPS}] Sprawdzam Node.js oraz npm...${NC}"

if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Node.js lub npm nie znaleziony!${NC}"
    if command -v apt-get >/dev/null 2>&1; then
        echo -e "${YELLOW}Instaluję Node.js 18.x poprzez NodeSource...${NC}"
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo -e "${RED}Zainstaluj Node.js (>=18) i spróbuj ponownie.${NC}"
        exit 1
    fi
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo -e "${GREEN}✅ Node ${NODE_VERSION}, npm ${NPM_VERSION}${NC}"

# ═══════════════════════════════════════════════════════════════════
# 4. FRONTEND – BUILD ANGULAR
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[4/${TOTAL_STEPS}] Przygotowuję build frontendu...${NC}"

if [ "${SKIP_FRONTEND_BUILD:-0}" = "1" ]; then
    echo -e "${YELLOW}⚠️  SKIP_FRONTEND_BUILD=1 – pomijam budowę frontendu.${NC}"
    if [ ! -f "$DIST_DIR/index.html" ]; then
        echo -e "${RED}❌ Brak skompilowanego frontendu w $DIST_DIR/index.html!${NC}"
        exit 1
    fi
else
    if [ "${SKIP_FRONTEND_INSTALL:-0}" = "1" ] && [ -d "$FRONTEND_DIR/node_modules" ]; then
        echo -e "${BLUE}ℹ️  SKIP_FRONTEND_INSTALL=1 – pomijam \`npm ci\`.${NC}"
    else
        echo -e "${YELLOW}📦 Instaluję zależności frontendu (npm ci)...${NC}"
        (cd "$FRONTEND_DIR" && npm ci --no-audit)
    fi
    echo -e "${YELLOW}⚙️  Buduję Angular (production)...${NC}"
    (cd "$FRONTEND_DIR" && npm run build:prod)
fi

# Upewnij się, że pliki istnieją
if [ ! -f "$DIST_DIR/index.html" ]; then
    echo -e "${RED}❌ Kompilacja frontendu nie wygenerowała $DIST_DIR/index.html!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend gotowy (${DIST_DIR})${NC}"

# ═══════════════════════════════════════════════════════════════════
# 5. ŚRODOWISKO PYTHON
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[5/${TOTAL_STEPS}] Tworzę środowisko wirtualne...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip wheel

echo -e "${YELLOW}[6/${TOTAL_STEPS}] Instaluję zależności (requirements.txt)...${NC}"
python -m pip install -r requirements.txt

echo -e "${YELLOW}Instaluję polski model językowy spaCy...${NC}"
python -m spacy download pl_core_news_sm || echo -e "${YELLOW}⚠️  Model polski już zainstalowany lub błąd instalacji${NC}"

echo -e "${YELLOW}Instaluję angielski model językowy spaCy...${NC}"
python -m spacy download en_core_web_sm || echo -e "${YELLOW}⚠️  Model angielski już zainstalowany lub błąd instalacji${NC}"

# Opcjonalne zależności systemowe (OCR/ffprobe)
if command -v apt-get >/dev/null 2>&1; then
    echo -e "${YELLOW}Sprawdzam OCR/ffmpeg (opcjonalnie)...${NC}"
    sudo apt-get update -y >/dev/null 2>&1 || true
    sudo apt-get install -y tesseract-ocr ffmpeg >/dev/null 2>&1 || true
fi
echo -e "${GREEN}✅ Środowisko Python gotowe${NC}"

# ═══════════════════════════════════════════════════════════════════
# 6. UTWÓRZ KATALOGI (tylko jeśli nie istnieją)
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[7/${TOTAL_STEPS}] Tworzę katalogi...${NC}"
export WORKSPACE_DIR="${WORKSPACE_DIR:-/root}"
export APP_DIR="$(pwd)"
export DATA_ROOT="${DATA_ROOT:-/root/mrd}"
export WORKSPACE="${WORKSPACE:-$DATA_ROOT}"
export UPLOAD_DIR="${UPLOAD_DIR:-$DATA_ROOT/out/uploads}"
mkdir -p "$DATA_ROOT" "$UPLOAD_DIR" "$DATA_ROOT/out/images/_selftest" "$DATA_ROOT/data/mem" logs
echo -e "${GREEN}✅ Katalogi utworzone${NC}"

# ═══════════════════════════════════════════════════════════════════
# 7. SPRAWDŹ .ENV
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[8/${TOTAL_STEPS}] Sprawdzam .env...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Brak .env – kontynuuję z wartościami domyślnymi.${NC}"
fi
set -a; [ -f .env ] && . ./.env; set +a
export AUTH_TOKEN="${AUTH_TOKEN:-ssjjMijaja6969}"
export MEM_DB="${MEM_DB:-$DATA_ROOT/mem.db}"
export UPLOAD_DIR
echo -e "${GREEN}✅ ENV przygotowane${NC}"

# ═══════════════════════════════════════════════════════════════════
# 8. INICJALIZUJ BAZĘ DANYCH (tylko jeśli nie istnieje)
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[9/${TOTAL_STEPS}] Sprawdzam bazę danych i tworzę brakujące tabele...${NC}"
python <<PYEOF
import os, sqlite3, time
db_path = os.environ.get('MEM_DB') or 'mem.db'
os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Memory tables (STM/LTM + meta)
c.execute("""CREATE TABLE IF NOT EXISTS memory(
  id TEXT PRIMARY KEY, user TEXT, role TEXT, content TEXT, ts REAL
)""")
c.execute("""CREATE TABLE IF NOT EXISTS memory_long(
  id TEXT PRIMARY KEY, user TEXT, summary TEXT, details TEXT, ts REAL
)""")
c.execute("""CREATE TABLE IF NOT EXISTS meta_memory(
  id TEXT PRIMARY KEY, user TEXT, key TEXT, value TEXT, conf REAL, ts REAL
)""")

c.execute("""CREATE TABLE IF NOT EXISTS facts(
  id TEXT PRIMARY KEY, text TEXT, tags TEXT, conf REAL, created REAL, deleted INTEGER DEFAULT 0
)""")
try:
  c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(text, tags)")
except Exception:
  pass

c.execute("""CREATE TABLE IF NOT EXISTS mem_embed(
  id TEXT PRIMARY KEY, user TEXT, vec TEXT, ts REAL
)""")

c.execute("""CREATE TABLE IF NOT EXISTS docs(
  id TEXT PRIMARY KEY, url TEXT, title TEXT, text TEXT, source TEXT, fetched REAL
)""")
try:
  c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(title, text, url UNINDEXED)")
except Exception:
  pass

c.execute("""CREATE TABLE IF NOT EXISTS cache(
  key TEXT PRIMARY KEY, value TEXT, ts REAL
)""")

# Psyche state + episodes
c.execute("""CREATE TABLE IF NOT EXISTS psy_state(
  id INTEGER PRIMARY KEY CHECK(id=1),
  mood REAL, energy REAL, focus REAL, openness REAL, directness REAL,
  agreeableness REAL, conscientiousness REAL, neuroticism REAL,
  style TEXT, updated REAL
)""")
c.execute("""CREATE TABLE IF NOT EXISTS psy_episode(
  id TEXT PRIMARY KEY, user TEXT, kind TEXT, valence REAL, intensity REAL, tags TEXT, note TEXT, ts REAL
)""")

# Indexes
c.execute("CREATE INDEX IF NOT EXISTS idx_facts_deleted ON facts(deleted) WHERE deleted=0")
c.execute("CREATE INDEX IF NOT EXISTS idx_facts_created ON facts(created DESC)")
c.execute("CREATE INDEX IF NOT EXISTS idx_facts_tags ON facts(tags)")
c.execute("CREATE INDEX IF NOT EXISTS idx_memory_user_ts ON memory(user, ts DESC)")
c.execute("CREATE INDEX IF NOT EXISTS idx_memory_long_user_ts ON memory_long(user, ts DESC)")
c.execute("CREATE INDEX IF NOT EXISTS idx_cache_ts ON cache(ts)")
c.execute("CREATE INDEX IF NOT EXISTS idx_psy_episode_user_ts ON psy_episode(user, ts DESC)")
c.execute("CREATE INDEX IF NOT EXISTS idx_psy_episode_ts ON psy_episode(ts DESC)")

# Seed psyche row
row = c.execute("SELECT COUNT(*) FROM psy_state WHERE id=1").fetchone()
if (row or [0])[0] == 0:
  c.execute("INSERT INTO psy_state(id,mood,energy,focus,openness,directness,agreeableness,conscientiousness,neuroticism,style,updated) VALUES(1,0.0,0.6,0.6,0.55,0.62,0.55,0.63,0.44,'rzeczowy',?)", (time.time(),))

conn.commit(); conn.close()
print(f"✅ DB OK: {db_path}")
PYEOF

# ═══════════════════════════════════════════════════════════════════
# 9. SPRAWDŹ WYMAGANE PLIKI
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[10/${TOTAL_STEPS}] Sprawdzam pliki...${NC}"
MISSING_FILES=0

for file in app.py assistant_endpoint.py sw.js "$DIST_DIR/index.html"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Brakuje: $file${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo -e "${RED}❌ Brakuje $MISSING_FILES plików!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Wszystkie pliki na miejscu${NC}"

# ═══════════════════════════════════════════════════════════════════
# 10. URUCHOM APLIKACJĘ
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}▶ Uruchamiam Mordzix AI...${NC}"
echo ""

LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}' || echo "localhost")

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🚀 MORDZIX AI URUCHOMIONY! 🚀              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 URL:${NC}"
echo -e "   http://${LOCAL_IP}:8080"
echo -e "   http://localhost:8080"
echo ""
echo -e "${BLUE}📚 API Docs:${NC} http://${LOCAL_IP}:8080/docs"
echo -e "${BLUE}🔧 Zatrzymaj:${NC} Ctrl+C"
echo ""

echo -e "${BLUE}🤖 Automatyzacja (fast path + tools):${NC}"
MORDZIX_SUPPRESS_STARTUP_LOGS=1 python <<'PYEOF'
import os
import json

os.environ['MORDZIX_SUPPRESS_STARTUP_LOGS'] = '1'

from app import get_automation_summary  # noqa: E402

summary = get_automation_summary(refresh=True)
payload = {
  "fast_path_count": summary.get("fast_path", {}).get("count", 0),
  "tool_count": summary.get("tools", {}).get("count", 0),
  "manual_count": summary.get("manual", {}).get("count", 0),
  "automatic_total": summary.get("totals", {}).get("automatic", 0),
  "categories": summary.get("tools", {}).get("categories", [])
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
PYEOF
echo ""

while true; do
    MEM_DB="$MEM_DB" UPLOAD_DIR="$UPLOAD_DIR" AUTH_TOKEN="$AUTH_TOKEN" \
    python -m uvicorn app:app --host 0.0.0.0 --port 8080 --log-level info 2>&1 | tee -a logs/mordzix.log
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}Aplikacja zakończona normalnie.${NC}"
        break
    else
        echo -e "${RED}Crash! Exit code: $EXIT_CODE${NC}"
        echo -e "${YELLOW}Restart za 3 sekundy...${NC}"
        sleep 3
    fi
done