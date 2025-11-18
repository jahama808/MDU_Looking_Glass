#!/bin/bash

# Install systemd timer for automated data processing
# This script must be run as root or with sudo

set -e

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Property Outage Dashboard - Systemd Timer Installation"
echo "========================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root or with sudo"
    echo "Usage: sudo ./install-systemd.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
echo "Installing for user: $ACTUAL_USER"
echo "Project directory: $PROJECT_DIR"
echo ""

# Create temporary service file with correct paths
cat > /tmp/outage-auto-process.service <<EOF
[Unit]
Description=Property Outage Dashboard - Automated Data Processing
After=network.target

[Service]
Type=oneshot
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/auto-process-data.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Copy files to systemd directory
echo "Installing systemd files..."
cp /tmp/outage-auto-process.service /etc/systemd/system/
cp "$SCRIPT_DIR/outage-auto-process.timer" /etc/systemd/system/
rm /tmp/outage-auto-process.service

# Make sure the script is executable
chmod +x "$PROJECT_DIR/auto-process-data.sh"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start the timer
echo "Enabling timer..."
systemctl enable outage-auto-process.timer

echo "Starting timer..."
systemctl start outage-auto-process.timer

echo ""
echo "✓ Installation complete!"
echo ""
echo "The auto-processing script will now run every 6 hours at:"
echo "  - 00:00 (midnight)"
echo "  - 06:00 (6 AM)"
echo "  - 12:00 (noon)"
echo "  - 18:00 (6 PM)"
echo ""
echo "Useful commands:"
echo "  Check timer status:  systemctl status outage-auto-process.timer"
echo "  Check service logs:  journalctl -u outage-auto-process.service"
echo "  Run now manually:    systemctl start outage-auto-process.service"
echo "  Stop timer:          systemctl stop outage-auto-process.timer"
echo "  Disable timer:       systemctl disable outage-auto-process.timer"
echo ""
echo "Next scheduled run:"
systemctl list-timers outage-auto-process.timer
