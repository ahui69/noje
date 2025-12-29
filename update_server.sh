#!/bin/bash
#═══════════════════════════════════════════════════════════════════════
# MORDZIX AI - AKTUALIZACJA Z GITHUB
#═══════════════════════════════════════════════════════════════════════
# Użycie: ./update_server.sh
#═══════════════════════════════════════════════════════════════════════

set -e

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║         🔄 AKTUALIZACJA MORDZIX AI Z GITHUB 🔄                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Sprawdź czy jesteś w katalogu projektu
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Błąd: Musisz być w katalogu projektu!${NC}"
    echo "Przejdź do: cd /workspace/EHH/EHH"
    exit 1
fi

echo -e "${YELLOW}⏸️  Zatrzymywanie aplikacji...${NC}"
sudo systemctl stop mordzix-ai

echo -e "${GREEN}📥 Pobieranie zmian z GitHub...${NC}"
git fetch origin

echo -e "${GREEN}🔄 Aktualizacja kodu...${NC}"
git pull origin cursor/review-and-debug-first-code-aa54

echo -e "${GREEN}📦 Sprawdzanie dependencies...${NC}"
source .venv/bin/activate
pip install -r requirements.txt --upgrade

echo -e "${GREEN}🔄 Restart aplikacji...${NC}"
sudo systemctl start mordzix-ai

echo ""
echo "⏳ Czekam 3 sekundy..."
sleep 3

echo -e "${GREEN}✅ Sprawdzanie statusu...${NC}"
sudo systemctl status mordzix-ai --no-pager -l

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║              ✅ AKTUALIZACJA ZAKOŃCZONA! ✅                       ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}🎉 Mordzix AI zaktualizowany do najnowszej wersji!${NC}"
echo ""
echo "📊 Sprawdź logi: journalctl -u mordzix-ai -f"
echo "🌐 Otwórz: http://$(curl -s ifconfig.me 2>/dev/null || echo 'IP_SERWERA')"
echo ""
