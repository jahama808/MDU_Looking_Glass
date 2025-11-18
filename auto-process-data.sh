#!/bin/bash

# Automated Data Processing Script
# Checks for new data files and processes them automatically

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Directories
INPUTS_DIR="inputs"
ARCHIVE_DIR="inputs_already_read"
DB_PATH="./output/outages.db"
LOG_FILE="./logs/auto-process.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_color() {
    echo -e "${2}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_color "========================================" "$BLUE"
log_color "Automated Data Processing - Starting" "$BLUE"
log_color "========================================" "$BLUE"

# Create directories if they don't exist
mkdir -p "$INPUTS_DIR"
mkdir -p "$ARCHIVE_DIR"
mkdir -p logs

# Check if inputs directory exists and has files
if [ ! -d "$INPUTS_DIR" ]; then
    log_color "Error: Inputs directory not found: $INPUTS_DIR" "$RED"
    exit 1
fi

# Find connectivity file (most recent if multiple)
WAN_FILE=$(find "$INPUTS_DIR" -maxdepth 1 -name "network_outages-*" -type f 2>/dev/null | sort -r | head -1)

# Find Eero discovery file (most recent if multiple)
EERO_FILE=$(find "$INPUTS_DIR" -maxdepth 1 -name "Eero Discovery Details*" -o -name "Eero*Discovery*Details*" -type f 2>/dev/null | sort -r | head -1)

# Check if both files were found
if [ -z "$WAN_FILE" ] || [ -z "$EERO_FILE" ]; then
    log_color "No new files to process" "$YELLOW"
    
    if [ -z "$WAN_FILE" ]; then
        log "  Missing: network_outages-*.csv"
    fi
    
    if [ -z "$EERO_FILE" ]; then
        log "  Missing: Eero Discovery Details*.csv"
    fi
    
    log "Exiting - no action taken"
    exit 0
fi

log_color "Files found for processing:" "$GREEN"
log "  WAN Connectivity: $(basename "$WAN_FILE")"
log "  Eero Discovery:   $(basename "$EERO_FILE")"

# Check if files have already been processed
WAN_BASENAME=$(basename "$WAN_FILE")
EERO_BASENAME=$(basename "$EERO_FILE")

if [ -f "$ARCHIVE_DIR/$WAN_BASENAME" ] && [ -f "$ARCHIVE_DIR/$EERO_BASENAME" ]; then
    log_color "Files already processed (found in archive)" "$YELLOW"
    log "Exiting - no action taken"
    exit 0
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    log_color "Error: Virtual environment not found" "$RED"
    log "Please run install.sh first"
    exit 1
fi

source venv/bin/activate
log_color "Virtual environment activated" "$GREEN"

# Process the data
log_color "Processing data files..." "$BLUE"

if python process_property_outages_db.py \
    --connectivity-file "$WAN_FILE" \
    --discovery-file "$EERO_FILE" \
    --database "$DB_PATH" \
    --mode append \
    --retain-days 7 2>&1 | tee -a "$LOG_FILE"; then
    
    log_color "✓ Data processing completed successfully" "$GREEN"
    
    # Move files to archive
    log "Moving files to archive..."
    
    # Create timestamped archive subdirectory
    ARCHIVE_SUBDIR="$ARCHIVE_DIR/$(date '+%Y-%m-%d_%H%M%S')"
    mkdir -p "$ARCHIVE_SUBDIR"
    
    mv "$WAN_FILE" "$ARCHIVE_SUBDIR/"
    mv "$EERO_FILE" "$ARCHIVE_SUBDIR/"
    
    log_color "✓ Files archived to: $ARCHIVE_SUBDIR" "$GREEN"
    
    # Optional: Restart services if running
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet outage-dashboard-api 2>/dev/null; then
            log "Restarting API service..."
            systemctl restart outage-dashboard-api
            log_color "✓ API service restarted" "$GREEN"
        fi
    fi
    
    log_color "========================================" "$BLUE"
    log_color "Processing Complete!" "$GREEN"
    log_color "Database updated: $DB_PATH" "$GREEN"
    log_color "========================================" "$BLUE"
    
else
    log_color "✗ Error during data processing" "$RED"
    log "Files NOT moved to archive (will retry on next run)"
    exit 1
fi
