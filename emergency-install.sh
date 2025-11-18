#!/bin/bash

#############################################################################
# EMERGENCY DEPLOYMENT SCRIPT FOR UBUNTU
# Property Outage Dashboard - Complete System Installation
#
# This script performs a complete installation and setup on a fresh Ubuntu
# server. Use this for disaster recovery or new server deployment.
#
# Usage:
#   sudo ./emergency-install.sh [--restore-backup /path/to/backup.tar.gz]
#
# What this script does:
#   1. Installs all system dependencies (Python, Node.js, nginx)
#   2. Sets up the application with all dependencies
#   3. Configures systemd services for automatic startup
#   4. Sets up automated data processing
#   5. Configures firewall
#   6. Optionally restores from backup
#   7. Starts all services
#
# Requirements:
#   - Ubuntu 20.04 or later
#   - Root/sudo access
#   - Internet connection
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="outage-dashboard"
APP_USER="${SUDO_USER:-$USER}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$SCRIPT_DIR"
BACKUP_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --restore-backup)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: sudo $0 [--restore-backup /path/to/backup.tar.gz]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

#############################################################################
# Helper Functions
#############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

check_ubuntu() {
    if [ ! -f /etc/os-release ]; then
        log_error "Cannot detect OS version"
        exit 1
    fi

    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        log_warn "This script is designed for Ubuntu. Detected: $ID"
        read -p "Continue anyway? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    log_info "Detected: $PRETTY_NAME"
}

#############################################################################
# Installation Steps
#############################################################################

install_system_dependencies() {
    print_header "Installing System Dependencies"

    log_info "Updating package lists..."
    apt-get update -qq

    log_info "Installing Python 3 and pip..."
    apt-get install -y python3 python3-pip python3-venv

    log_info "Installing Node.js and npm..."
    # Install Node.js 18.x LTS
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi

    log_info "Installing additional utilities..."
    apt-get install -y curl git sqlite3 nginx

    log_success "System dependencies installed"

    # Show versions
    log_info "Installed versions:"
    python3 --version
    node --version
    npm --version
}

setup_application() {
    print_header "Setting Up Application"

    cd "$INSTALL_DIR"

    # Create necessary directories
    log_info "Creating directory structure..."
    mkdir -p output logs inputs inputs_already_read
    chown -R "$APP_USER:$APP_USER" output logs inputs inputs_already_read

    # Set up Python virtual environment
    log_info "Creating Python virtual environment..."
    if [ -d "venv" ]; then
        log_warn "Virtual environment already exists, removing..."
        rm -rf venv
    fi

    sudo -u "$APP_USER" python3 -m venv venv

    log_info "Installing Python dependencies..."
    sudo -u "$APP_USER" venv/bin/pip install --upgrade pip
    sudo -u "$APP_USER" venv/bin/pip install flask flask-cors pandas

    # Set up Node.js dependencies
    log_info "Installing Node.js dependencies..."
    cd frontend
    sudo -u "$APP_USER" npm install

    log_info "Building frontend for production..."
    sudo -u "$APP_USER" npm run build

    cd "$INSTALL_DIR"
    log_success "Application setup complete"
}

setup_systemd_services() {
    print_header "Setting Up Systemd Services"

    # Create API service
    log_info "Creating API service..."
    cat > /etc/systemd/system/outage-dashboard-api.service <<EOF
[Unit]
Description=Property Outage Dashboard - API Server
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Create frontend service (using a simple Python HTTP server for the build)
    log_info "Creating frontend service..."
    cat > /etc/systemd/system/outage-dashboard-frontend.service <<EOF
[Unit]
Description=Property Outage Dashboard - Frontend Server
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$INSTALL_DIR/frontend/dist
ExecStart=/usr/bin/python3 -m http.server 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Set up auto-processing timer
    log_info "Setting up auto-processing timer..."
    cat > /etc/systemd/system/outage-auto-process.service <<EOF
[Unit]
Description=Property Outage Dashboard - Automated Data Processing
After=network.target

[Service]
Type=oneshot
User=$APP_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/auto-process-data.sh
StandardOutput=journal
StandardError=journal
EOF

    cp "$INSTALL_DIR/systemd/outage-auto-process.timer" /etc/systemd/system/

    # Make scripts executable
    chmod +x "$INSTALL_DIR/auto-process-data.sh"
    chmod +x "$INSTALL_DIR/update-data.sh" 2>/dev/null || true

    # Reload systemd
    systemctl daemon-reload

    # Enable services
    log_info "Enabling services..."
    systemctl enable outage-dashboard-api.service
    systemctl enable outage-dashboard-frontend.service
    systemctl enable outage-auto-process.timer

    log_success "Systemd services configured"
}

