#!/bin/bash

#############################################################################
# BACKUP SCRIPT - Property Outage Dashboard
#
# Creates a complete backup of the application for disaster recovery.
#
# Usage:
#   ./create-backup.sh [output-directory]
#
# Default backup location: ./backups/
#
# What is backed up:
#   - Database (output/outages.db)
#   - Configuration files
#   - Processed data archive (inputs_already_read/)
#   - Processing logs (logs/)
#   - Application code (entire directory)
#
# Backup file naming: outage-dashboard-backup-YYYY-MM-DD_HHMMSS.tar.gz
#############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="${1:-$SCRIPT_DIR/backups}"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
BACKUP_NAME="outage-dashboard-backup-$TIMESTAMP"
BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME.tar.gz"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Property Outage Dashboard - Backup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

cd "$SCRIPT_DIR"

echo -e "${BLUE}[INFO]${NC} Creating backup: $BACKUP_NAME"
echo -e "${BLUE}[INFO]${NC} Backup location: $BACKUP_FILE"
echo ""

# Create temporary file list
TEMP_LIST=$(mktemp)

# What to include
cat > "$TEMP_LIST" <<EOF
output/outages.db
logs/
inputs_already_read/
*.py
*.sh
*.bat
*.ps1
*.md
*.txt
frontend/
systemd/
.gitignore
requirements.txt
package.json
vite.config.js
EOF

# What to exclude
EXCLUDE_PATTERNS=(
    "venv"
    "node_modules"
    "frontend/dist"
    "frontend/node_modules"
    "backups"
    "inputs/*.csv"
    "*.pyc"
    "__pycache__"
    ".git"
)

# Build exclude arguments
EXCLUDE_ARGS=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$pattern"
done

# Create backup
echo -e "${BLUE}[INFO]${NC} Compressing files..."
tar -czf "$BACKUP_FILE" \
    $EXCLUDE_ARGS \
    --exclude-from="$TEMP_LIST" \
    -C "$SCRIPT_DIR" \
    $(cat "$TEMP_LIST" | grep -v "^#" | tr '\n' ' ')

# Also create a simple backup with just essentials
ESSENTIAL_BACKUP="$BACKUP_DIR/outage-dashboard-essential-$TIMESTAMP.tar.gz"
echo -e "${BLUE}[INFO]${NC} Creating essential backup (database and logs only)..."
tar -czf "$ESSENTIAL_BACKUP" \
    -C "$SCRIPT_DIR" \
    output/outages.db \
    logs/ \
    inputs_already_read/ 2>/dev/null || true

# Clean up
rm -f "$TEMP_LIST"

# Show backup info
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
ESSENTIAL_SIZE=$(du -h "$ESSENTIAL_BACKUP" | cut -f1)

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Full Backup:"
echo -e "  File: ${BLUE}$BACKUP_FILE${NC}"
echo -e "  Size: ${BLUE}$BACKUP_SIZE${NC}"
echo ""
echo "Essential Backup (database + logs):"
echo -e "  File: ${BLUE}$ESSENTIAL_BACKUP${NC}"
echo -e "  Size: ${BLUE}$ESSENTIAL_SIZE${NC}"
echo ""
echo "Backup contains:"
echo "  ✓ Database (output/outages.db)"
echo "  ✓ Processing logs (logs/)"
echo "  ✓ Processed data archive (inputs_already_read/)"
echo "  ✓ Application code (Python, Shell scripts)"
echo "  ✓ Frontend code (React application)"
echo "  ✓ Configuration files"
echo ""
echo "To restore on a new server:"
echo "  1. Copy backup file to new server"
echo "  2. Extract: tar -xzf $BACKUP_NAME.tar.gz"
echo "  3. Run: sudo ./emergency-install.sh --restore-backup $BACKUP_NAME.tar.gz"
echo ""
echo "Or see EMERGENCY_DEPLOYMENT.md for detailed instructions"
echo ""

# Optional: Clean up old backups (keep last 7 days)
if [ -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}[INFO]${NC} Cleaning up old backups (keeping last 7 days)..."
    find "$BACKUP_DIR" -name "outage-dashboard-backup-*.tar.gz" -mtime +7 -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "outage-dashboard-essential-*.tar.gz" -mtime +7 -delete 2>/dev/null || true
fi

echo -e "${GREEN}✓ Backup process complete${NC}"
