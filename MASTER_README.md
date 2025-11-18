# Property Outage Analysis System - Complete Guide

> **⚠️ IMPORTANT:** All Python scripts in this system must run inside a virtual environment (venv). Always activate the venv before running any commands!

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [System Overview](#system-overview)
- [Installation](#installation)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Documentation](#documentation)

## 🚀 Quick Start

### First Time Setup

1. **Download all project files** to a directory
2. **Run the installer:**
   ```bash
   # Linux/Mac
   chmod +x install.sh
   ./install.sh
   
   # Windows
   install.bat
   ```
3. **Activate the virtual environment:**
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```
   You should see `(venv)` in your prompt.

4. **Process your data:**
   ```bash
   # Option A: CSV files
   python process_property_outages.py \
     --outages-file wan_connectivity.csv \
     --discovery-file eero_discovery.csv
   
   # Option B: Database (recommended for web apps)
   python process_property_outages_db.py \
     --outages-file wan_connectivity.csv \
     --discovery-file eero_discovery.csv
   ```

5. **When done, deactivate:**
   ```bash
   deactivate
   ```

## 📖 System Overview

This system provides **two backends** for analyzing network outage data:

### 1. File-Based Backend (CSV)
- **Script:** `process_property_outages.py`
- **Output:** Individual CSV files per property
- **Use for:** Simple reporting, exports, email attachments
- **Location:** `./output/property-files/`

### 2. Database Backend (SQLite)
- **Script:** `process_property_outages_db.py`
- **Output:** SQLite database
- **Use for:** Web applications, dynamic queries, dashboards
- **Location:** `./output/outages.db`
- **Bonus:** Includes REST API server (`api_server.py`)

## 🛠️ Installation

### What the installer does:
1. Creates a Python virtual environment (`./venv`)
2. Upgrades pip
3. Installs dependencies (pandas, flask, flask-cors)

### Linux/Mac
```bash
chmod +x install.sh
./install.sh
```

### Windows
```cmd
install.bat
```

### Manual Installation
If the scripts don't work:
```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## 💻 Usage

### Always Start Here!
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### CSV File Processor

Generate individual CSV reports for each property:

```bash
python process_property_outages.py \
  --outages-file network_outages-2025-11-06.csv \
  --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv \
  --output-dir ./output/property-files
```

**Output structure:**
- `00_INDEX.txt` - List of all properties
- `{PROPERTY}_outages.csv` - Individual property report with:
  - Header (property name, totals)
  - Network summary (total outages per network)
  - Aggregated hourly outages (all networks combined)
  - Per-network hourly outages

### Database Processor

Create a SQLite database for web applications:

```bash
python process_property_outages_db.py \
  --outages-file network_outages-2025-11-06.csv \
  --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv \
  --database ./output/outages.db
```

**Database includes:**
- 5 tables: properties, networks, property_hourly_outages, network_hourly_outages, outages
- Indexed for fast queries
- Raw outage records for detailed analysis

### REST API Server

Start a web API to access the database:

```bash
python api_server.py
```

**Endpoints:**
- `GET /api/properties` - List all properties
- `GET /api/property/<id>` - Property details
- `GET /api/property/<id>/hourly` - Hourly outage data
- `GET /api/property/<id>/networks` - Networks in property
- `GET /api/network/<id>` - Network details
- `GET /api/stats` - Overall statistics
- `GET /api/search?q=query` - Search properties

**Test it:**
```bash
# In another terminal
curl http://localhost:5000/api/properties
```

### Deactivate When Done
```bash
deactivate
```

## 📁 File Structure

```
project/
├── process_property_outages.py      # CSV file processor
├── process_property_outages_db.py   # Database processor  
├── api_server.py                    # REST API server
├── requirements.txt                 # Python dependencies
├── install.sh                       # Linux/Mac installer
├── install.bat                      # Windows installer
│
├── README.md                        # This file
├── QUICKSTART.md                    # Quick reference
├── DATABASE_README.md               # Database documentation
├── PROJECT_SUMMARY.md               # Complete system overview
│
├── venv/                            # Virtual environment (created by install)
│   ├── bin/                         # Executables (Linux/Mac)
│   ├── Scripts/                     # Executables (Windows)
│   └── lib/                         # Python packages
│
└── output/
    ├── property-files/              # CSV outputs (if using CSV processor)
    │   ├── 00_INDEX.txt
    │   ├── PROPERTY1_outages.csv
    │   ├── PROPERTY2_outages.csv
    │   └── ...
    └── outages.db                   # SQLite database (if using DB processor)
```

## 📚 Documentation

### Quick Reference
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup and common commands

### Detailed Guides
- **[DATABASE_README.md](DATABASE_README.md)** - Database schema, queries, API examples
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete system architecture

### Help Commands
```bash
# CSV processor help
python process_property_outages.py --help

# Database processor help
python process_property_outages_db.py --help
```

## ⚡ Common Workflows

### Daily Reporting (CSV)
```bash
source venv/bin/activate
python process_property_outages.py \
  --outages-file today_data.csv \
  --discovery-file current_discovery.csv
deactivate
```

### Web Application (Database + API)
```bash
# Terminal 1: Process data
source venv/bin/activate
python process_property_outages_db.py \
  --outages-file data.csv \
  --discovery-file discovery.csv
python api_server.py

# Terminal 2: Run your frontend
cd my-web-app
npm start
```

### Query Database Directly
```bash
source venv/bin/activate
python << EOF
import sqlite3
conn = sqlite3.connect('output/outages.db')
cursor = conn.cursor()
cursor.execute("SELECT property_name, total_outages FROM properties ORDER BY total_outages DESC LIMIT 10")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} outages")
conn.close()
EOF
deactivate
```

## 🐛 Troubleshooting

### "Module not found" errors
**Problem:** Trying to run scripts outside venv
**Solution:** Activate venv first:
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### "Database file not found" (API server)
**Problem:** Database hasn't been created yet
**Solution:** Run database processor first:
```bash
python process_property_outages_db.py \
  --outages-file data.csv \
  --discovery-file discovery.csv
```

### Port 5000 already in use
**Problem:** Another service is using port 5000
**Solution:** Either:
1. Stop the other service
2. Modify `api_server.py` line: `app.run(debug=True, host='0.0.0.0', port=5001)`

### "Permission denied" on install.sh
**Problem:** Script not executable
**Solution:** 
```bash
chmod +x install.sh
```

## 🎯 Best Practices

1. **Always use venv** - Keeps dependencies isolated
2. **Keep venv activated** - While working on the project
3. **Update regularly** - Pull latest CSV files
4. **Backup database** - Before reprocessing data
5. **Use database for web** - More flexible than CSV files
6. **Monitor API logs** - Check terminal for errors

## 🔐 Security Notes

- API has no authentication (add if needed for production)
- Database file is readable by anyone with file access
- CORS is enabled for all origins (restrict in production)
- Don't commit `venv/` or `output/` to git

## 📊 Data Flow

```
CSV Files
    ↓
[Process Scripts] (in venv)
    ↓
CSV Files OR Database
    ↓
[API Server] (in venv, optional)
    ↓
Web Frontend
```

## 🤝 Support

- Check documentation files in this directory
- Run `--help` on any script
- Review error messages carefully

## 📝 License

This system is provided as-is for data analysis purposes.

---

**Remember:** Always activate the virtual environment before running any Python scripts!

```bash
source venv/bin/activate  # You should see (venv) in your prompt
```
