#!/bin/bash

# IxOS Port Utilization Plotter - Docker Compose Stop Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}IxOS Port Utilization Plotter${NC}"
echo -e "${BLUE}Docker Compose Stop${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Parse command line arguments
REMOVE_VOLUMES=false
if [ "$1" == "--volumes" ] || [ "$1" == "-v" ]; then
    REMOVE_VOLUMES=true
    echo -e "${YELLOW}⚠️  WARNING: This will remove all data volumes!${NC}"
    echo -e "${YELLOW}   All historical data will be permanently deleted.${NC}"
    echo ""
    echo -e "   Press Enter to continue or Ctrl+C to cancel"
    read -r
fi

echo -e "${BLUE}🛑 Stopping services...${NC}"
$COMPOSE_CMD down

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${YELLOW}🗑️  Removing volumes...${NC}"
    $COMPOSE_CMD down -v
    echo -e "${GREEN}✅ Volumes removed${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Stack stopped successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ "$REMOVE_VOLUMES" = false ]; then
    echo -e "${BLUE}💡 Note:${NC} Data volumes are preserved."
    echo -e "   To remove all data, run: ${YELLOW}./stop.sh --volumes${NC}"
fi

echo ""

