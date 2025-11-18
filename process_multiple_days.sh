#!/usr/bin/env bash
#
# Batch process multiple network_outages files
# This script processes network outage files for multiple days and updates the database
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUTS_DIR="${SCRIPT_DIR}/inputs"
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
        echo "   Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
fi

# Parse command line arguments
MODE="rebuild"  # Default to rebuild for first run
DISCOVERY_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --discovery-file)
            DISCOVERY_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--mode rebuild|append] [--discovery-file path]"
            echo ""
            echo "Options:"
            echo "  --mode            Processing mode: 'rebuild' (default) or 'append'"
            echo "  --discovery-file  Optional path to Eero discovery file"
            echo ""
            echo "This script will process all network_outages-*.csv files found in the inputs directory."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

echo "============================================================"
echo "BATCH PROCESSING NETWORK OUTAGES"
echo "============================================================"
echo "Inputs directory: ${INPUTS_DIR}"
echo "Database: ${DATABASE}"
echo "Mode: ${MODE}"
if [[ -n "${DISCOVERY_FILE}" ]]; then
    echo "Discovery file: ${DISCOVERY_FILE}"
else
    echo "Discovery file: None (processing outages only)"
fi
echo "============================================================"
echo ""

# Find all network_outages files
OUTAGE_FILES=($(find "${INPUTS_DIR}" -name "network_outages-*.csv" -type f | sort))

if [[ ${#OUTAGE_FILES[@]} -eq 0 ]]; then
    echo "✗ No network_outages-*.csv files found in ${INPUTS_DIR}"
    exit 1
fi

echo "Found ${#OUTAGE_FILES[@]} network outages file(s) to process:"
for file in "${OUTAGE_FILES[@]}"; do
    echo "  - $(basename "$file")"
done
echo ""

# Process first file with specified mode (rebuild or append)
FIRST_FILE="${OUTAGE_FILES[0]}"
echo "Processing first file with mode='${MODE}': $(basename "$FIRST_FILE")"
echo "------------------------------------------------------------"

if [[ -n "${DISCOVERY_FILE}" ]]; then
    python3 "${PROCESSING_SCRIPT}" \
        --outages-file "${FIRST_FILE}" \
        --discovery-file "${DISCOVERY_FILE}" \
        --database "${DATABASE}" \
        --mode "${MODE}"
else
    python3 "${PROCESSING_SCRIPT}" \
        --outages-file "${FIRST_FILE}" \
        --database "${DATABASE}" \
        --mode "${MODE}"
fi

echo ""
echo "✓ First file processed successfully"
echo ""

# Process remaining files in append mode
if [[ ${#OUTAGE_FILES[@]} -gt 1 ]]; then
    echo "Processing remaining files in append mode..."
    echo ""

    for (( i=1; i<${#OUTAGE_FILES[@]}; i++ )); do
        FILE="${OUTAGE_FILES[$i]}"
        echo "[$((i+1))/${#OUTAGE_FILES[@]}] Processing: $(basename "$FILE")"
        echo "------------------------------------------------------------"

        if [[ -n "${DISCOVERY_FILE}" ]]; then
            python3 "${PROCESSING_SCRIPT}" \
                --outages-file "${FILE}" \
                --discovery-file "${DISCOVERY_FILE}" \
                --database "${DATABASE}" \
                --mode append \
                --retain-days 30
        else
            python3 "${PROCESSING_SCRIPT}" \
                --outages-file "${FILE}" \
                --database "${DATABASE}" \
                --mode append \
                --retain-days 30
        fi

        echo ""
    done

    echo "✓ All files processed successfully"
else
    echo "Only one file to process - done!"
fi

echo ""
echo "============================================================"
echo "BATCH PROCESSING COMPLETE"
echo "============================================================"
echo "Database location: ${DATABASE}"
echo "Total files processed: ${#OUTAGE_FILES[@]}"
echo "============================================================"
