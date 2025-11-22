# Updating the Database with New Data

This guide explains how to update the MDU Performance Dashboard with new data files.

## Recommended: Automated Processing

The easiest way to update data is using the **automated processing system**. Just copy your CSV files to the `inputs/` directory and the system will process them automatically every 6 hours.

```bash
# Copy files to the inputs directory
cp network_outages-2025-11-08.csv inputs/
cp "Eero Discovery Details - 2025-11-08 120000.csv" inputs/
```

See the [Automated Updates](#automated-updates-recommended) section below for setup instructions.

## Quick Method (Manual Update Script)

### Linux/Mac:
```bash
# 1. Copy your new CSV files to the project directory
# 2. Run the update script
./update-data.sh network_outages-2025-11-08.csv "Eero Discovery Details - 2025-11-08 120000.csv"

# 3. Restart the application
./start-all.sh
```

### Windows:
```cmd
REM 1. Copy your new CSV files to the project directory
REM 2. Activate virtual environment
call venv\Scripts\activate.bat

REM 3. Run the processing script
python process_property_outages_db.py --outages-file network_outages-2025-11-08.csv --discovery-file "Eero Discovery Details - 2025-11-08 120000.csv"

REM 4. Restart the application
start-all.bat
```

## Manual Method (Step-by-Step)

### Step 1: Stop the Application

If the application is running, stop it:
- Press `Ctrl+C` in the terminal(s) where services are running
- Or close the terminal windows

### Step 2: Place New Data Files

Copy your new CSV files to the project directory:

```bash
# Example - copy from your downloads
cp ~/Downloads/network_outages-2025-11-08.csv .
cp ~/Downloads/"Eero Discovery Details - 2025-11-08 120000.csv" .
```

### Step 3: Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
call venv\Scripts\activate.bat
```

### Step 4: Process the New Files

Run the processing script with your new files:

**Append Mode (Recommended - keeps 7 days of data):**
```bash
python process_property_outages_db.py \
  --outages-file network_outages-2025-11-08.csv \
  --discovery-file "Eero Discovery Details - 2025-11-08 120000.csv" \
  --mode append \
  --retain-days 7
```

**Rebuild Mode (clears all existing data):**
```bash
python process_property_outages_db.py \
  --outages-file network_outages-2025-11-08.csv \
  --discovery-file "Eero Discovery Details - 2025-11-08 120000.csv" \
  --mode rebuild
```

#### Append Mode (default)
- ✓ Keeps existing outage data
- ✓ Adds new outages from CSV files
- ✓ Removes data older than 7 days (configurable)
- ✓ Maintains equipment relationships
- ✓ Allows viewing trends over multiple days

#### Rebuild Mode
- ✓ Clears the entire database
- ✓ Processes all properties (with and without outages)
- ✓ Extract xPON shelf and 7x50 router relationships
- ✓ Generate statistics
- ✓ Creates a fresh database at `./output/outages.db`

**Processing time:** ~30-60 seconds depending on file size

### Step 5: Restart the Application

**Linux/Mac:**
```bash
./start-all.sh
```

**Windows:**
```cmd
start-all.bat
```

### Step 6: Verify the Update

1. Open your browser to `http://localhost:5173`
2. Check the Dashboard - look at the "Last Updated" timestamp
3. Verify property counts and statistics match your new data

## File Naming Convention

Your CSV files should follow these patterns:

- **Network Outages:** `network_outages-YYYY-MM-DD.csv`
  - Example: `network_outages-2025-11-08.csv`

- **Eero Discovery:** `Eero Discovery Details - YYYY-MM-DD HHMMSS.csv`
  - Example: `Eero Discovery Details - 2025-11-08 120000.csv`

## Required CSV Columns

### Network Outages File Must Have:
- `network_id` - Unique network identifier
- `wan_down_start` - Outage start timestamp
- `wan_down_end` - Outage end timestamp
- `duration` - Outage duration
- `reason` - Reason for outage

### Eero Discovery File Must Have:
- `MDU Name` - Property name
- `Eero Network ID` - Network identifier  
- `Street Address` - Property address
- `Subloc` - Sub-location/unit
- `Customer Name` - Customer name
- `Equip Name` - Equipment name (ONT-SHELFNAME-##-##-##-##)
- `7x50` - 7x50 router name

## Archiving Old Data (Optional)

If you want to keep historical data:

```bash
# Create archive directory with today's date
mkdir -p data/archive/$(date +%Y-%m-%d)

# Move old files to archive
mv network_outages-*.csv data/archive/$(date +%Y-%m-%d)/
mv "Eero Discovery Details"*.csv data/archive/$(date +%Y-%m-%d)/

# Backup old database
cp output/outages.db data/archive/$(date +%Y-%m-%d)/outages.db
```

## Troubleshooting

### Error: "File not found"
- Check that CSV files are in the correct directory
- Verify file names are exact (including spaces and special characters)
- Use quotes around filenames with spaces

### Error: "Module not found"
- Make sure virtual environment is activated
- Look for `(venv)` at the start of your command prompt

### Error: "Missing required columns"
- Verify your CSV files have all required columns
- Check column names match exactly (case-sensitive)

### Database shows old data
- Make sure you restarted the application after processing
- Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
- Check the "Last Updated" timestamp on property details

### Processing takes too long
- Large files (>50MB) may take several minutes
- This is normal - the script processes all properties and relationships
- Do not interrupt the process

## Automated Updates (Recommended)

The MDU Performance Dashboard includes automated processing that monitors the `inputs/` directory for new data files and processes them automatically.

### How Automated Processing Works

1. **Place files in the inputs directory:**
   ```bash
   # Copy new files to the inputs directory
   cp network_outages-2025-11-08.csv inputs/
   cp "Eero Discovery Details - 2025-11-08 120000.csv" inputs/
   ```

2. **The system automatically:**
   - Finds files matching patterns: `network_outages-*` and `Eero Discovery Details*`
   - Checks if files have already been processed
   - Processes new files every 6 hours (at 00:00, 06:00, 12:00, 18:00)
   - **Appends new outage data** and maintains a **rolling 7-day window**
   - Removes outage data older than 7 days
   - Moves processed files to `inputs_already_read/<timestamp>/`
   - Logs all activity to `logs/auto-process.log`

**Note:** The automated scripts use **append mode** by default, which keeps existing data and only removes records older than 7 days. This allows you to see trends over the past week.

### Setting Up Automated Processing

#### Linux/Mac:
```bash
# Install systemd timer (runs every 6 hours)
cd systemd
sudo ./install-systemd.sh
```

See [systemd/README.md](systemd/README.md) for detailed instructions.

#### Windows:
```powershell
# Run PowerShell as Administrator
.\install-scheduled-task.ps1
```

See [WINDOWS_AUTOMATION.md](WINDOWS_AUTOMATION.md) for detailed instructions.

### Manual Trigger (Without Waiting for Schedule)

If you want to process files immediately without waiting for the scheduled run:

**Linux/Mac:**
```bash
./auto-process-data.sh
```

**Windows:**
```cmd
auto-process-data.bat
```

### Monitoring Automated Processing

**View the processing log:**
```bash
# Linux/Mac
tail -f logs/auto-process.log

# Windows (PowerShell)
Get-Content logs\auto-process.log -Tail 50 -Wait
```

**Check systemd timer status (Linux):**
```bash
systemctl status outage-auto-process.timer
systemctl list-timers outage-auto-process.timer
```

**Check Windows scheduled task:**
```powershell
Get-ScheduledTask -TaskName "OutageDashboardAutoProcess"
```

### Benefits of Automated Processing

- **No manual intervention required** - Just drop files in the `inputs/` directory
- **Duplicate prevention** - Automatically skips files that have already been processed
- **Complete audit trail** - All processing logged with timestamps
- **Archive management** - Processed files automatically organized by date/time
- **Service integration** - Can automatically restart API service after updates (Linux)

### File Requirements for Automation

Files must follow naming patterns:
- network outages: `network_outages-*.csv` (e.g., `network_outages-2025-11-08.csv`)
- Eero discovery: `Eero Discovery Details*.csv` (e.g., `Eero Discovery Details - 2025-11-08 120000.csv`)

Both files must be present in the `inputs/` directory for processing to begin.

## Database Location

Default location: `./output/outages.db`

To use a different location, specify with `--database` flag:
```bash
python process_property_outages_db.py \
  --outages-file wan.csv \
  --discovery-file eero.csv \
  --database /custom/path/outages.db
```

Remember to update `api_server.py` if you change the database location:
```python
DATABASE = os.environ.get('OUTAGES_DB', '/custom/path/outages.db')
```

## What Happens During Update

1. **Database is cleared** - All old data is removed
2. **New data is processed** - Fresh analysis of current state
3. **Relationships are rebuilt** - Properties linked to equipment
4. **Statistics are calculated** - Counts and aggregations
5. **Database is saved** - New data ready to use

**Important:** The entire database is regenerated. There is no "incremental update" - it's a full refresh each time.

## Support

For issues or questions about data updates, check:
- README.md - General documentation
- DEPLOYMENT_NOTES.md - Detailed deployment guide
- process_property_outages_db.py --help - Script usage help
