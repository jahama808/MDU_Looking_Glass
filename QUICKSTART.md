# Quick Start Guide

## Setup (One-Time)

### Linux/Mac
```bash
./install.sh
```

### Windows
```cmd
install.bat
```

**What this does:**
- Creates a Python virtual environment in `./venv`
- Installs pandas, flask, flask-cors, and requests
- Prepares your system for all operations

## Running the Scripts

**IMPORTANT:** All Python scripts must run inside the virtual environment!

### 1. Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 2. Choose Your Processing Method

**Option A: CSV Files**
```bash
python process_property_outages.py \
  --outages-file network_outages-2025-11-06.csv \
  --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv
```

**Option B: Database (Recommended for Web)**
```bash
python process_property_outages_db.py \
  --outages-file network_outages-2025-11-06.csv \
  --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv \
  --database output/outages.db
```

### 3. (Optional) Start API Server

If you used the database option:

```bash
python api_server.py
```

API will be available at http://localhost:5000

### 4. Find Your Results

**CSV Files:** `./output/property-files/`
- `00_INDEX.txt` - List of all properties
- `{PROPERTY_NAME}_outages.csv` - Individual property reports

**Database:** `./output/outages.db`
- Query with Python or SQL
- Access via API at http://localhost:5000

### 5. Deactivate When Done

```bash
deactivate
```

## File Structure

```
project/
├── install.sh                      # Linux/Mac installation script
├── install.bat                     # Windows installation script
├── requirements.txt                # Python dependencies
├── process_property_outages.py     # CSV processor (runs in venv)
├── process_property_outages_db.py  # Database processor (runs in venv)
├── api_server.py                   # API server (runs in venv)
├── README.md                       # Full documentation
├── QUICKSTART.md                   # This file
├── venv/                           # Virtual environment (created by install)
└── output/
    ├── property-files/             # CSV results (if using CSV processor)
    │   ├── 00_INDEX.txt
    │   └── *.csv
    └── outages.db                  # Database (if using DB processor)
```

## Common Workflow

```bash
# 1. Activate venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Process new data
python process_property_outages_db.py \
  --connectivity-file new_data.csv \
  --discovery-file discovery.csv

# 3. Start API server
python api_server.py

# 4. Build/run your web frontend (in another terminal)

# 5. When done, deactivate
deactivate
```

## Need Help?

- View all options: `python process_property_outages.py --help`
- View database options: `python process_property_outages_db.py --help`
- Read full docs: See `README.md` and `DATABASE_README.md`
