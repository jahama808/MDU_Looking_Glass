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

## Running the Script

### 1. Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

### 2. Run the Analysis

```bash
python process_property_outages.py \
  --connectivity-file wan_connectivity-2025-11-06.csv \
  --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv
```

### 3. Find Your Results

Output files will be in: `./output/property-files/`

- `00_INDEX.txt` - List of all properties
- `{PROPERTY_NAME}_outages.csv` - Individual property reports

### 4. Deactivate When Done

```bash
deactivate
```

## File Structure

```
project/
├── install.sh                      # Linux/Mac installation script
├── install.bat                     # Windows installation script
├── requirements.txt                # Python dependencies
├── process_property_outages.py     # Main script
├── README.md                       # Full documentation
├── QUICKSTART.md                   # This file
├── venv/                           # Virtual environment (created by install)
└── output/
    └── property-files/             # Results go here
        ├── 00_INDEX.txt
        ├── PROPERTY1_outages.csv
        ├── PROPERTY2_outages.csv
        └── ...
```

## Need Help?

- View all options: `python process_property_outages.py --help`
- Read full docs: See `README.md`
