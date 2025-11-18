#!/bin/bash

# Start script for API server and frontend
# Both services run in the background and persist after terminal closes

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Starting Outage Looking Glass Services...${NC}"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if services are already running
API_PID=$(pgrep -f "python.*api_server.py")
FRONTEND_PID=$(pgrep -f "vite.*frontend")

if [ ! -z "$API_PID" ]; then
    echo -e "${YELLOW}API server is already running (PID: $API_PID)${NC}"
    echo "Use ./stop_services.sh to stop it first if you want to restart."
else
    # Start API server
    echo -e "${GREEN}Starting API server...${NC}"
    source venv/bin/activate
    nohup python api_server.py > logs/api_server.log 2>&1 &
    API_PID=$!
    echo "API server started (PID: $API_PID)"
    echo "Logs: logs/api_server.log"
    deactivate
fi

echo ""

if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}Frontend is already running (PID: $FRONTEND_PID)${NC}"
    echo "Use ./stop_services.sh to stop it first if you want to restart."
else
    # Start frontend
    echo -e "${GREEN}Starting frontend...${NC}"
    cd frontend
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend started (PID: $FRONTEND_PID)"
    echo "Logs: logs/frontend.log"
    cd ..
fi

echo ""
echo -e "${BLUE}Services started successfully!${NC}"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:5173"
echo "  API:      http://localhost:5000"
echo ""
echo "To view logs:"
echo "  API:      tail -f logs/api_server.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "To stop services:"
echo "  ./stop_services.sh"
echo ""

# Save PIDs to file for easy stopping later
echo "$API_PID" > logs/api_server.pid
echo "$FRONTEND_PID" > logs/frontend.pid
