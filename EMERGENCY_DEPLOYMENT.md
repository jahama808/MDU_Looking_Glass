# Emergency Deployment Guide - MDU Performance Dashboard

This guide provides instructions for creating backups and performing emergency deployments to a new server.

## Table of Contents
- [Quick Start](#quick-start)
- [Creating a Backup](#creating-a-backup)
- [Emergency Restore](#emergency-restore)
- [Manual Deployment](#manual-deployment)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Create Backup (Current Server)
```bash
cd /path/to/mdu-dashboard
./emergency-backup.sh
```

### Restore on New Server
```bash
# 1. Copy backup to new server
scp backups/mdu-dashboard-*.tar.gz user@new-server:/tmp/

# 2. On new server, extract and restore
cd /tmp
tar -xzf mdu-dashboard-*.tar.gz
cd mdu-dashboard-*
sudo ./emergency-restore.sh
```

---

## Creating a Backup

The `emergency-backup.sh` script creates a comprehensive backup of your entire MDU Performance Dashboard installation.

### What Gets Backed Up

- **Database**: `property_outages.db` (all network outages and properties)
- **Cron Jobs**: Exported crontab configuration
- **Application Code**: All Python scripts, shell scripts, batch files
- **Frontend**: React application (without node_modules for smaller size)
- **Recent Logs**: Last 30 days of application logs
- **Processing Reports**: Last 30 days of processing reports
- **Archived Data**: Last 7 days of archived input files
- **Configuration**: `.env` file (if exists) with sensitive credentials

### Creating a Backup

```bash
# Run from the application directory
./emergency-backup.sh

# Or specify a custom backup location
./emergency-backup.sh /path/to/backup/location
```

### Backup File Format

- **Naming**: `mdu-dashboard-YYYY-MM-DD_HHMMSS.tar.gz`
- **Location**: `./backups/` (default) or custom directory
- **Retention**: Automatically keeps last 14 days of backups
- **Compression**: Gzip compressed tar archive

### Example Output

```
============================================================
MDU Performance Dashboard - COMPREHENSIVE BACKUP
============================================================

[1/7] Backing up database...
✓ Database backed up

[2/7] Backing up cron jobs...
✓ Cron jobs backed up

[3/7] Backing up environment and configuration...
✓ .env file backed up

[4/7] Backing up application code...
✓ Application code backed up

[5/7] Backing up frontend...
✓ Frontend backed up

[6/7] Backing up data and logs...
✓ Data and logs backed up

[7/7] Creating backup metadata...
✓ Metadata created

============================================================
BACKUP COMPLETE!
============================================================

Backup Details:
  File: /path/to/backups/mdu-dashboard-2025-11-18_120000.tar.gz
  Size: 125M
  Database: 89M
```

---

## Emergency Restore

The `emergency-restore.sh` script automates the complete restoration of your MDU Performance Dashboard on a new server.

### Prerequisites

- Ubuntu/Debian or RedHat/CentOS/Fedora server
- Root or sudo access
- Internet connection (for installing dependencies)

### Supported Operating Systems

- Ubuntu 18.04+
- Debian 9+
- CentOS 7+
- RHEL 7+
- Fedora 30+

### Installation Steps

#### 1. Transfer Backup to New Server

```bash
# From your local machine or current server
scp backups/mdu-dashboard-2025-11-18_120000.tar.gz user@new-server:/tmp/
```

#### 2. Extract Backup

```bash
# On the new server
cd /tmp
tar -xzf mdu-dashboard-2025-11-18_120000.tar.gz
cd mdu-dashboard-2025-11-18_120000
```

#### 3. Run Restore Script

**Basic restore (default options):**
```bash
sudo ./emergency-restore.sh
```

**Custom installation directory:**
```bash
sudo ./emergency-restore.sh --install-dir /home/user/mdu-dashboard
```

**Custom ports:**
```bash
sudo ./emergency-restore.sh --api-port 8080 --frontend-port 8081
```

**Without systemd services (manual start):**
```bash
sudo ./emergency-restore.sh --no-services
```

### Restore Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `--install-dir PATH` | Installation directory | `/opt/mdu-dashboard` |
| `--api-port PORT` | API server port | `5000` |
| `--frontend-port PORT` | Frontend server port | `3000` |
| `--no-services` | Don't create systemd services | Services created |
| `--help` | Show help message | - |

### What the Restore Script Does

1. **Detects OS** and installs required system dependencies
2. **Creates installation directory** (default: `/opt/mdu-dashboard`)
3. **Copies all application files** from backup
4. **Sets up Python virtual environment** and installs dependencies
5. **Builds frontend** for production
6. **Restores database** (`property_outages.db`)
7. **Restores cron jobs** (with path updates)
8. **Sets file permissions** appropriately
9. **Creates systemd services** for API and frontend
10. **Starts services** and verifies they're running
11. **Displays access information** and next steps

### Example Restore Output

```
============================================================
MDU Performance Dashboard - EMERGENCY RESTORE
============================================================

Configuration:
  Installation directory: /opt/mdu-dashboard
  API port: 5000
  Frontend port: 3000
  Create systemd services: true

[1/11] Detecting operating system...
✓ Detected: Ubuntu 22.04.3 LTS

[2/11] Installing system dependencies...
✓ Dependencies installed (apt)

[3/11] Creating installation directory...
✓ Created /opt/mdu-dashboard

[4/11] Copying application files...
✓ Application files copied

[5/11] Setting up Python virtual environment...
✓ Python dependencies installed

[6/11] Setting up frontend...
✓ Frontend dependencies installed
✓ Frontend built for production

[7/11] Restoring database...
✓ Database restored (property_outages.db)
  Database size: 89M

[8/11] Restoring cron jobs...
✓ Cron jobs installed

[9/11] Setting file permissions...
✓ Permissions configured

[10/11] Creating systemd services...
✓ Created mdu-api.service
✓ Created mdu-frontend.service
✓ Services enabled

[11/11] Starting services...
✓ API server started
✓ Frontend server started

============================================================
RESTORE COMPLETE!
============================================================

Access the application:
  http://192.168.1.100:3000
  http://localhost:3000
```

---

## Manual Deployment

If you prefer not to use the automated restore script, here are manual deployment instructions.

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nodejs npm sqlite3 rsync
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip nodejs npm sqlite rsync
```

### 2. Extract Backup

```bash
cd /opt
sudo tar -xzf /tmp/mdu-dashboard-*.tar.gz
sudo mv mdu-dashboard-* mdu-dashboard
cd mdu-dashboard
```

### 3. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. Restore Cron Jobs

```bash
# Edit paths in crontab.txt to match new installation
nano crontab.txt

# Install crontab
crontab crontab.txt
```

### 6. Start Services Manually

**Terminal 1 - API Server:**
```bash
cd /opt/mdu-dashboard
source venv/bin/activate
python3 api_server.py
```

**Terminal 2 - Frontend:**
```bash
cd /opt/mdu-dashboard/frontend/dist
python3 -m http.server 3000
```

### 7. Create Systemd Services (Optional)

**API Service (`/etc/systemd/system/mdu-api.service`):**
```ini
[Unit]
Description=MDU Performance Dashboard API Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/mdu-dashboard
Environment="PATH=/opt/mdu-dashboard/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/mdu-dashboard/venv/bin/python3 /opt/mdu-dashboard/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service (`/etc/systemd/system/mdu-frontend.service`):**
```ini
[Unit]
Description=MDU Performance Dashboard Frontend
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/mdu-dashboard/frontend/dist
ExecStart=/usr/bin/python3 -m http.server 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mdu-api mdu-frontend
sudo systemctl start mdu-api mdu-frontend
```

---

## Verification

### Check Services

```bash
# Check service status
sudo systemctl status mdu-api
sudo systemctl status mdu-frontend

# View logs
sudo journalctl -u mdu-api -f
sudo journalctl -u mdu-frontend -f
```

### Check Database

```bash
cd /opt/mdu-dashboard
sqlite3 property_outages.db

# Check outage count
SELECT COUNT(*) FROM outages;

# Check network count
SELECT COUNT(*) FROM networks;

# Check recent outages
SELECT * FROM outages ORDER BY last_seen DESC LIMIT 10;

.quit
```

### Check Cron Jobs

```bash
# List cron jobs
crontab -l

# Check cron logs
grep CRON /var/log/syslog
```

### Access Application

Open your browser and navigate to:
```
http://your-server-ip:3000
```

Default credentials (if not changed):
- Username: `admin`
- Password: (whatever was set in your original installation)

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u mdu-api -n 50
sudo journalctl -u mdu-frontend -n 50
```

**Check port conflicts:**
```bash
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :3000
```

**Manually test API:**
```bash
cd /opt/mdu-dashboard
source venv/bin/activate
python3 api_server.py
# Look for errors in output
```

### Database Issues

**Check database permissions:**
```bash
ls -la /opt/mdu-dashboard/property_outages.db
sudo chown your-user:your-user /opt/mdu-dashboard/property_outages.db
```

**Test database connection:**
```bash
sqlite3 /opt/mdu-dashboard/property_outages.db "SELECT COUNT(*) FROM outages;"
```

### Frontend Not Loading

**Check if build exists:**
```bash
ls -la /opt/mdu-dashboard/frontend/dist/
```

**Rebuild frontend:**
```bash
cd /opt/mdu-dashboard/frontend
npm install
npm run build
```

### Cron Jobs Not Running

**Check cron service:**
```bash
sudo systemctl status cron  # Ubuntu/Debian
sudo systemctl status crond  # CentOS/RHEL
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog | tail -20
```

**Verify paths in crontab:**
```bash
crontab -l
# Make sure all paths point to /opt/mdu-dashboard
```

### Python Module Missing

**Reinstall dependencies:**
```bash
cd /opt/mdu-dashboard
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Production Recommendations

### 1. Use a Reverse Proxy

Set up nginx or Apache as a reverse proxy for better security and performance.

**Example nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Configure Firewall

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. Set Up SSL Certificates

Use Let's Encrypt for free SSL certificates:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 4. Regular Backups

Add a daily backup cron job:
```bash
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /opt/mdu-dashboard/emergency-backup.sh
```

### 5. Monitoring

Set up basic monitoring:
```bash
# Install monitoring tools
sudo apt-get install htop iotop

# Monitor service health
watch -n 5 'systemctl status mdu-api mdu-frontend'
```

---

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u mdu-api -n 100`
2. Review the processing reports in `processing_reports/`
3. Check cron logs for scheduled job failures

---

## Backup Retention Policy

The emergency backup script automatically:
- Creates timestamped backups
- Keeps the last 14 days of backups
- Deletes older backups automatically

To change retention:
```bash
# Edit emergency-backup.sh line 203
find "$BACKUP_DIR" -name "mdu-dashboard-*.tar.gz" -mtime +30 -delete  # 30 days
```

---

**Last Updated:** 2025-11-18
**Version:** 2.0
