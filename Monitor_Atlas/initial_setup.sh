#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

trap 'echo -e "\n'"$RED"'❌ Unhandled error. Exiting.'"$NC"'' ERR

FIXTURE_FILES=(fixtures/*.json)
TOTAL_FIXTURES=${#FIXTURE_FILES[@]}
CURRENT_FIXTURE=0

echo -e "${BLUE}🚀 ---- Running migrations ---- 🚀${NC}"
if ! output=$(python manage.py makemigrations 2>&1); then
    echo -e "${RED}❌ makemigrations failed:${NC}\n$output"
    exit 1
fi
if ! output=$(python manage.py migrate 2>&1); then
    echo -e "${RED}❌ migrate failed:${NC}\n$output"
    exit 1
fi
echo -e "${GREEN}✨ Migrations completed.${NC}"

echo ""
echo -e "${CYAN}📦 ---- Loading fixtures ---- 📦${NC}"

for fixture in "${FIXTURE_FILES[@]}"; do
    CURRENT_FIXTURE=$((CURRENT_FIXTURE + 1))
    PERCENTAGE=$((CURRENT_FIXTURE * 100 / TOTAL_FIXTURES))
    FILLED=$((PERCENTAGE * 50 / 100))
    EMPTY=$((50 - FILLED))
    PROGRESS_BAR=$(printf "%${FILLED}s" | tr ' ' '#')
    EMPTY_BAR=$(printf "%${EMPTY}s" | tr ' ' ' ')

    printf "\033[2K\r${GREEN}[%s%s]${NC} %3d%% (%d/%d) ${CYAN}%s${NC}" \
           "$PROGRESS_BAR" "$EMPTY_BAR" "$PERCENTAGE" "$CURRENT_FIXTURE" "$TOTAL_FIXTURES" "$(basename "$fixture")"

    # Ejecutar y capturar salida: sólo mostrar si falla
    if ! output=$(python manage.py loaddata "$fixture" 2>&1); then
        echo ""  # saltar a nueva línea antes del error
        echo -e "${RED}❌ Failed loading fixture: $(basename "$fixture")${NC}"
        echo -e "${RED}${output}${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}✅ All fixtures loaded successfully.${NC}"

echo ""
echo -e "${CYAN}🔄 ---- Synchronizing data with ChirpStack ---- 🔄${NC}"
if output=$(python manage.py sync_chirpstack 2>&1); then
    echo -e "$output"
    echo -e "${GREEN}✨ ChirpStack synchronization completed.${NC}"
else
    echo -e "$output"
    echo -e "${RED}❌ sync_chirpstack failed.${NC}"
    exit 1
fi

exec "$@"
