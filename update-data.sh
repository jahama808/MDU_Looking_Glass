#!/bin/bash

echo "MDU Performance Dashboard - Data Update"
echo "========================================"
echo ""

# Check for files
if [ $# -ne 2 ]; then
    echo "Usage: ./update-data.sh <connectivity-file> <discovery-file>"
    echo ""
    echo "Example:"
    echo "  ./update-data.sh networks_outage-2025-11-08.csv 'Eero Discovery Details - 2025-11-08 120000.csv'"
    exit 1
fi

WAN_FILE=$1
EERO_FILE=$2

# Validate files exist
if [ ! -f "$WAN_FILE" ]; then
    echo "Error: Connectivity file not found: $WAN_FILE"
    exit 1
fi

if [ ! -f "$EERO_FILE" ]; then
    echo "Error: Discovery file not found: $EERO_FILE"
    exit 1
fi

echo "Files found:"
echo "  WAN: $WAN_FILE"
echo "  Eero: $EERO_FILE"
echo ""

# Activate venv and process
source venv/bin/activate

echo "Processing data files..."
python process_property_outages_db.py \
  --connectivity-file "$WAN_FILE" \
  --discovery-file "$EERO_FILE" \
  --database ./output/outages.db

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Database updated successfully!"
    echo ""
    echo "Restart the application to see new data:"
    echo "  ./start-all.sh"
else
    echo ""
    echo "✗ Error updating database"
    exit 1
fi
