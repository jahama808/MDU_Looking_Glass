#!/bin/bash
# Start Flask Backend Server

echo "Starting Flask API Server..."
echo "Database: output/outages.db"
echo ""

# Activate virtual environment
source venv/bin/activate

# Run Flask server
python api_server.py
