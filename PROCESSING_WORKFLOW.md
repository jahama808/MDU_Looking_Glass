# Network Outages Processing Workflow

## Overview

The system now correctly processes network outages with the following rules:
1. **Eero Discovery file** defines ALL properties and networks
2. **Network outages files** only add outages for networks that exist in the discovery file
3. Networks in outages files that aren't in the discovery file are **ignored**

## Database Structure

- **Properties**: Defined by Eero Discovery file (MDU Name)
- **Networks**: Defined by Eero Discovery file (Eero Network ID)
- **Outages**: From network_outages files, filtered to only include existing networks

## Processing Scripts

### 1. Main Processing Script: `process_discovery_then_outages.sh`

**Usage:**
```bash
source venv/bin/activate
./process_discovery_then_outages.sh
```

**What it does:**
1. Finds the Eero Discovery file in `inputs/`
2. Finds all `network_outages-*.csv` files in `inputs/`
3. Processes first outages file WITH discovery file (rebuild mode) → establishes all properties/networks
4. Processes remaining outages files WITHOUT discovery file (append mode) → only adds outages for existing networks
5. Moves all processed files to `inputs_already_used/`

**Expected behavior:**
- Skips outages for networks not in the Eero Discovery file
- No "Unknown Property" entries
- Only networks from the discovery file are in the database

### 2. Single File Processing: `process_property_outages_db.py`

**With Discovery File (Rebuild):**
```bash
python process_property_outages_db.py \
    --outages-file inputs/network_outages-2025-11-06.csv \
    --discovery-file "inputs/Eero Discovery Details - 2025-11-11 081053.csv" \
    --mode rebuild
```

**Without Discovery File (Append):**
```bash
python process_property_outages_db.py \
    --outages-file inputs/network_outages-2025-11-07.csv \
    --mode append
```

When run without a discovery file:
- Checks existing networks in database
- Only inserts outages for networks that exist
- Skips outages for networks not in database
- Reports how many outages were skipped

## File Management

### Input Directory (`inputs/`)
- Place new files here:
  - `Eero Discovery Details - YYYY-MM-DD HHMMSS.csv`
  - `network_outages-YYYY-MM-DD.csv`

### Archive Directory (`inputs_already_used/`)
- Processed files are automatically moved here
- Organized by processing timestamp for batch runs

## Typical Workflow

### Initial Setup (Fresh Database)
```bash
# 1. Place files in inputs/
cp /path/to/Eero_Discovery.csv inputs/
cp /path/to/network_outages-*.csv inputs/

# 2. Run the processing script
source venv/bin/activate
./process_discovery_then_outages.sh
```

### Daily Updates (Existing Database)
```bash
# 1. Place new outages file in inputs/
cp /path/to/network_outages-2025-11-12.csv inputs/

# 2. Process without discovery file (appends to existing data)
source venv/bin/activate
python process_property_outages_db.py \
    --outages-file inputs/network_outages-2025-11-12.csv \
    --mode append

# 3. Move processed file to archive
mv inputs/network_outages-2025-11-12.csv inputs_already_used/
```

### Weekly/Monthly Discovery Update
```bash
# 1. Place new discovery file and outages files
cp /path/to/new_Eero_Discovery.csv inputs/
cp /path/to/network_outages-*.csv inputs/

# 2. Rebuild database with new discovery
./process_discovery_then_outages.sh
```

## Verification

### Check Database Contents
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('output/outages.db')
cursor = conn.cursor()

print("=== DATABASE SUMMARY ===")
cursor.execute("SELECT COUNT(*) FROM properties")
print(f"Properties: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM properties WHERE property_name = 'Unknown Property'")
unknown = cursor.fetchone()[0]
print(f"Unknown Properties: {unknown} (should be 0)")

cursor.execute("SELECT COUNT(*) FROM networks")
print(f"Networks: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM outages")
print(f"Outages: {cursor.fetchone()[0]:,}")

conn.close()
EOF
```

### Start Services
```bash
# Backend API
source venv/bin/activate
python api_server.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

## Key Changes from Previous Version

### Before
- ❌ Created "Unknown Property" for networks without discovery data
- ❌ Added ALL networks from outages files
- ❌ Mixed property and non-property networks

### After
- ✅ Only properties from Eero Discovery file
- ✅ Only networks from Eero Discovery file
- ✅ Outages filtered to existing networks only
- ✅ Skips networks not in discovery file

## Frontend Updates

- "Outage Reasons Breakdown" section is now hidden if the only reason is "UNKNOWN" (null/empty)
- Location data (city, region, coordinates) available in network endpoints
- No other changes required

## Database Schema

Key tables:
- `properties` - MDU properties from discovery file
- `networks` - Networks for each property
- `outages` - Individual outage records
- `property_hourly_outages` - Aggregated by property and hour
- `network_hourly_outages` - Aggregated by network and hour
- `xpon_shelves` - Equipment tracking
- `router_7x50s` - Router tracking

## Troubleshooting

### Issue: "No networks found in database"
**Cause**: Trying to process outages without first processing discovery file
**Solution**: Run `process_discovery_then_outages.sh` or process first file with `--discovery-file`

### Issue: Too many outages skipped
**Cause**: Outages file contains networks not in your properties
**Solution**: This is expected behavior - only your property networks should be tracked

### Issue: "Unknown Property" appears
**Cause**: Old processing logic or manual script usage
**Solution**: Delete database and run `process_discovery_then_outages.sh`

## File Formats

### Eero Discovery File
Required columns:
- `MDU Name` - Property name
- `Eero Network ID` - Network identifier
- `Street Address`, `Subloc`, `Customer Name`
- `Service Config Name` - For speed targets
- `Gateway Speed Down/Up` - Actual speeds
- `Equip Name`, `7x50`, `SAP` - Equipment info

### Network Outages File
Required columns:
- `network_id` - Must match Eero Network ID
- `start_time`, `end_time` - ISO timestamp format
- `city`, `region`, `country_name` - Location data
- `latitude`, `longitude` - Coordinates

## Notes

- The discovery file should be updated periodically to reflect new properties/networks
- Outages files can be processed daily without the discovery file
- Database maintains a rolling window (default 7 days in append mode)
- All processed files are archived for reference
- **Important**: Networks without outages are retained in the database for speedtest tracking
