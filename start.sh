#!/bin/bash

# IxOS Port Utilization Plotter - Docker Compose Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}IxOS Port Utilization Plotter${NC}"
echo -e "${BLUE}Docker Compose Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed!${NC}"
    echo -e "   Please install Docker from https://www.docker.com/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Error: Docker Compose is not installed!${NC}"
    echo -e "   Please install Docker Compose"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found!${NC}"
    echo -e "   Creating .env from env.example..."
    
    if [ -f env.example ]; then
        cp env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file and configure:${NC}"
        echo -e "   1. CHASSIS_LIST with your chassis IPs"
        echo -e "   2. INFLUXDB_TOKEN (change default token)"
        echo -e "   3. Admin passwords if needed"
        echo ""
        echo -e "   Press Enter to continue or Ctrl+C to exit and edit .env"
        read -r
    else
        echo -e "${RED}❌ Error: env.example not found!${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}Starting Docker Compose stack...${NC}"
echo ""

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Pull latest images
echo -e "${BLUE}📥 Pulling latest images...${NC}"
$COMPOSE_CMD pull

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
$COMPOSE_CMD up -d

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Stack started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Wait a moment for services to initialize
sleep 3

# Show service status
echo -e "${BLUE}📊 Service Status:${NC}"
$COMPOSE_CMD ps

echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"

# Load ports from .env or use defaults
if [ -f .env ]; then
    source .env
fi
GRAFANA_PORT=${GRAFANA_PORT:-3000}
INFLUXDB_PORT=${INFLUXDB_PORT:-8086}
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}

echo -e "   Grafana:    ${GREEN}http://localhost:${GRAFANA_PORT}${NC}"
echo -e "   InfluxDB:   ${GREEN}http://localhost:${INFLUXDB_PORT}${NC}"
echo -e "   Prometheus: ${GREEN}http://localhost:${PROMETHEUS_PORT}${NC}"
echo ""
echo -e "${BLUE}📝 Default Credentials:${NC}"
echo -e "   Username: ${GREEN}admin${NC}"
echo -e "   Password: ${GREEN}admin${NC}"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo -e "   View logs:        ${YELLOW}$COMPOSE_CMD logs -f${NC}"
echo -e "   Stop stack:       ${YELLOW}$COMPOSE_CMD down${NC}"
echo -e "   Restart stack:    ${YELLOW}$COMPOSE_CMD restart${NC}"
echo ""
echo -e "${BLUE}🔧 Run IxOS Poller (on host):${NC}"
echo -e "   Start poller:     ${YELLOW}python3 portInfoPoller.py${NC}"
echo -e "   Configure:        ${YELLOW}edit config.py${NC}"
echo ""
echo -e "${GREEN}Happy monitoring! 📊🚀${NC}"

