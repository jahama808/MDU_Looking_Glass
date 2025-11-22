# MDU Performance Dashboard

A comprehensive web-based dashboard for monitoring and analyzing property outages across MDU (Multi-Dwelling Unit) networks. This application tracks outages by property, network, xPON shelf, and 7x50 router equipment, providing real-time alerts for property-wide outages.

## Features

- **Property Outage Tracking**: Monitor outages across all properties with detailed statistics
- **Network-Level Analysis**: View outage data for individual networks
- **Equipment Monitoring**: Track xPON shelves and 7x50 routers and their associated properties
- **Property-Wide Outage Alerts**: Automatic detection when ≥90% of networks are affected
- **Interactive Dashboards**: Visualize outage patterns with charts and graphs
- **Equipment Relationships**: See which MDUs are connected to specific network equipment
- **Hourly Trend Analysis**: Track outage patterns over time
- **7-Day Rolling Window**: Maintains outage data for the past 7 days automatically
- **Automated Data Processing**: Monitors `inputs/` directory and processes new files every 6 hours
- **Archive Management**: Automatically archives processed files with timestamps
- **Emergency Deployment**: Complete backup and restore system for disaster recovery

## Architecture

### Backend (Python/Flask)
- **Flask REST API** serving outage data
- **SQLite Database** for efficient data storage and querying
- **Data Processing Pipeline** to ingest connectivity and discovery data

### Frontend (React/Vite)
- **React 18** for modern UI components
- **React Router** for navigation
- **Recharts** for data visualization
- **Axios** for API communication

## Prerequisites

### Required Software

- **Python 3.8+** - Backend runtime
- **Node.js 16+** - Frontend build tool and runtime
- **npm** - Node package manager

### System Requirements

- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 500MB for application + space for database
- **OS**: Linux, macOS, or Windows

## Quick Start

### 1. Extract the Archive

```bash
unzip property-outage-dashboard.zip
cd property-outage-dashboard
```

### 2. Run the Installation Script

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
- Check for required software (Python, Node.js)
- Create a Python virtual environment
- Install all Python dependencies
- Install all Node.js dependencies
- Create start scripts
- Optionally process your data files if found

### 3. Add Your Data Files

Place your CSV files in the project directory:
- `wan_connectivity-YYYY-MM-DD.csv` - WAN connectivity outage data
- `Eero Discovery Details - YYYY-MM-DD HHMMSS.csv` - Eero network discovery data

### 4. Process the Data

**Linux/Mac:**
```bash
source venv/bin/activate
python process_property_outages_db.py \
  --outages-file network_outages-2025-11-06.csv \
  --discovery-file "Eero Discovery Details - 2025-11-04 081045.csv"
```

**Windows:**
```cmd
call venv\Scripts\activate.bat
python process_property_outages_db.py --outages-file network_outages-2025-11-06.csv --discovery-file "Eero Discovery Details - 2025-11-04 081045.csv"
```

### 5. Start the Application

**Linux/Mac:**
```bash
./start-all.sh
```

**Windows:**
```cmd
start-all.bat
```

Access the dashboard at: **http://localhost:5173**

## Manual Setup (Advanced)

If you prefer to set up components individually:

### Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install flask flask-cors pandas requests

# Start the API server
python api_server.py
```

The API will be available at: **http://localhost:5000**

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: **http://localhost:5173**

## API Endpoints

### Properties
- `GET /api/properties` - List all properties with outages
- `GET /api/property/<id>` - Get property details
- `GET /api/property/<id>/hourly` - Hourly outage data for property
- `GET /api/property/<id>/networks` - Networks for property

### Networks
- `GET /api/network/<id>` - Get network details
- `GET /api/network/<id>/hourly` - Hourly outage data for network

### Equipment
- `GET /api/xpon-shelves` - List all xPON shelves
- `GET /api/xpon-shelf/<id>` - xPON shelf details and associated properties
- `GET /api/7x50s` - List all 7x50 routers
- `GET /api/7x50/<id>` - 7x50 router details and associated properties

### Monitoring
- `GET /api/property-wide-outages` - Properties with property-wide outages (last 24h)
- `GET /api/stats` - Overall statistics

## Configuration

### Making the Application Accessible to Other Users

#### Local Network Access

The application is configured to be accessible on your local network:

1. **Backend** - Already configured to listen on all interfaces (0.0.0.0)
2. **Frontend** - Update `frontend/vite.config.js`:
   ```javascript
   server: {
     host: '0.0.0.0',
     port: 5173,
     // ...
   }
   ```

3. **Firewall** - Allow incoming connections:
   ```bash
   # Linux (ufw)
   sudo ufw allow 5000/tcp
   sudo ufw allow 5173/tcp
   
   # Linux (firewalld)
   sudo firewall-cmd --add-port=5000/tcp --permanent
   sudo firewall-cmd --add-port=5173/tcp --permanent
   sudo firewall-cmd --reload
   ```

4. **Access** - Other users can access via your IP:
   ```
   http://YOUR_IP_ADDRESS:5173
   ```

#### Internet Access

For external access, consider:
- **Port Forwarding** - Configure router to forward port 5173
- **Cloud Deployment** - Deploy to AWS, DigitalOcean, etc.
- **Tunneling** - Use ngrok for temporary access

### Database Location

By default, the database is created at: `./output/outages.db`

To specify a custom location:
```bash
python process_property_outages_db.py \
  --connectivity-file <file> \
  --discovery-file <file> \
  --database /path/to/custom/location.db
