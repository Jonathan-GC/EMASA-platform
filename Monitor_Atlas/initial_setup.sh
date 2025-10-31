#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

FIXTURE_FILES=(fixtures/*.json)
TOTAL_FIXTURES=${#FIXTURE_FILES[@]}
CURRENT_FIXTURE=0

echo -e "${BLUE}🚀 ---- Running migrations ---- 🚀${NC}"
python manage.py makemigrations
python manage.py migrate
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
    
    python manage.py loaddata "$fixture" > /dev/null 2>&1
done

echo ""
echo -e "${GREEN}✅ All fixtures loaded successfully.${NC}"

echo ""
echo -e "${CYAN}🔄 ---- Synchronizing data with ChirpStack ---- 🔄${NC}"
python manage.py sync_chirpstack
echo -e "${GREEN}✨ ChirpStack synchronization completed.${NC}"

exec "$@"
