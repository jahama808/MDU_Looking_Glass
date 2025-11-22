#!/usr/bin/env bash
#
# Process all network_outages files and move them to inputs_already_read after processing
# This script is designed to run after download_network_outages.py has downloaded files
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUTS_DIR="${SCRIPT_DIR}/inputs"
ARCHIVE_DIR="${SCRIPT_DIR}/inputs_already_read"
DATABASE="${SCRIPT_DIR}/property_outages.db"
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

# Parse command line arguments
DISCOVERY_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --discovery-file)
            DISCOVERY_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--discovery-file path]"
            echo ""
            echo "Options:"
            echo "  --discovery-file  Optional path to Eero discovery file"
            echo ""
            echo "This script will process all network_outages-*.csv files in the inputs directory"
            echo "and move them to inputs_already_used/ after successful processing."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Create archive directory if it doesn't exist
mkdir -p "${ARCHIVE_DIR}"

echo "============================================================"
echo "BATCH PROCESSING AND ARCHIVING NETWORK OUTAGES"
echo "============================================================"
echo "Inputs directory: ${INPUTS_DIR}"
echo "Archive directory: ${ARCHIVE_DIR}"
echo "Database: ${DATABASE}"
if [[ -n "${DISCOVERY_FILE}" ]]; then
    echo "Discovery file: ${DISCOVERY_FILE}"
else
    echo "Discovery file: None (processing outages only)"
fi
echo "============================================================"
echo ""

# Find all network_outages files
OUTAGE_FILES=($(find "${INPUTS_DIR}" -maxdepth 1 -name "network_outages-*.csv" -type f | sort))

if [[ ${#OUTAGE_FILES[@]} -eq 0 ]]; then
    echo "✓ No network_outages-*.csv files found in ${INPUTS_DIR}"
    echo "  All files have been processed!"
    exit 0
fi

echo "Found ${#OUTAGE_FILES[@]} network outages file(s) to process:"
for file in "${OUTAGE_FILES[@]}"; do
    echo "  - $(basename "$file")"
done
echo ""

# Process each file
SUCCESS_COUNT=0
FAILED_COUNT=0

for FILE in "${OUTAGE_FILES[@]}"; do
    FILENAME=$(basename "$FILE")
    echo "Processing: ${FILENAME}"
    echo "------------------------------------------------------------"

    # Build the command
    CMD="python3 \"${PROCESSING_SCRIPT}\" --outages-file \"${FILE}\" --database \"${DATABASE}\" --mode append --retain-days 7"

    if [[ -n "${DISCOVERY_FILE}" ]]; then
        CMD="${CMD} --discovery-file \"${DISCOVERY_FILE}\""
    fi

    # Execute the command
    if eval ${CMD}; then
        # Move to archive with timestamp subdirectory on success
        TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
        TIMESTAMP_DIR="${ARCHIVE_DIR}/${TIMESTAMP}"
        mkdir -p "${TIMESTAMP_DIR}"
        mv "${FILE}" "${TIMESTAMP_DIR}/"
        echo ""
        echo "✓ Successfully processed and archived: ${FILENAME}"
        echo "  Moved to: ${TIMESTAMP_DIR}/${FILENAME}"
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

echo "============================================================"
echo "PROCESSING COMPLETE"
echo "============================================================"
echo "Successfully processed: ${SUCCESS_COUNT} file(s)"
echo "Failed: ${FAILED_COUNT} file(s)"
echo "Archive location: ${ARCHIVE_DIR}"
echo "============================================================"

if [[ ${FAILED_COUNT} -gt 0 ]]; then
    exit 1
fi
