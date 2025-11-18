# Automated Daily Schedule

This document outlines all automated tasks scheduled via cron.

## Daily Schedule (HST - Hawaii Standard Time)

### 1:00 AM - Database Backup
**Command:** `/home/jahama/Documents/home/jahama/MDU/theNewOutageLookingGlass/create-backup.sh`
- Backs up entire database and application
- Location: `/mnt/usb/MDU_Dashboard_Backup/`
- Retention: 7 days
- Logs: `/mnt/usb/MDU_Dashboard_Backup/backup.log`

### 6:00 AM - Eero Discovery Download
**Script:** `download_eero_discovery.py`
**API Dataset:** `networks` (Eero Discovery Details)
- Downloads latest Eero Discovery file via API
- Updates all 14,000+ networks in database
- Adds new networks, updates existing networks
- Removes networks no longer in discovery file
- Logs: `logs/eero_discovery_download.log`
- Processing report: `processing_reports/`

### 6:15 AM - Network Outages Download
**Script:** `download_network_outages.py`
**API Dataset:** `network_outages`
- Downloads latest network outages file via API to `inputs/` directory
- Checks for duplicate downloads
- Logs: `logs/network_outages_download.log`

### 6:30 AM - Network Outages Processing
**Script:** `process_and_archive.sh`
- Processes all downloaded network outages files from `inputs/` directory
- Updates database with outage data for existing networks only
- Maintains 7-day rolling window of outage data
- Archives processed files to `inputs_already_read/` with timestamp
- Logs: `logs/network_outages_processing.log`
- Processing report: `processing_reports/`

### 11:59 PM - WiFi Monitor Backup
**Command:** `/home/jahama/Documents/home/jahama/MDU/common_area_looking_glass/backup_to_usb.sh`
- Backs up WiFi monitoring application
- Location: `/mnt/usb/common_area_backup/`

## Key Features

### Duplicate Prevention
- Download scripts check `inputs_already_read/` directory
- Skip download if file already exists
- Automatically delete duplicate downloads
- Processing script only processes new files in `inputs/` directory

### Database Management
- **Append mode**: Adds new data, removes old data (7-day window)
- Networks are updated with latest discovery information
- Outages only processed for networks in database
- All networks have assigned properties (enforced by schema)

### Processing Reports
- Generated after each processing run
- Shows networks added/removed
- Shows outages processed
- Stored in `processing_reports/`
- Timestamped for tracking

### Separation of Concerns
- **Download phase**: Fetches files from API, stores in `inputs/`
- **Processing phase**: Processes files, updates database, archives to `inputs_already_read/`
- 15-minute gap between download and processing ensures download completion

## Files Created

### Scripts
- `download_eero_discovery.py` - Downloads Eero Discovery file
- `download_network_outages.py` - Downloads network outages file (download only)
- `process_and_archive.sh` - Processes and archives network outages files
- `process_property_outages_db.py` - Core processing engine

### Logs
- `logs/eero_discovery_download.log` - Eero Discovery download activity
- `logs/network_outages_download.log` - Network Outages download activity
- `logs/network_outages_processing.log` - Network Outages processing activity
- `logs/api_server.log` - API server activity

### Data Directories
- `inputs/` - Downloaded files (temporary)
- `inputs_already_read/` - Processed files (archived with timestamp)
- `processing_reports/` - Processing reports
- `output/outages.db` - Main database

## Monitoring

Check logs for any issues:
```bash
# Check discovery download
tail -f logs/eero_discovery_download.log

# Check outages download
tail -f logs/network_outages_download.log

# Check outages processing
tail -f logs/network_outages_processing.log

# Check processing reports
ls -lt processing_reports/ | head -5
```

## Manual Execution

Run scripts manually if needed:
```bash
# Discovery file download and processing
./venv/bin/python3 download_eero_discovery.py

# Outages file download only
./venv/bin/python3 download_network_outages.py

# Outages file processing (after download)
./process_and_archive.sh
```

## Crontab Schedule

View current schedule:
```bash
crontab -l
```

Edit schedule:
```bash
crontab -e
```
