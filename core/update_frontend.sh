#!/bin/bash
################################################################################
# MORDZIX AI - UPDATE FRONTEND (LINUX ONLY)
# Rebuild Angular i restart backendu na serwerze OVH
################################################################################

set -e

echo ""
echo "═══════════════════════════════════════════════════════════"
echo " MORDZIX AI - ANGULAR FRONTEND UPDATE"
echo "═══════════════════════════════════════════════════════════"
echo ""

FRONTEND_DIR="/workspace/mrd/frontend"
DIST_DIR="$FRONTEND_DIR/dist/mordzix-ai"

# Sprawdź czy jesteśmy w odpowiednim katalogu
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "✗ BŁĄD: Katalog $FRONTEND_DIR nie istnieje!"
    exit 1
fi

cd "$FRONTEND_DIR"

# Sprawdź Node.js
echo "[1/4] Sprawdzanie Node.js..."
if ! command -v node &> /dev/null; then
    echo "✗ BŁĄD: Node.js nie zainstalowany!"
    echo "Uruchom: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "         sudo apt-get install -y nodejs"
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "  Node.js: $NODE_VERSION"
echo "  npm: $NPM_VERSION"

# Sprawdź czy node_modules istnieje
if [ ! -d "node_modules" ]; then
    echo "[2/4] Instalacja zależności..."
    npm install
else
    echo "[2/4] Zależności już zainstalowane"
fi

# Usuń stary build
if [ -d "dist" ]; then
    echo "[3/4] Usuwanie starego buildu..."
    rm -rf dist
fi

# Build production
echo "[3/4] Build Angular production..."
npm run build:prod

if [ $? -ne 0 ]; then
    echo "✗ BŁĄD: Build failed!"
    exit 1
fi

# Sprawdź czy build istnieje
if [ ! -f "$DIST_DIR/index.html" ]; then
    echo "✗ BŁĄD: Build nie utworzył index.html!"
    exit 1
fi

BUILD_SIZE=$(du -sh "$DIST_DIR" | cut -f1)
echo "  Build size: $BUILD_SIZE"
echo "  ✓ Build success!"

# Restart backendu
echo "[4/4] Restart backendu..."
sudo supervisorctl restart mordzix

sleep 2

# Sprawdź status
STATUS=$(sudo supervisorctl status mordzix | awk '{print $2}')
echo "  Status: $STATUS"

if [ "$STATUS" = "RUNNING" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo " ✓ UPDATE ZAKOŃCZONY!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Aplikacja dostępna na: https://mordxixai.xyz/"
    echo ""
    echo "Sprawdź logi:"
    echo "  sudo supervisorctl tail -f mordzix"
    echo ""
else
    echo ""
    echo "✗ UWAGA: Backend nie działa poprawnie!"
    echo "Sprawdź logi: sudo supervisorctl tail mordzix"
    exit 1
fi
