# Migration to network_outages Files - Summary

## Changes Completed

### 1. Database Schema Updated
- Added location fields to `networks` table:
  - `country_code`, `country_name`
  - `city`, `region`, `region_name`
  - `latitude`, `longitude`
  - `timezone`, `postal_code`

### 2. Processing Script Updated
**File**: `process_property_outages_db.py`

**Key Changes:**
- Now accepts `--outages-file` instead of `--outages-file`
- Eero discovery file (`--discovery-file`) is now **optional**
- Reads `network_outages-<date>.csv` format with columns:
  - `network_id`, `start_time`, `end_time`
  - `country_code`, `country_name`, `city`, `region`
  - `latitude`, `longitude`, `timezone`, `postal_code`, `region_name`
- Automatically calculates `duration` from start/end times
- Handles missing Eero discovery files gracefully

**Usage:**
```bash
# With discovery file
python process_property_outages_db.py \
    --outages-file network_outages-2025-11-11.csv \
    --discovery-file Eero_Discovery_Details.csv \
    --mode rebuild

# Without discovery file (location data only)
python process_property_outages_db.py \
    --outages-file network_outages-2025-11-11.csv \
    --mode rebuild
```

### 3. Batch Processing Script Created
**File**: `process_multiple_days.sh`

Processes multiple days of network_outages files automatically.

**Usage:**
```bash
# Rebuild database with all network_outages files in inputs/
./process_multiple_days.sh --mode rebuild

# With discovery file
./process_multiple_days.sh \
    --mode rebuild \
    --discovery-file path/to/Eero_Discovery.csv

# Append mode (keeps existing data)
./process_multiple_days.sh --mode append
```

### 4. API Server Updated
**File**: `api_server.py`

**Changes:**
- Network endpoints now return location data:
  - `city`, `region`, `country_name`
  - `latitude`, `longitude`
  - `timezone`, `postal_code`

**Example API Response:**
```json
{
  "network_id": 16157219,
  "city": "Waianae",
  "region": "Hawaii",
  "country_name": "United States",
  "latitude": 21.4337,
  "longitude": -158.1767,
  "total_outages": 1105,
  "street_address": null,
  "subloc": null
}
```

### 5. Database Rebuilt
- **Status**: ✓ Complete
- **Database**: `output/outages.db` (22 MB)
- **Records**: 77,609 outages across 34,597 networks
- **Date Range**: October 29 - November 6, 2025
- **Files Processed**: 6 network_outages files

## Current State

### Data Sources
- **Primary**: `network_outages-<date>.csv` files (required)
- **Secondary**: Eero Discovery Details (optional)

### When Eero Discovery File is NOT Available
- All networks are grouped under "Unknown Property"
- Location data from network_outages is used
- Equipment information (xPON shelves, routers) is not available
- Frontend will still display outage data with location info

### When Eero Discovery File IS Available
- Networks are properly grouped by property (MDU Name)
- Equipment relationships are tracked
- Both location and property data are available

## File Locations

### Input Files
- `inputs/network_outages-2025-11-*.csv` - Processed
- `inputs_already_read/` - Old wan_connectivity files (archived)

### Output Files
- `output/outages.db` - Main database (rebuilt)

### Processing Scripts
- `process_property_outages_db.py` - Single file processor
- `process_multiple_days.sh` - Batch processor

### Server Files
- `api_server.py` - API backend (updated with location fields)
- `frontend/` - React frontend (no changes needed)

## Next Steps for Daily Updates

### Option 1: Process Single Day (Manual)
```bash
source venv/bin/activate
python process_property_outages_db.py \
    --outages-file inputs/network_outages-2025-11-12.csv \
    --mode append
```

### Option 2: Batch Process Multiple Days
```bash
source venv/bin/activate
./process_multiple_days.sh --mode append
```

### Option 3: Automated Daily Processing
Update your cron job or scheduled task to use the new script:
```bash
# Old command (deprecated)
# python process_property_outages_db.py --outages-file wan_connectivity.csv ...

# New command
python process_property_outages_db.py \
    --outages-file inputs/network_outages-$(date +%Y-%m-%d).csv \
    --mode append \
    --retain-days 7
```

## Testing

### Verify Database
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('output/outages.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM outages")
print(f"Total outages: {cursor.fetchone()[0]:,}")
cursor.execute("SELECT COUNT(*) FROM networks")
print(f"Total networks: {cursor.fetchone()[0]:,}")
cursor.execute("SELECT city, region, COUNT(*) FROM networks WHERE city IS NOT NULL GROUP BY city, region LIMIT 5")
for row in cursor.fetchall():
    print(f"  {row[0]}, {row[1]}: {row[2]} networks")
conn.close()
EOF
```

### Start Services
```bash
# Start backend API
source venv/bin/activate
python api_server.py

# In another terminal, start frontend
cd frontend
npm run dev
```

## Notes

- The database schema is backward compatible
- Existing frontend code works without modifications
- Location data is now available in the API
- Frontend can be enhanced later to display maps or location filters

## Migration Complete ✓

All tasks completed successfully. The system now uses `network_outages-<date>.csv` files instead of `wan_connectivity` files, and the Eero discovery file is optional.
