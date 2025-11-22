#!/bin/bash

#############################################################################
# COMPREHENSIVE BACKUP SCRIPT - MDU Performance Dashboard
#
# Creates a complete backup including database, code, config, and cron jobs
#
# Usage:
#   ./emergency-backup.sh [output-directory]
#
# Default backup location: ./backups/
#
# What is backed up:
#   - Database (property_outages.db)
#   - All application code
#   - Configuration files (.env if exists)
#   - Cron jobs
#   - Processing logs
#   - Archived data (inputs_already_read/)
#   - requirements.txt for Python dependencies
#
# Backup file naming: mdu-dashboard-YYYY-MM-DD_HHMMSS.tar.gz
#############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="${1:-$SCRIPT_DIR/backups}"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
BACKUP_NAME="mdu-dashboard-$TIMESTAMP"
BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME.tar.gz"
TEMP_DIR=$(mktemp -d)

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}MDU Performance Dashboard - COMPREHENSIVE BACKUP${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$TEMP_DIR/$BACKUP_NAME"

cd "$SCRIPT_DIR"

echo -e "${BLUE}[1/7]${NC} Backing up database..."
if [ -f "property_outages.db" ]; then
    cp property_outages.db "$TEMP_DIR/$BACKUP_NAME/"
    echo -e "${GREEN}✓${NC} Database backed up"
else
    echo -e "${YELLOW}⚠${NC} Warning: property_outages.db not found"
fi

echo ""
echo -e "${BLUE}[2/7]${NC} Backing up cron jobs..."
crontab -l > "$TEMP_DIR/$BACKUP_NAME/crontab.txt" 2>/dev/null || echo "No crontab found" > "$TEMP_DIR/$BACKUP_NAME/crontab.txt"
echo -e "${GREEN}✓${NC} Cron jobs backed up"

echo ""
echo -e "${BLUE}[3/7]${NC} Backing up environment and configuration..."
# Save .env if it exists
if [ -f ".env" ]; then
    cp .env "$TEMP_DIR/$BACKUP_NAME/"
    echo -e "${GREEN}✓${NC} .env file backed up"
else
    echo -e "${YELLOW}⚠${NC} No .env file found"
fi

# Save Python requirements
if [ -f "requirements.txt" ]; then
    cp requirements.txt "$TEMP_DIR/$BACKUP_NAME/"
fi

# Save current directory path for reference
echo "$SCRIPT_DIR" > "$TEMP_DIR/$BACKUP_NAME/original_install_path.txt"

echo ""
echo -e "${BLUE}[4/7]${NC} Backing up application code..."
# Copy all Python scripts
cp *.py "$TEMP_DIR/$BACKUP_NAME/" 2>/dev/null || true
# Copy all shell scripts
cp *.sh "$TEMP_DIR/$BACKUP_NAME/" 2>/dev/null || true
# Copy batch files
cp *.bat "$TEMP_DIR/$BACKUP_NAME/" 2>/dev/null || true
# Copy PowerShell scripts
cp *.ps1 "$TEMP_DIR/$BACKUP_NAME/" 2>/dev/null || true
# Copy documentation
cp *.md "$TEMP_DIR/$BACKUP_NAME/" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Application code backed up"

echo ""
echo -e "${BLUE}[5/7]${NC} Backing up frontend..."
if [ -d "frontend" ]; then
    mkdir -p "$TEMP_DIR/$BACKUP_NAME/frontend"
    rsync -a --exclude='node_modules' --exclude='dist' frontend/ "$TEMP_DIR/$BACKUP_NAME/frontend/"
    echo -e "${GREEN}✓${NC} Frontend backed up"
else
    echo -e "${YELLOW}⚠${NC} Frontend directory not found"
fi

echo ""
echo -e "${BLUE}[6/7]${NC} Backing up data and logs..."
# Backup logs (last 30 days)
if [ -d "logs" ]; then
    mkdir -p "$TEMP_DIR/$BACKUP_NAME/logs"
    find logs/ -name "*.log" -mtime -30 -exec cp {} "$TEMP_DIR/$BACKUP_NAME/logs/" \; 2>/dev/null || true
fi

# Backup processing reports (last 30 days)
if [ -d "processing_reports" ]; then
    mkdir -p "$TEMP_DIR/$BACKUP_NAME/processing_reports"
    find processing_reports/ -name "*.txt" -mtime -30 -exec cp {} "$TEMP_DIR/$BACKUP_NAME/processing_reports/" \; 2>/dev/null || true
fi

# Backup recent archived inputs (last 7 days)
if [ -d "inputs_already_read" ]; then
    mkdir -p "$TEMP_DIR/$BACKUP_NAME/inputs_already_read"
    find inputs_already_read/ -type f -mtime -7 -exec bash -c 'mkdir -p "$TEMP_DIR/$BACKUP_NAME/$(dirname {})" && cp {} "$TEMP_DIR/$BACKUP_NAME/{}"' \; 2>/dev/null || true
fi
echo -e "${GREEN}✓${NC} Data and logs backed up"

echo ""
echo -e "${BLUE}[7/7]${NC} Creating backup metadata..."
cat > "$TEMP_DIR/$BACKUP_NAME/BACKUP_INFO.txt" <<EOF
MDU Performance Dashboard - Backup Information
=============================================
Backup Date: $(date)
Hostname: $(hostname)
Original Path: $SCRIPT_DIR
Backup Version: 2.0

Contents:
- Database: property_outages.db
- Cron jobs: crontab.txt
- Application code: All .py, .sh, .bat, .ps1 files
- Frontend: React application (without node_modules)
- Logs: Last 30 days
- Processing reports: Last 30 days
- Archived inputs: Last 7 days
- Configuration: .env (if exists)

Restore Instructions:
1. Copy this backup to the new server
2. Extract: tar -xzf $BACKUP_NAME.tar.gz
3. Run: cd $BACKUP_NAME && sudo ./emergency-restore.sh

Or see EMERGENCY_DEPLOYMENT.md for detailed instructions.
EOF
echo -e "${GREEN}✓${NC} Metadata created"

echo ""
echo -e "${BLUE}[INFO]${NC} Compressing backup..."
cd "$TEMP_DIR"
tar -czf "$BACKUP_FILE" "$BACKUP_NAME"
cd "$SCRIPT_DIR"

# Clean up temp directory
rm -rf "$TEMP_DIR"

# Show backup info
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
DB_SIZE=$(du -h "property_outages.db" 2>/dev/null | cut -f1 || echo "N/A")

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}BACKUP COMPLETE!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "Backup Details:"
echo -e "  File: ${BLUE}$BACKUP_FILE${NC}"
echo -e "  Size: ${BLUE}$BACKUP_SIZE${NC}"
echo -e "  Database: ${BLUE}$DB_SIZE${NC}"
echo ""
echo "Backup includes:"
echo "  ✓ Database (property_outages.db)"
echo "  ✓ Cron jobs configuration"
echo "  ✓ Application code (Python, Shell scripts)"
echo "  ✓ Frontend (React application)"
echo "  ✓ Recent logs (last 30 days)"
echo "  ✓ Processing reports (last 30 days)"
echo "  ✓ Recent archived data (last 7 days)"
echo "  ✓ Environment configuration (.env if exists)"
echo ""
echo "To restore on a new server:"
echo "  1. Copy backup to new server:"
echo -e "     ${BLUE}scp $BACKUP_FILE user@new-server:/tmp/${NC}"
echo ""
echo "  2. On new server, extract and restore:"
echo -e "     ${BLUE}cd /tmp${NC}"
echo -e "     ${BLUE}tar -xzf $BACKUP_NAME.tar.gz${NC}"
echo -e "     ${BLUE}cd $BACKUP_NAME${NC}"
echo -e "     ${BLUE}sudo ./emergency-restore.sh${NC}"
echo ""

# Optional: Clean up old backups (keep last 14 days)
if [ -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}[INFO]${NC} Cleaning up old backups (keeping last 14 days)..."
    find "$BACKUP_DIR" -name "mdu-dashboard-*.tar.gz" -mtime +14 -delete 2>/dev/null || true
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "mdu-dashboard-*.tar.gz" | wc -l)
    echo -e "${GREEN}✓${NC} Cleanup complete (${OLD_BACKUPS} backups remaining)"
fi

echo ""
echo -e "${GREEN}✓ Backup process complete!${NC}"
echo ""
