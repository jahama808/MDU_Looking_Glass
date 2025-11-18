#!/bin/bash
#
# Script to reload historical outage data into the database
#
# Usage:
#   ./reload_historical_data.sh                    # Process all historical files
#   ./reload_historical_data.sh 2025-11-10        # Process specific date
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
HISTORICAL_DIR="./inputs_already_read"
DATABASE="property_outages.db"
DISCOVERY_FILE="$HISTORICAL_DIR/Eero Discovery Details - 2025-11-13 081040.csv"

echo "=========================================="
echo "Historical Data Loader"
echo "=========================================="
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Function to process a single file
process_file() {
    local outage_file=$1
    local filename=$(basename "$outage_file")

    echo -e "${GREEN}Processing: $filename${NC}"

    if [ -f "$DISCOVERY_FILE" ]; then
        python3 process_property_outages_db.py \
            --outages-file "$outage_file" \
            --discovery-file "$DISCOVERY_FILE" \
            --database "$DATABASE"
    else
        python3 process_property_outages_db.py \
            --outages-file "$outage_file" \
            --database "$DATABASE"
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully processed $filename${NC}"
    else
        echo -e "${RED}✗ Failed to process $filename${NC}"
        return 1
    fi
    echo ""
}

# Check if specific date was provided
if [ $# -eq 1 ]; then
    DATE_PATTERN="$1"
    echo "Looking for files matching date: $DATE_PATTERN"
    echo ""

    # Find files matching the date
    for file in "$HISTORICAL_DIR"/network_outages-${DATE_PATTERN}*.csv; do
        if [ -f "$file" ]; then
            process_file "$file"
        fi
    done

    for dir in "$HISTORICAL_DIR"/${DATE_PATTERN}*; do
        if [ -d "$dir" ]; then
            for file in "$dir"/network_outages*.csv; do
                if [ -f "$file" ]; then
                    process_file "$file"
                fi
            done
        fi
    done
else
    echo "Processing ALL historical files..."
    echo -e "${YELLOW}WARNING: This will reprocess all historical data${NC}"
    echo ""
    read -p "Continue? (y/N): " confirm

    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Cancelled."
        exit 0
    fi

    echo ""

    # Process all CSV files in root of historical directory
    for file in "$HISTORICAL_DIR"/network_outages-*.csv; do
        if [ -f "$file" ]; then
            process_file "$file"
        fi
    done

    # Process all CSV files in subdirectories
    for dir in "$HISTORICAL_DIR"/2025-*; do
        if [ -d "$dir" ]; then
            echo -e "${YELLOW}Processing directory: $(basename $dir)${NC}"
            for file in "$dir"/network_outages*.csv; do
                if [ -f "$file" ]; then
                    process_file "$file"
                fi
            done
        fi
    done
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Historical data loading complete!"
echo "==========================================${NC}"
echo ""
echo "Database statistics:"
python3 << 'PYTHON_STATS'
import sqlite3
conn = sqlite3.connect('property_outages.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM properties")
print(f"  Properties: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM networks")
print(f"  Networks: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM outages")
print(f"  Outages: {cursor.fetchone()[0]}")

cursor.execute("SELECT MIN(wan_down_start), MAX(wan_down_start) FROM outages")
date_range = cursor.fetchone()
print(f"  Date range: {date_range[0]} to {date_range[1]}")

conn.close()
PYTHON_STATS

echo ""
echo "Run 'python track_ongoing_outages.py --notify' to check for ongoing outages"
