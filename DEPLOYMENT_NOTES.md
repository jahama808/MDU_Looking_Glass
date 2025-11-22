# Deployment Notes

## Quick Deployment Guide

This document provides step-by-step instructions for deploying the MDU Performance Dashboard to a new machine.

## Pre-Deployment Checklist

Before deploying, ensure you have:
- [ ] Python 3.8 or higher installed
- [ ] Node.js 16 or higher installed
- [ ] npm installed
- [ ] Your CSV data files (wan_connectivity and Eero Discovery)
- [ ] Sufficient disk space (minimum 500MB + data size)

## Deployment Steps

### Step 1: Transfer Files

Transfer the `property-outage-dashboard.zip` file to the target machine using one of these methods:
- USB drive
- SCP: `scp property-outage-dashboard.zip user@remote:/path/to/destination/`
- SFTP client (FileZilla, WinSCP, etc.)
- Cloud storage (Google Drive, Dropbox, etc.)

### Step 2: Extract Archive

**Linux/Mac:**
```bash
unzip property-outage-dashboard.zip
cd property-outage-dashboard
```

**Windows:**
- Right-click the ZIP file
- Select "Extract All..."
- Choose destination folder
- Open Command Prompt in the extracted folder

### Step 3: Run Installer

**Linux/Mac:**
```bash
chmod +x install.sh
./install.sh
```

**Windows:**
```cmd
install.bat
```

The installer will:
1. Check for Python 3 and Node.js
2. Create a Python virtual environment
3. Install Python dependencies (flask, flask-cors, pandas)
4. Install Node.js dependencies (~200MB)
5. Create start scripts
6. Optionally process data files if found

**Installation Time:** 3-5 minutes (depending on internet speed)

### Step 4: Add Data Files

If you didn't include data files in the ZIP:

1. Copy your CSV files to the project directory
2. Process the data:

**Linux/Mac:**
```bash
source venv/bin/activate
python process_property_outages_db.py \
  --outages-file network_outages-YYYY-MM-DD.csv \
  --discovery-file "Eero Discovery Details - YYYY-MM-DD HHMMSS.csv"
```

**Windows:**
```cmd
call venv\Scripts\activate.bat
python process_property_outages_db.py --outages-file network_outages-YYYY-MM-DD.csv --discovery-file "Eero Discovery Details - YYYY-MM-DD HHMMSS.csv"
```

### Step 5: Start the Application

**Linux/Mac:**
```bash
./start-all.sh
```

**Windows:**
```cmd
start-all.bat
```

The application will start both:
- Backend API on port 5000
- Frontend on port 5173

### Step 6: Verify Installation

1. Open a web browser
2. Navigate to: `http://localhost:5173`
3. You should see the dashboard
4. Check that data is loading correctly

## Network Access Configuration

### Enable Local Network Access

To allow other users on the same network to access the dashboard:

#### 1. Find Your IP Address

**Linux:**
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
# OR
hostname -I
```

**Mac:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```cmd
ipconfig
```

Look for "IPv4 Address" under your active network adapter.

#### 2. Configure Firewall

**Linux (ufw):**
```bash
sudo ufw allow 5000/tcp
sudo ufw allow 5173/tcp
sudo ufw reload
```

**Linux (firewalld):**
```bash
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --add-port=5173/tcp --permanent
sudo firewall-cmd --reload
```

**Windows:**
```
1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" > "New Rule"
4. Select "Port" > Next
5. Enter ports: 5000, 5173
6. Allow the connection
7. Apply to all profiles
8. Name: "MDU Performance Dashboard"
```

**Mac:**
```
System Preferences > Security & Privacy > Firewall > Firewall Options
Add Python and Node to allowed apps
```

#### 3. Share Access URL

Other users can access the dashboard at:
```
http://YOUR_IP_ADDRESS:5173
```

Example: `http://192.168.1.100:5173`

## Production Deployment

For production use:

### 1. Update Configuration

Edit `api_server.py` line 288:
```python
app.run(debug=False, host='0.0.0.0', port=5000)  # Disable debug mode
```

### 2. Use Production Server

Instead of Flask development server, use Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### 3. Build Frontend for Production

```bash
cd frontend
npm run build
```

Serve the `dist/` directory with Nginx or Apache.

### 4. Setup as System Service

**Linux (systemd):**

Create `/etc/systemd/system/outage-dashboard-api.service`:
```ini
[Unit]
Description=MDU Performance Dashboard API
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/property-outage-dashboard
Environment="PATH=/path/to/property-outage-dashboard/venv/bin"
ExecStart=/path/to/property-outage-dashboard/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 api_server:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable outage-dashboard-api
sudo systemctl start outage-dashboard-api
```

## Updating Data

To update with new data files:

1. Stop the application (Ctrl+C or close windows)
2. Run the processing script with new files
3. Restart the application

The database will be completely rebuilt with the new data.

## Troubleshooting

### Port Already in Use

**Find process using port:**
```bash
# Linux/Mac
lsof -i:5000
lsof -i:5173

# Windows
netstat -ano | findstr :5000
netstat -ano | findstr :5173
```

**Kill the process or change ports in configuration**

### Permission Denied (Linux/Mac)

```bash
chmod +x install.sh
chmod +x start-all.sh
chmod +x start-backend.sh
chmod +x start-frontend.sh
```

### Python Virtual Environment Issues

```bash
# Remove and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install flask flask-cors pandas
```

### Node Modules Issues

```bash
# Remove and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Backup Strategy

### What to Backup

1. **Data Files** (Input CSVs)
2. **Database** (`output/outages.db`)
3. **Configuration** (if customized)

### Backup Commands

```bash
# Create backup directory
mkdir -p backups/$(date +%Y-%m-%d)

# Backup database
cp output/outages.db backups/$(date +%Y-%m-%d)/

# Backup data files
cp *.csv backups/$(date +%Y-%m-%d)/
```

## Migration to New Server

1. Backup current installation (database + data files)
2. Transfer ZIP and backup to new server
3. Run installer on new server
4. Restore database to `output/outages.db`
5. Start application

## Security Considerations

- **Change default ports** if deploying to internet
- **Use HTTPS** for external access (reverse proxy with Nginx + Let's Encrypt)
- **Implement authentication** for production (not included in current version)
- **Restrict firewall** to only allow necessary IPs
- **Keep dependencies updated** regularly

## Performance Tuning

### For Large Datasets (>10,000 properties)

1. **Increase Gunicorn workers:**
   ```bash
   gunicorn -w 8 -b 0.0.0.0:5000 api_server:app
   ```

2. **Enable database optimization:**
   ```python
   # In api_server.py, add after connection:
   conn.execute("PRAGMA journal_mode=WAL")
   conn.execute("PRAGMA synchronous=NORMAL")
   ```

3. **Add caching** for frequently accessed data

## Contact

For deployment assistance, contact the development team.
