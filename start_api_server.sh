#!/bin/bash
# Start API Server with Environment Variables
#
# Usage:
#   1. Copy .env.example to .env
#   2. Edit .env and add your ANTHROPIC_API_KEY
#   3. Run: ./start_api_server.sh

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found. AI analysis will not work without ANTHROPIC_API_KEY."
    echo "Copy .env.example to .env and add your API key."
fi

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY is not set!"
    echo "AI-powered outage analysis will be unavailable."
    echo ""
    echo "To enable AI analysis:"
    echo "  1. Get an API key from: https://console.anthropic.com/settings/keys"
    echo "  2. Copy .env.example to .env"
    echo "  3. Add your API key to .env"
    echo "  4. Run this script again"
    echo ""
    read -p "Continue without AI analysis? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ ANTHROPIC_API_KEY is configured"
fi

# Kill existing API server processes
echo "Stopping existing API server processes..."
pkill -f "python.*api_server.py"
sleep 2

# Create logs directory if it doesn't exist
mkdir -p logs

# Start API server
echo "Starting API server..."
nohup ./venv/bin/python3 api_server.py > logs/api_server.log 2>&1 &

sleep 3

# Check if server started
if ps aux | grep -v grep | grep "api_server.py" > /dev/null; then
    echo "✓ API server started successfully"
    echo "  Log file: logs/api_server.log"
    echo "  API available at: http://localhost:5000"
else
    echo "✗ Failed to start API server"
    echo "  Check logs/api_server.log for details"
    exit 1
fi