```

Update `api_server.py` to point to the new location:
```python
DATABASE = os.environ.get('OUTAGES_DB', '/path/to/custom/location.db')
```

## Data Processing

### Input Files

**Network Outages CSV** - Must contain:
- `network_id` - Unique network identifier
- `start_time` - Outage start timestamp
- `end_time` - Outage end timestamp
- `duration` - Outage duration
- Location data (city, region, country_name, latitude, longitude)

**Eero Discovery CSV** - Must contain:
- `MDU Name` - Property name
- `Eero Network ID` - Network identifier
- `Street Address` - Property address
- `Subloc` - Sub-location
- `Customer Name` - Customer name
- `Equip Name` - Equipment name (format: ONT-SHELFNAME-##-##-##-##)
- `7x50` - 7x50 router name

### Processing Script

```bash
python process_property_outages_db.py \
  --outages-file <network-outages-file> \
  --discovery-file <discovery-file> \
  [--database <db-file>] \
  [--mode {append,rebuild}]
```

The script will:
1. Validate input files
2. Process outage data
3. Extract equipment information (xPON shelves and 7x50 routers)
4. Calculate statistics
5. Create the SQLite database

### Automated Processing (Recommended)

The dashboard includes an automated processing system that monitors the `inputs/` directory and processes new files every 6 hours.

**Setup on Linux/Mac:**
```bash
cd systemd
sudo ./install-systemd.sh
```

**Setup on Windows:**
```powershell
# Run as Administrator
.\install-scheduled-task.ps1
```

**Using Automated Processing:**
1. Copy your CSV files to the `inputs/` directory:
   ```bash
   cp network_outages-2025-11-08.csv inputs/
   cp "Eero Discovery Details - 2025-11-08 120000.csv" inputs/
   ```

2. The system automatically:
   - Processes files every 6 hours (00:00, 06:00, 12:00, 18:00)
   - Updates the database
   - Moves processed files to `inputs_already_read/<timestamp>/`
   - Logs activity to `logs/auto-process.log`

**Manual trigger (without waiting for schedule):**
```bash
# Linux/Mac
./auto-process-data.sh

# Windows
auto-process-data.bat
```

For detailed setup instructions:
- Linux/Mac: See [systemd/README.md](systemd/README.md)
- Windows: See [WINDOWS_AUTOMATION.md](WINDOWS_AUTOMATION.md)
- General instructions: See [UPDATE_DATA.md](UPDATE_DATA.md)

## Emergency Deployment & Disaster Recovery

The dashboard includes a complete backup and emergency deployment system for quick recovery in case of server failure.

### Creating Backups

**Automated Daily Backups (Recommended):**
```bash
# Set up daily backup at 2 AM
crontab -e
# Add: 0 2 * * * /path/to/outage-dashboard/create-backup.sh
```

**Manual Backup:**
```bash
./create-backup.sh
# Creates: backups/outage-dashboard-backup-YYYY-MM-DD_HHMMSS.tar.gz
```

### Emergency Deployment to New Ubuntu Server

**Quick Recovery (5 minutes):**

```bash
# 1. On old/backup server - create backup
./create-backup.sh

# 2. Copy to new server
scp backups/outage-dashboard-backup-*.tar.gz user@new-server:/tmp/

# 3. On new server - extract and deploy
mkdir outage-dashboard && cd outage-dashboard
tar -xzf /tmp/outage-dashboard-backup-*.tar.gz
sudo ./emergency-install.sh

