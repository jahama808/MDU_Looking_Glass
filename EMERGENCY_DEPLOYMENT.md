# Emergency Deployment Guide

This guide provides step-by-step instructions for deploying the Property Outage Dashboard to a new Ubuntu server in an emergency scenario (server crash, hardware failure, migration, etc.).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [What Gets Deployed](#what-gets-deployed)
4. [Creating Regular Backups](#creating-regular-backups)
5. [Restoring from Backup](#restoring-from-backup)
6. [Manual Deployment Steps](#manual-deployment-steps)
7. [Post-Deployment Checklist](#post-deployment-checklist)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### New Server Requirements

- **OS**: Ubuntu 20.04 LTS or later (recommended: Ubuntu 22.04 LTS)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 10GB free space minimum
- **Network**: Internet connection (for initial setup)
- **Access**: Root or sudo privileges

### Files You Need

1. **Application backup** (created with `create-backup.sh`)
2. **SSH access** to the new server
3. **Optional**: Database backup if you have a separate one

---

## Quick Start (5 Minutes)

This is the fastest way to deploy in an emergency.

### On Your Current/Backup Server

```bash
# 1. Create a backup (if the server is still accessible)
./create-backup.sh

# This creates: backups/outage-dashboard-backup-YYYY-MM-DD_HHMMSS.tar.gz
```

### On the New Ubuntu Server

```bash
# 1. Copy the backup to the new server
scp backups/outage-dashboard-backup-*.tar.gz user@new-server:/tmp/

# 2. SSH into the new server
ssh user@new-server

# 3. Extract the backup
cd ~
mkdir outage-dashboard
cd outage-dashboard
tar -xzf /tmp/outage-dashboard-backup-*.tar.gz

# 4. Run the emergency install script
sudo ./emergency-install.sh

# 5. That's it! The dashboard should now be running
```

Access the dashboard at: `http://NEW_SERVER_IP`

---

## What Gets Deployed

The emergency installation script automatically:

### System Components
- ✓ Python 3.8+ and pip
- ✓ Node.js 18.x LTS and npm
- ✓ Nginx (reverse proxy)
- ✓ SQLite3
- ✓ Git and curl

### Application Components
- ✓ Flask API server (runs on port 5000)
- ✓ React frontend (builds and serves on port 5173)
- ✓ Database with all outage data
- ✓ All Python dependencies
- ✓ All Node.js dependencies

### Services & Automation
- ✓ Systemd service for API (auto-starts on boot)
- ✓ Systemd service for frontend (auto-starts on boot)
- ✓ Auto-processing timer (runs every 6 hours)
- ✓ Nginx reverse proxy configuration

### Firewall Configuration
- ✓ SSH (port 22)
- ✓ HTTP (port 80)
- ✓ HTTPS (port 443)

---

## Creating Regular Backups

**IMPORTANT**: Create backups regularly (daily recommended) to ensure quick recovery.

### Automated Backups (Recommended)

Set up a daily cron job:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /path/to/outage-dashboard/create-backup.sh /path/to/backup/location

# For example:
0 2 * * * /home/user/outage-dashboard/create-backup.sh /mnt/backup/outage-dashboard
```

### Manual Backup

```bash
cd /path/to/outage-dashboard
./create-backup.sh [optional-backup-directory]

# Example:
./create-backup.sh /mnt/external-drive/backups
```

### What Gets Backed Up

**Full Backup** (complete application):
- Database (`output/outages.db`)
- All application code
- Frontend code
- Configuration files
- Processing logs
- Archived data

**Essential Backup** (database only):
- Database (`output/outages.db`)
- Processing logs (`logs/`)
- Archived data (`inputs_already_read/`)

### Backup Retention

- Backups older than 7 days are automatically deleted
- Modify retention in `create-backup.sh` if needed

---

## Restoring from Backup

### Full Restore (New Server)

```bash
# 1. Copy application code to new server
scp -r /path/to/outage-dashboard user@new-server:~/

# 2. SSH to new server
ssh user@new-server

# 3. Run emergency install
cd ~/outage-dashboard
sudo ./emergency-install.sh

# Done! Services are now running with your data
```

### Restore Database Only (Existing Installation)

```bash
# 1. Stop services
sudo systemctl stop outage-dashboard-api

# 2. Backup current database (just in case)
cp output/outages.db output/outages.db.backup

# 3. Restore from backup
tar -xzf /path/to/backup.tar.gz output/outages.db

# 4. Restart services
sudo systemctl start outage-dashboard-api
```

---

## Manual Deployment Steps

If you need to understand what the emergency script does, here's the manual process:

### 1. Install System Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python
sudo apt-get install -y python3 python3-pip python3-venv

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install additional tools
sudo apt-get install -y git sqlite3 nginx curl
```

### 2. Set Up Application

```bash
# Copy application files to server
cd ~
mkdir -p outage-dashboard
cd outage-dashboard

# Extract backup or clone repository
tar -xzf /path/to/backup.tar.gz

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask flask-cors pandas

# Install Node.js dependencies and build frontend
cd frontend
npm install
npm run build
cd ..
```

### 3. Create Systemd Services

**API Service:** `/etc/systemd/system/outage-dashboard-api.service`

```ini
[Unit]
Description=Property Outage Dashboard - API Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/outage-dashboard
Environment="PATH=/home/YOUR_USERNAME/outage-dashboard/venv/bin"
ExecStart=/home/YOUR_USERNAME/outage-dashboard/venv/bin/python /home/YOUR_USERNAME/outage-dashboard/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service:** `/etc/systemd/system/outage-dashboard-frontend.service`

```ini
[Unit]
Description=Property Outage Dashboard - Frontend Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/outage-dashboard/frontend/dist
ExecStart=/usr/bin/python3 -m http.server 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start Services:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable outage-dashboard-api outage-dashboard-frontend
sudo systemctl start outage-dashboard-api outage-dashboard-frontend
```

### 4. Configure Nginx

Create `/etc/nginx/sites-available/outage-dashboard`:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/outage-dashboard /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Configure Firewall

```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Post-Deployment Checklist

After deployment, verify everything is working:

### 1. Check Services

```bash
# Check API service
sudo systemctl status outage-dashboard-api
curl http://localhost:5000/api/stats

# Check frontend service
sudo systemctl status outage-dashboard-frontend

# Check auto-processing timer
sudo systemctl status outage-auto-process.timer
sudo systemctl list-timers outage-auto-process.timer
```

### 2. Check Web Access

```bash
# Get server IP
hostname -I

# Access from browser:
# http://YOUR_SERVER_IP
```

### 3. Verify Data

- Open the dashboard in a browser
- Check that properties are showing
- Verify outage counts match expectations
- Check equipment pages (xPON, 7x50)

### 4. Test Auto-Processing

```bash
# Place a test file in inputs/
cp /path/to/test-wan-file.csv inputs/
cp /path/to/test-eero-file.csv inputs/

# Run manual processing test
./auto-process-data.sh

# Check logs
tail -f logs/auto-process.log
```

### 5. Verify Logs

```bash
# API logs
sudo journalctl -u outage-dashboard-api -f

# Frontend logs
sudo journalctl -u outage-dashboard-frontend -f

# Auto-processing logs
tail -f logs/auto-process.log
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check service status and logs
sudo systemctl status outage-dashboard-api
sudo journalctl -u outage-dashboard-api -n 50

# Common issues:
# 1. Port already in use
sudo lsof -i :5000
sudo lsof -i :5173

# 2. Permission issues
sudo chown -R $USER:$USER /path/to/outage-dashboard

# 3. Missing dependencies
source venv/bin/activate
pip install flask flask-cors pandas
```

### Database Not Found

```bash
# Check database exists
ls -la output/outages.db

# If missing, process some data
./auto-process-data.sh
# Or manually:
source venv/bin/activate
python process_property_outages_db.py \
  --outages-file <file> \
  --discovery-file <file>
```

### Nginx 502 Bad Gateway

```bash
# Check backend services are running
sudo systemctl status outage-dashboard-api
sudo systemctl status outage-dashboard-frontend

# Check nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Firewall Blocking Access

```bash
# Check firewall status
sudo ufw status

# Allow HTTP if not already
sudo ufw allow 80/tcp
sudo ufw reload

# Or temporarily disable for testing
sudo ufw disable
```

### Auto-Processing Not Running

```bash
# Check timer is active
sudo systemctl status outage-auto-process.timer

# Check timer schedule
sudo systemctl list-timers outage-auto-process.timer

# Run manually to test
./auto-process-data.sh

# Check logs
tail -f logs/auto-process.log
```

---

## Additional Notes

### Production Hardening (Optional)

For production deployment, consider:

1. **HTTPS/SSL**:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Monitoring**:
   - Set up log rotation
   - Configure monitoring/alerting
   - Set up database backups to external storage

3. **Security**:
   - Change default SSH port
   - Set up fail2ban
   - Regular system updates
   - Restrict API access if needed

### Backup Best Practices

1. **Store backups off-site**
   - Use external storage/cloud
   - Keep at least 3 copies in different locations

2. **Test restores regularly**
   - Perform test restores monthly
   - Document recovery time

3. **Automate everything**
   - Automated daily backups
   - Automated backup verification
   - Alerts if backups fail

### Performance Tuning

For large deployments:

1. **Database**: Consider PostgreSQL instead of SQLite
2. **Frontend**: Use nginx to serve static files directly
3. **API**: Use gunicorn with multiple workers
4. **Caching**: Add Redis for API caching

---

## Support

For issues during emergency deployment:

1. Check service logs: `sudo journalctl -u outage-dashboard-api -f`
2. Check application logs: `tail -f logs/auto-process.log`
3. Review this document's troubleshooting section
4. Check README.md for general documentation

## Emergency Contact Checklist

Keep this information handy for emergencies:

- [ ] Backup location: ____________________
- [ ] Server IP/hostname: ____________________
- [ ] SSH credentials: ____________________
- [ ] Database admin contact: ____________________
- [ ] Last successful backup date: ____________________

---

**Last Updated**: 2025-11-08
**Version**: 1.0
