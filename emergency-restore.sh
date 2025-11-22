#!/bin/bash

#############################################################################
# EMERGENCY RESTORE SCRIPT - MDU Performance Dashboard
#
# Restores a complete backup on a new server with a single command
#
# Usage:
#   sudo ./emergency-restore.sh [options]
#
# Options:
#   --install-dir PATH    Installation directory (default: /opt/mdu-dashboard)
#   --api-port PORT       API server port (default: 5000)
#   --frontend-port PORT  Frontend port (default: 3000)
#   --no-services         Don't create/start systemd services
#   --help                Show this help message
#
# Prerequisites:
#   - Must be run as root or with sudo
#   - Backup must be extracted first (this script runs from backup directory)
#
# What is restored:
#   - All application code
#   - Database (property_outages.db)
#   - Cron jobs
#   - Python virtual environment
#   - Frontend build
#   - Systemd services (optional)
#
#############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default configuration
INSTALL_DIR="/opt/mdu-dashboard"
API_PORT=5000
FRONTEND_PORT=3000
CREATE_SERVICES=true
BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --api-port)
            API_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --no-services)
            CREATE_SERVICES=false
            shift
            ;;
        --help)
            head -30 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root or with sudo${NC}"
   exit 1
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}MDU Performance Dashboard - EMERGENCY RESTORE${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "Configuration:"
echo "  Installation directory: $INSTALL_DIR"
echo "  API port: $API_PORT"
echo "  Frontend port: $FRONTEND_PORT"
echo "  Create systemd services: $CREATE_SERVICES"
echo "  Backup directory: $BACKUP_DIR"
echo ""
echo -e "${YELLOW}Press Ctrl+C within 5 seconds to cancel...${NC}"
sleep 5

#############################################################################
# 1. Detect OS and Install Dependencies
#############################################################################

echo ""
echo -e "${BLUE}[1/11]${NC} Detecting operating system..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
    echo -e "${GREEN}✓${NC} Detected: $PRETTY_NAME"
else
    echo -e "${RED}✗${NC} Cannot detect operating system"
    exit 1
fi

echo ""
echo -e "${BLUE}[2/11]${NC} Installing system dependencies..."

case $OS in
    ubuntu|debian)
        apt-get update
        apt-get install -y python3 python3-pip python3-venv nodejs npm sqlite3 rsync curl
        echo -e "${GREEN}✓${NC} Dependencies installed (apt)"
        ;;
    centos|rhel|fedora)
        yum install -y python3 python3-pip nodejs npm sqlite rsync curl
        echo -e "${GREEN}✓${NC} Dependencies installed (yum)"
        ;;
    *)
        echo -e "${YELLOW}⚠${NC} Unknown OS: $OS"
        echo "Please manually install: python3, python3-pip, python3-venv, nodejs, npm, sqlite3, rsync, curl"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        ;;
esac

# Verify Node.js version
NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo -e "${YELLOW}⚠${NC} Node.js version is $NODE_VERSION, but 16+ is recommended"
fi

#############################################################################
# 2. Create Installation Directory
#############################################################################

echo ""
echo -e "${BLUE}[3/11]${NC} Creating installation directory..."

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠${NC} Directory $INSTALL_DIR already exists"
    read -p "Remove existing directory and continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}✓${NC} Removed existing directory"
    else
        echo -e "${RED}✗${NC} Restore cancelled"
        exit 1
    fi
fi

mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}✓${NC} Created $INSTALL_DIR"

#############################################################################
# 3. Copy Application Files
#############################################################################

echo ""
echo -e "${BLUE}[4/11]${NC} Copying application files..."

# Copy all files from backup to install directory
rsync -av --exclude='venv' --exclude='node_modules' --exclude='dist' --exclude='*.tar.gz' \
    "$BACKUP_DIR/" "$INSTALL_DIR/"

echo -e "${GREEN}✓${NC} Application files copied"

#############################################################################
# 4. Set Up Python Environment
#############################################################################

echo ""
echo -e "${BLUE}[5/11]${NC} Setting up Python virtual environment..."

cd "$INSTALL_DIR"

python3 -m venv venv
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${YELLOW}⚠${NC} No requirements.txt found, skipping Python dependencies"
fi

#############################################################################
# 5. Set Up Frontend
#############################################################################

echo ""
echo -e "${BLUE}[6/11]${NC} Setting up frontend..."

if [ -d "frontend" ]; then
    cd "$INSTALL_DIR/frontend"

    # Install dependencies
    npm install
    echo -e "${GREEN}✓${NC} Frontend dependencies installed"

    # Build production version
    npm run build
    echo -e "${GREEN}✓${NC} Frontend built for production"
else
    echo -e "${YELLOW}⚠${NC} No frontend directory found, skipping frontend setup"
fi

cd "$INSTALL_DIR"

#############################################################################
# 6. Restore Database
#############################################################################

echo ""
echo -e "${BLUE}[7/11]${NC} Restoring database..."

if [ -f "property_outages.db" ]; then
    echo -e "${GREEN}✓${NC} Database restored (property_outages.db)"
    DB_SIZE=$(du -h property_outages.db | cut -f1)
    echo "  Database size: $DB_SIZE"
else
    echo -e "${YELLOW}⚠${NC} No database file found in backup"
fi

#############################################################################
# 7. Restore Cron Jobs
#############################################################################

echo ""
echo -e "${BLUE}[8/11]${NC} Restoring cron jobs..."

if [ -f "crontab.txt" ]; then
    # Update paths in crontab to new installation directory
    sed "s|$(cat original_install_path.txt 2>/dev/null || echo '/old/path')|$INSTALL_DIR|g" crontab.txt > crontab_updated.txt

    echo -e "${YELLOW}Cron jobs found in backup:${NC}"
    cat crontab_updated.txt
    echo ""
    read -p "Install these cron jobs for current user? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        crontab crontab_updated.txt
        echo -e "${GREEN}✓${NC} Cron jobs installed"
    else
        echo -e "${YELLOW}⚠${NC} Cron jobs not installed (file saved as crontab_updated.txt)"
    fi