# 4. Done! Access at http://NEW_SERVER_IP
```

The emergency install script automatically:
- ✓ Installs all system dependencies (Python, Node.js, Nginx)
- ✓ Sets up the application and all services
- ✓ Configures systemd for automatic startup
- ✓ Sets up automated data processing
- ✓ Configures firewall and reverse proxy
- ✓ Starts all services

**For detailed instructions:**
- Quick reference: See [EMERGENCY_QUICK_START.txt](EMERGENCY_QUICK_START.txt)
- Complete guide: See [EMERGENCY_DEPLOYMENT.md](EMERGENCY_DEPLOYMENT.md)

**What gets backed up:**
- Database (all outage data)
- Application code
- Configuration files
- Processing logs
- Archived data

## Troubleshooting

### Common Issues

**API Connection Errors**
- Ensure the Flask server is running: `python api_server.py`
- Check if port 5000 is in use: `lsof -i:5000` (Linux/Mac) or `netstat -ano | findstr :5000` (Windows)
- Verify firewall settings

**Frontend Not Loading**
- Ensure Node.js server is running: `npm run dev` in frontend directory
- Check if port 5173 is in use
- Clear browser cache

**Database Errors**
- Verify database file exists: `ls -la output/outages.db`
- Re-run data processing script
- Check CSV file formats

**Module Not Found Errors**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install flask flask-cors pandas`

**Equipment Page Empty**
- Database needs to be regenerated with new schema
- Run: `python process_property_outages_db.py --connectivity-file <file> --discovery-file <file>`

### Logs

Check console output for detailed error messages:
- **Backend**: Terminal where `api_server.py` is running
- **Frontend**: Terminal where `npm run dev` is running
- **Browser**: Developer Console (F12)

## Project Structure

```
property-outage-dashboard/
├── api_server.py                    # Flask API server
├── process_property_outages_db.py   # Data processing script
├── install.sh                       # Linux/Mac installer
├── install.bat                      # Windows installer
├── start-all.sh                     # Start all services (Linux/Mac)
├── start-all.bat                    # Start all services (Windows)
├── start-backend.sh                 # Start API only (Linux/Mac)
├── start-backend.bat                # Start API only (Windows)
├── start-frontend.sh                # Start frontend only (Linux/Mac)
├── start-frontend.bat               # Start frontend only (Windows)
├── README.md                        # This file
├── output/
│   └── outages.db                   # SQLite database (created after processing)
├── frontend/
│   ├── package.json                 # Node.js dependencies
│   ├── vite.config.js              # Vite configuration
│   ├── src/
│   │   ├── App.jsx                  # Main application component
│   │   ├── main.jsx                 # Entry point
│   │   └── components/
│   │       ├── Dashboard.jsx        # Main dashboard
│   │       ├── PropertyList.jsx     # Property list view
│   │       ├── PropertyDetail.jsx   # Property details
│   │       ├── NetworkDetail.jsx    # Network details
│   │       ├── EquipmentView.jsx    # Equipment list (xPON/7x50)
│   │       ├── XponShelfDetail.jsx  # xPON shelf details
│   │       └── Router7x50Detail.jsx # 7x50 router details
│   └── public/                      # Static assets
└── venv/                            # Python virtual environment (created by installer)
```

## Development

### Adding New Features

1. **Backend**: Add new routes to `api_server.py`
2. **Database**: Modify schema in `process_property_outages_db.py`
3. **Frontend**: Create new components in `frontend/src/components/`

### Building for Production

```bash
cd frontend
npm run build
```

Built files will be in `frontend/dist/`

For production deployment, consider:
- Using a production WSGI server (Gunicorn, uWSGI)
- Serving frontend with Nginx or Apache
- Using a production database (PostgreSQL, MySQL)

## License

This is proprietary software for internal use.

## Support

For issues or questions, contact the development team.

## Version History

### v1.0.1 (2025-11-14)
- **Critical Bug Fix**: Fixed data retention issue where networks without outages were incorrectly deleted
- **Enhancement**: Added `requests` module to requirements for API download functionality
- Database now correctly stores ALL networks from discovery file, not just those with outages
- Networks with speedtest data but no outages are now properly retained
- Ensures accurate "passing" vs "failing" network counts on speedtest pages

### v1.0.0 (2025-01-07)
- Initial release
- Property and network outage tracking
- xPON shelf and 7x50 router monitoring
- Property-wide outage alerts
- Interactive dashboard with visualizations