configure_nginx() {
    print_header "Configuring Nginx Reverse Proxy"

    log_info "Creating nginx configuration..."
    cat > /etc/nginx/sites-available/outage-dashboard <<'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/outage-dashboard /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Test nginx config
    nginx -t

    log_success "Nginx configured"
}

configure_firewall() {
    print_header "Configuring Firewall"

    if command -v ufw &> /dev/null; then
        log_info "Configuring UFW firewall..."
        ufw --force enable
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw status
        log_success "Firewall configured"
    else
        log_warn "UFW not installed, skipping firewall configuration"
    fi
}

restore_backup() {
    if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
        print_header "Restoring from Backup"

        log_info "Extracting backup: $BACKUP_FILE"
        cd "$INSTALL_DIR"
        tar -xzf "$BACKUP_FILE"

        # Fix permissions
        chown -R "$APP_USER:$APP_USER" output logs inputs inputs_already_read

        log_success "Backup restored"
    elif [ -n "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
}

start_services() {
    print_header "Starting Services"

    log_info "Starting API service..."
    systemctl start outage-dashboard-api.service

    log_info "Starting frontend service..."
    systemctl start outage-dashboard-frontend.service

    log_info "Starting auto-processing timer..."
    systemctl start outage-auto-process.timer

    log_info "Restarting nginx..."
    systemctl restart nginx

    sleep 2

    # Check service status
    log_info "Checking service status..."
    systemctl status outage-dashboard-api.service --no-pager -l || true
    systemctl status outage-dashboard-frontend.service --no-pager -l || true
    systemctl status outage-auto-process.timer --no-pager -l || true

    log_success "All services started"
}

print_summary() {
    print_header "Installation Complete!"

    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')

    echo -e "${GREEN}✓ Property Outage Dashboard is now running!${NC}"
    echo ""
    echo "Access the dashboard:"
    echo -e "  ${BLUE}http://$SERVER_IP${NC}"
    echo -e "  ${BLUE}http://localhost${NC} (from this server)"
    echo ""
    echo "Service Management:"
    echo "  Check API status:      sudo systemctl status outage-dashboard-api"
    echo "  Check frontend status: sudo systemctl status outage-dashboard-frontend"
    echo "  Check auto-processing: sudo systemctl status outage-auto-process.timer"
    echo "  View API logs:         sudo journalctl -u outage-dashboard-api -f"
    echo "  View frontend logs:    sudo journalctl -u outage-dashboard-frontend -f"
    echo ""
    echo "Data Management:"
    echo "  Place CSV files in:    $INSTALL_DIR/inputs/"
    echo "  Auto-processing runs:  Every 6 hours (00:00, 06:00, 12:00, 18:00)"
    echo "  View processing logs:  tail -f $INSTALL_DIR/logs/auto-process.log"
    echo ""
    echo "Next Steps:"
    if [ -z "$BACKUP_FILE" ]; then
        echo "  1. Place your CSV data files in: $INSTALL_DIR/inputs/"
        echo "  2. Wait for auto-processing or run manually: $INSTALL_DIR/auto-process-data.sh"
    else
        echo "  ✓ Database restored from backup"
    fi
    echo ""
    echo "For backup/restore instructions, see: EMERGENCY_DEPLOYMENT.md"
    echo ""
}

#############################################################################
# Main Installation Flow
#############################################################################

main() {
    print_header "EMERGENCY DEPLOYMENT - Property Outage Dashboard"

    log_info "Starting emergency installation on Ubuntu..."
    log_info "Install directory: $INSTALL_DIR"
    log_info "Application user: $APP_USER"

    check_root
    check_ubuntu

    # Confirm before proceeding
    echo ""
    log_warn "This will install system packages and configure services."
    read -p "Continue with installation? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi

    # Run installation steps
    install_system_dependencies
    setup_application
    setup_systemd_services
    configure_nginx
    configure_firewall
    restore_backup
    start_services
    print_summary

    log_success "Emergency deployment completed successfully!"
}

# Run main function
main "$@"