else
    echo -e "${YELLOW}⚠${NC} No crontab.txt found in backup"
fi

#############################################################################
# 8. Set Permissions
#############################################################################

echo ""
echo -e "${BLUE}[9/11]${NC} Setting file permissions..."

# Make scripts executable
chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR"/*.py 2>/dev/null || true

# Set appropriate ownership (to the user who invoked sudo)
if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER:$SUDO_USER" "$INSTALL_DIR"
    echo -e "${GREEN}✓${NC} Ownership set to $SUDO_USER"
fi

echo -e "${GREEN}✓${NC} Permissions configured"

#############################################################################
# 9. Create Systemd Services
#############################################################################

if [ "$CREATE_SERVICES" = true ]; then
    echo ""
    echo -e "${BLUE}[10/11]${NC} Creating systemd services..."

    # API Service
    cat > /etc/systemd/system/mdu-api.service <<EOF
[Unit]
Description=MDU Performance Dashboard API Server
After=network.target

[Service]
Type=simple
User=${SUDO_USER:-root}
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}✓${NC} Created mdu-api.service"

    # Frontend Service (using Python's http.server for simplicity)
    cat > /etc/systemd/system/mdu-frontend.service <<EOF
[Unit]
Description=MDU Performance Dashboard Frontend
After=network.target

[Service]
Type=simple
User=${SUDO_USER:-root}
WorkingDirectory=$INSTALL_DIR/frontend/dist
ExecStart=/usr/bin/python3 -m http.server $FRONTEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}✓${NC} Created mdu-frontend.service"

    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable mdu-api.service
    systemctl enable mdu-frontend.service
    echo -e "${GREEN}✓${NC} Services enabled"
else
    echo ""
    echo -e "${YELLOW}[10/11] Skipping systemd service creation${NC}"
fi

#############################################################################
# 10. Start Services
#############################################################################

if [ "$CREATE_SERVICES" = true ]; then
    echo ""
    echo -e "${BLUE}[11/11]${NC} Starting services..."

    systemctl start mdu-api.service
    sleep 2
    systemctl start mdu-frontend.service
    sleep 2

    # Check service status
    if systemctl is-active --quiet mdu-api.service; then
        echo -e "${GREEN}✓${NC} API server started"
    else
        echo -e "${RED}✗${NC} API server failed to start"
        systemctl status mdu-api.service --no-pager
    fi

    if systemctl is-active --quiet mdu-frontend.service; then
        echo -e "${GREEN}✓${NC} Frontend server started"
    else
        echo -e "${RED}✗${NC} Frontend server failed to start"
        systemctl status mdu-frontend.service --no-pager
    fi
else
    echo ""
    echo -e "${BLUE}[11/11]${NC} Manual service start required"
    echo ""
    echo "To start services manually:"
    echo "  1. Start API server:"
    echo "     cd $INSTALL_DIR"
    echo "     source venv/bin/activate"
    echo "     python3 api_server.py"
    echo ""
    echo "  2. Start Frontend (in another terminal):"
    echo "     cd $INSTALL_DIR/frontend/dist"
    echo "     python3 -m http.server $FRONTEND_PORT"
fi

#############################################################################
# 11. Display Success Information
#############################################################################

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}RESTORE COMPLETE!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "Installation Details:"
echo -e "  Location: ${BLUE}$INSTALL_DIR${NC}"
echo -e "  Database: ${BLUE}property_outages.db${NC}"
if [ -f "property_outages.db" ]; then
    OUTAGE_COUNT=$(sqlite3 property_outages.db "SELECT COUNT(*) FROM outages" 2>/dev/null || echo "N/A")
    NETWORK_COUNT=$(sqlite3 property_outages.db "SELECT COUNT(*) FROM networks" 2>/dev/null || echo "N/A")
    echo -e "  Outages in DB: ${BLUE}$OUTAGE_COUNT${NC}"
    echo -e "  Networks in DB: ${BLUE}$NETWORK_COUNT${NC}"
fi
echo ""

if [ "$CREATE_SERVICES" = true ]; then
    echo "Services:"
    echo -e "  API: ${BLUE}systemctl status mdu-api.service${NC}"
    echo -e "  Frontend: ${BLUE}systemctl status mdu-frontend.service${NC}"
    echo ""
    echo "Access the application:"
    HOSTNAME=$(hostname -I | awk '{print $1}' || echo "localhost")
    echo -e "  ${BLUE}http://$HOSTNAME:$FRONTEND_PORT${NC}"
    echo -e "  ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
fi

echo ""
echo "Useful commands:"
echo "  View API logs: journalctl -u mdu-api.service -f"
echo "  View frontend logs: journalctl -u mdu-frontend.service -f"
echo "  Restart API: systemctl restart mdu-api.service"
echo "  Restart frontend: systemctl restart mdu-frontend.service"
echo ""
echo "Cron jobs:"
if [ -f "crontab.txt" ]; then
    echo "  View installed: crontab -l"
    echo "  Edit: crontab -e"
fi
echo ""

echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Verify the application is accessible at the URL above"
echo "2. Check that scheduled jobs are running (crontab -l)"
echo "3. Update firewall rules if needed to allow ports $API_PORT and $FRONTEND_PORT"
echo "4. Configure reverse proxy (nginx/apache) for production use"
echo "5. Set up SSL certificates for HTTPS access"
echo ""
echo -e "${GREEN}✓ Emergency restore complete!${NC}"
echo ""
