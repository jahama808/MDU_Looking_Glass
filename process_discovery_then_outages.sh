#!/usr/bin/env bash
#
# Process Eero Discovery file first, then process all network outages files
# This ensures only networks from the discovery file are in the database
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUTS_DIR="${SCRIPT_DIR}/inputs"
ARCHIVE_DIR="${SCRIPT_DIR}/inputs_already_used"
DATABASE="${SCRIPT_DIR}/output/outages.db"
PROCESSING_SCRIPT="${SCRIPT_DIR}/process_property_outages_db.py"

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "   Attempting to activate..."
    if [[ -f "${SCRIPT_DIR}/venv/bin/activate" ]]; then
        source "${SCRIPT_DIR}/venv/bin/activate"
        echo "✓ Virtual environment activated"
    else
        echo "✗ Virtual environment not found at ${SCRIPT_DIR}/venv"
        exit 1
    fi
fi

# Create archive directory if it doesn't exist
mkdir -p "${ARCHIVE_DIR}"

echo "============================================================"
echo "PROCESSING DISCOVERY FILE AND NETWORK OUTAGES"
echo "============================================================"
echo "Inputs directory: ${INPUTS_DIR}"
echo "Archive directory: ${ARCHIVE_DIR}"
echo "Database: ${DATABASE}"
echo "============================================================"
echo ""

# Find Eero Discovery file
DISCOVERY_FILE=$(find "${INPUTS_DIR}" -maxdepth 1 -name "Eero Discovery Details*.csv" -type f | head -1)

if [[ -z "${DISCOVERY_FILE}" ]]; then
    echo "✗ ERROR: No Eero Discovery file found in ${INPUTS_DIR}"
    echo "  Expected format: 'Eero Discovery Details - YYYY-MM-DD HHMMSS.csv'"
    exit 1
fi

echo "Found Discovery file: $(basename "$DISCOVERY_FILE")"
echo ""

# Find all network_outages files
OUTAGE_FILES=($(find "${INPUTS_DIR}" -maxdepth 1 -name "network_outages-*.csv" -type f | sort))

if [[ ${#OUTAGE_FILES[@]} -eq 0 ]]; then
    echo "✗ ERROR: No network_outages-*.csv files found in ${INPUTS_DIR}"
    exit 1
fi

echo "Found ${#OUTAGE_FILES[@]} network outages file(s):"
for file in "${OUTAGE_FILES[@]}"; do
    echo "  - $(basename "$file")"
done
echo ""

# STEP 1: Process first outages file WITH discovery file (rebuild mode)
# This establishes all properties and networks from the discovery file
FIRST_FILE="${OUTAGE_FILES[0]}"
echo "============================================================"
echo "STEP 1: Initialize Database with Discovery + First Outages"
echo "============================================================"
echo "Processing: $(basename "$FIRST_FILE")"
echo "With discovery: $(basename "$DISCOVERY_FILE")"
echo "Mode: REBUILD (creates fresh database)"
echo ""

python3 "${PROCESSING_SCRIPT}" \
    --outages-file "${FIRST_FILE}" \
    --discovery-file "${DISCOVERY_FILE}" \
    --database "${DATABASE}" \
    --mode rebuild

if [[ $? -ne 0 ]]; then
    echo ""
    echo "✗ Failed to process first file with discovery data"
    exit 1
fi

# Move first file to archive
mv "${FIRST_FILE}" "${ARCHIVE_DIR}/"
echo ""
echo "✓ First file processed and archived: $(basename "$FIRST_FILE")"
echo ""

# STEP 2: Process remaining outages files WITHOUT discovery file (append mode)
# This only adds outages for networks that already exist
if [[ ${#OUTAGE_FILES[@]} -gt 1 ]]; then
    echo "============================================================"
    echo "STEP 2: Process Remaining Outages Files"
    echo "============================================================"
    echo "Mode: APPEND (only adds outages for existing networks)"
    echo ""

    SUCCESS_COUNT=1  # Count the first file
    FAILED_COUNT=0

    for (( i=1; i<${#OUTAGE_FILES[@]}; i++ )); do
        FILE="${OUTAGE_FILES[$i]}"
        FILENAME=$(basename "$FILE")

        echo "[$((i+1))/${#OUTAGE_FILES[@]}] Processing: ${FILENAME}"
        echo "------------------------------------------------------------"

        python3 "${PROCESSING_SCRIPT}" \
            --outages-file "${FILE}" \
            --database "${DATABASE}" \
            --mode append \
            --retain-days 30

        if [[ $? -eq 0 ]]; then
            mv "${FILE}" "${ARCHIVE_DIR}/"
            echo ""
            echo "✓ Successfully processed and archived: ${FILENAME}"
            echo ""
            ((SUCCESS_COUNT++))
        else
            echo ""
            echo "✗ Failed to process: ${FILENAME}"
            echo "  File left in inputs directory"
            echo ""
            ((FAILED_COUNT++))
        fi
    done
else
    SUCCESS_COUNT=1
    FAILED_COUNT=0
fi

# Move discovery file to archive at the end
mv "${DISCOVERY_FILE}" "${ARCHIVE_DIR}/"
echo "✓ Discovery file archived: $(basename "$DISCOVERY_FILE")"
echo ""

echo "============================================================"
echo "PROCESSING COMPLETE"
echo "============================================================"
echo "Outage files processed: ${SUCCESS_COUNT}"
echo "Failed: ${FAILED_COUNT}"
echo "Discovery file: Archived"
echo "Archive location: ${ARCHIVE_DIR}"
echo "Database: ${DATABASE}"
echo "============================================================"

if [[ ${FAILED_COUNT} -gt 0 ]]; then
    exit 1
fi
