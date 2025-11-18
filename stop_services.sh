#!/bin/bash

# Stop script for API server and frontend

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping Outage Looking Glass Services...${NC}"
echo ""

# Find and kill API server
API_PID=$(pgrep -f "python.*api_server.py")
if [ ! -z "$API_PID" ]; then
    echo -e "${RED}Stopping API server (PID: $API_PID)...${NC}"
    kill $API_PID
    sleep 1
    # Force kill if still running
    if ps -p $API_PID > /dev/null 2>&1; then
        kill -9 $API_PID
        echo "API server forcefully terminated"
    else
        echo "API server stopped"
    fi
else
    echo "API server not running"
fi

echo ""

# Find and kill frontend (Vite dev server)
FRONTEND_PID=$(pgrep -f "vite.*frontend")
if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${RED}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
    kill $FRONTEND_PID
    sleep 1
    # Force kill if still running
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill -9 $FRONTEND_PID
        echo "Frontend forcefully terminated"
    else
        echo "Frontend stopped"
    fi
else
    echo "Frontend not running"
fi

# Also kill any Node processes related to the project
NODE_PIDS=$(pgrep -f "node.*vite")
if [ ! -z "$NODE_PIDS" ]; then
    echo ""
    echo -e "${RED}Stopping additional Node/Vite processes...${NC}"
    echo "$NODE_PIDS" | xargs kill 2>/dev/null
fi

echo ""
echo -e "${GREEN}All services stopped${NC}"

# Clean up PID files
rm -f logs/api_server.pid logs/frontend.pid 2>/dev/null
