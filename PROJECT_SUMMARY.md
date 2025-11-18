# Property Outage Analysis System - Complete Package

## Overview

This system processes network outage data and provides both file-based and database-based backends for web applications.

## 📦 What's Included

### Data Processing Scripts

1. **process_property_outages.py** - File-based processor
   - Generates individual CSV files for each property
   - Output: `./output/property-files/*.csv`
   - Best for: Simple reporting, CSV exports

2. **process_property_outages_db.py** - Database processor
   - Stores data in SQLite database
   - Output: `./output/outages.db`
   - Best for: Web applications, dynamic querying

### Web API

3. **api_server.py** - REST API server
   - Flask-based REST API
   - Provides JSON endpoints for frontend
   - Runs on http://localhost:5000

### Installation & Setup

4. **install.sh** (Linux/Mac) / **install.bat** (Windows)
   - Automated setup scripts
   - Creates virtual environment
   - Installs all dependencies

5. **requirements.txt**
   - Python dependencies
   - pandas, flask, flask-cors

### Documentation

6. **README.md** - General documentation
7. **DATABASE_README.md** - Database schema and query examples
8. **QUICKSTART.md** - Quick setup guide

## 🚀 Quick Start

### Option 1: File-Based Output (CSV Files)

```bash
# 1. Install
./install.sh  # or install.bat on Windows

# 2. Activate environment
source venv/bin/activate

# 3. Process data
python process_property_outages.py \
  --outages-file wan_connectivity.csv \
  --discovery-file eero_discovery.csv

# 4. Find results
ls output/property-files/
```

### Option 2: Database Backend (Recommended for Web)

```bash
# 1. Install (creates venv and installs dependencies)
./install.sh  # or install.bat on Windows

# 2. Activate environment (REQUIRED for all commands)
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 3. Process data into database (runs in venv)
python process_property_outages_db.py \
  --outages-file wan_connectivity.csv \
  --discovery-file eero_discovery.csv \
  --database output/outages.db

# 4. Start API server (runs in venv)
python api_server.py

# 5. When done, deactivate
deactivate
```

**IMPORTANT:** All Python scripts (file processor, database processor, and API server) must run inside the virtual environment. Always activate the venv first!

## 📊 Data Structure

### File-Based Output

Each property CSV file contains:
- **Header**: Property name, total networks, total outages
- **Network Summary**: Networks ranked by outages
- **Aggregated Hourly Outages**: Total outages per hour (all networks combined)
- **Per-Network Hourly Outages**: Individual network breakdown

### Database Schema

Five tables:
- `properties` - Property-level summaries
- `networks` - Network details
- `property_hourly_outages` - Aggregated hourly data
- `network_hourly_outages` - Per-network hourly data
- `outages` - Raw outage records

## 🌐 API Endpoints

```
GET /api/properties              # List all properties
GET /api/property/<id>           # Property details
GET /api/property/<id>/hourly    # Hourly outage trend
GET /api/property/<id>/networks  # Networks in property
GET /api/network/<id>            # Network details
GET /api/network/<id>/hourly     # Network hourly data
GET /api/stats                   # Overall statistics
GET /api/search?q=<query>        # Search properties
```

## 💡 Use Cases

### For Reporting
Use the file-based processor to generate CSV reports for each property.

### For Web Applications
1. Process data with database processor
2. Start API server
3. Build frontend that queries the API

### For Data Analysis
Query the SQLite database directly using Python, R, or any SQL tool.

## 📁 Project Structure

```
project/
├── process_property_outages.py      # CSV file processor
├── process_property_outages_db.py   # Database processor
├── api_server.py                    # REST API server
├── requirements.txt                 # Python dependencies
├── install.sh                       # Linux/Mac installer
├── install.bat                      # Windows installer
├── README.md                        # Main documentation
├── DATABASE_README.md               # Database documentation
├── QUICKSTART.md                    # Quick start guide
├── venv/                            # Virtual environment (created by install)
└── output/
    ├── property-files/              # CSV outputs (if using file processor)
    │   ├── 00_INDEX.txt
    │   └── *.csv
    └── outages.db                   # SQLite database (if using DB processor)
```

## 🔄 Workflow

### Initial Setup
```bash
# 1. Download all project files
# 2. Run installer (creates venv and installs pandas, flask, flask-cors)
./install.sh  # Linux/Mac
# OR
install.bat  # Windows

# 3. Activate environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows
```

### Regular Use
```bash
# ALWAYS activate environment first!
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Option A: Generate CSV files
python process_property_outages.py \
  --outages-file new_data.csv \
  --discovery-file discovery.csv

# Option B: Update database
python process_property_outages_db.py \
  --outages-file new_data.csv \
  --discovery-file discovery.csv \
  --database output/outages.db

# If using database, start API (also requires venv)
python api_server.py

# When finished, deactivate
deactivate
```

### Building a Web Frontend

With the API running, you can build a frontend using any framework:

**React Example:**
```javascript
// Fetch properties
fetch('http://localhost:5000/api/properties')
  .then(res => res.json())
  .then(properties => console.log(properties));

// Fetch hourly data for property
fetch('http://localhost:5000/api/property/1/hourly')
  .then(res => res.json())
  .then(hourly => {
    // Use chart library to visualize
  });
```

**Vue Example:**
```javascript
// In your component
async mounted() {
  const response = await fetch('http://localhost:5000/api/properties');
  this.properties = await response.json();
}
```

## 🎯 Key Features

### File-Based Processor
- ✅ Simple CSV output
- ✅ Easy to email/share
- ✅ Import into Excel/Google Sheets
- ✅ No database required

### Database Processor
- ✅ Structured relational data
- ✅ Fast queries
- ✅ Web application ready
- ✅ Scalable
- ✅ Includes raw outage records

### REST API
- ✅ RESTful design
- ✅ JSON responses
- ✅ CORS enabled
- ✅ Error handling
- ✅ Search functionality
- ✅ Statistics endpoint

## 📈 Example Queries

### Python
```python
import sqlite3

conn = sqlite3.connect('output/outages.db')
cursor = conn.cursor()

# Properties with most outages
cursor.execute("""
    SELECT property_name, total_outages 
    FROM properties 
    ORDER BY total_outages DESC 
    LIMIT 5
""")
print(cursor.fetchall())
```

### cURL
```bash
# Get all properties
curl http://localhost:5000/api/properties

# Get property details
curl http://localhost:5000/api/property/1

# Search
curl "http://localhost:5000/api/search?q=WAIKIKI"
```

## 🔧 Customization

### Change Output Directories
```bash
# CSV files
python process_property_outages.py \
  --output-dir /path/to/custom/dir \
  ...

# Database
python process_property_outages_db.py \
  --database /path/to/custom.db \
  ...
```

### Environment Variables
```bash
# Set database location for API
export OUTAGES_DB=/path/to/custom.db
python api_server.py
```

## 🐛 Troubleshooting

### "Database file not found"
Run `process_property_outages_db.py` first to create the database.

### "Module not found"
Activate the virtual environment: `source venv/bin/activate`

### API won't start
Check that port 5000 is available, or modify the port in `api_server.py`

## 📝 License

This system is provided as-is for data analysis purposes.

## 🤝 Support

Refer to:
- `README.md` for general usage
- `DATABASE_README.md` for database details
- `QUICKSTART.md` for quick start instructions
