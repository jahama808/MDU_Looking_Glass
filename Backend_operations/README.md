# Property Outage Analysis Script

This Python script processes WAN connectivity outage data and Eero discovery details to generate per-property outage reports with hourly summaries.

## Requirements

- Python 3.6 or higher
- pandas library

## Installation

### Quick Setup (Recommended)

#### Linux/Mac:
```bash
# Make the install script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

#### Windows:
```cmd
REM Run the installation script
install.bat
```

The install script will:
1. Create a Python virtual environment in `./venv`
2. Activate the virtual environment
3. Install all required dependencies from `requirements.txt`

### Manual Installation

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Activate Virtual Environment

Before running the script, activate the virtual environment:

```bash
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Basic Usage

```bash
python process_property_outages.py \
  --connectivity-file wan_connectivity-2025-11-06.csv \
  --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv
```

This will create output files in `./output/property-files/` by default.

### Specify Custom Output Directory

```bash
python process_property_outages.py \
  --connectivity-file wan_connectivity-2025-11-06.csv \
  --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv \
  --output-dir ./my_reports
```

### Deactivate Virtual Environment

When you're done:

```bash
deactivate
```

### View Help

```bash
python process_property_outages.py --help
```

## Command-Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--connectivity-file` | Yes | Path to the WAN connectivity CSV file (contains outage data with columns: network_id, wan_down_start, wan_down_end, duration, reason) |
| `--discovery-file` | Yes | Path to the Eero discovery details CSV file (contains property and network data with columns: MDU Name, Eero Network ID, Street Address, Subloc, Customer Name) |
| `--output-dir` | No | Directory where output files will be saved (default: ./output/property-files) |

## Input File Requirements

### Connectivity File (WAN Outages)
Must contain the following columns:
- `network_id` - Unique network identifier
- `wan_down_start` - Timestamp when outage started
- `wan_down_end` - Timestamp when outage ended
- `duration` - Duration in seconds
- `reason` - Reason code for the outage

### Discovery File (Eero Networks)
Must contain the following columns:
- `MDU Name` - Property name
- `Eero Network ID` - Network identifier (matches network_id in connectivity file)
- `Street Address` - Property street address
- `Subloc` - Sub-location (apartment/unit number)
- `Customer Name` - Customer identifier

## Output

The script generates:

1. **Individual Property Files** - One CSV file per property that has outages
   - Format: `{PROPERTY_NAME}_outages.csv`
   - Contains:
     - Property header with summary statistics
     - Network summary showing total outages per network
     - Hourly outage counts for each network

2. **Index File** - `00_INDEX.txt`
   - Lists all properties and their corresponding output files
   - Includes summary statistics

### Output File Structure

Each property outage file contains four sections:

#### 1. Header
```
Property: WAIKIKI BEACH TOWER
Report Generated: 2025-11-07 06:54:30
Total Networks: 140
Total Outages: 178
```

#### 2. Network Summary (Total Outages)
```
network_id,total_outages,Eero Network ID,Street Address,Subloc,Customer Name
12501575,178,12501575,2470 KALAKAUA AVE,RM LBRY,200000000660051
```

#### 3. Aggregated Outage Counts (All Networks Combined by Hour)
This section shows the total number of outages across all networks in the property for each hour.
```
outage_hour,total_outage_count
2025-11-06 00:00:00+00:00,6
2025-11-06 01:00:00+00:00,7
2025-11-06 02:00:00+00:00,7
...
```

#### 4. Hourly Outage Counts (Per Network)
This section shows outages broken down by individual network and hour.
```
network_id,outage_hour,outage_count,Eero Network ID,Street Address,Subloc,Customer Name
12501575,2025-11-06 00:00:00+00:00,6,12501575,2470 KALAKAUA AVE,RM LBRY,200000000660051
12501575,2025-11-06 01:00:00+00:00,7,12501575,2470 KALAKAUA AVE,RM LBRY,200000000660051
...
```

## Example Output

Running the script will show progress like this:

```
============================================================
PROPERTY OUTAGE ANALYSIS
============================================================

Reading connectivity file: wan_connectivity-2025-11-06.csv
  ✓ Loaded 5,404 WAN connectivity records

Reading discovery file: Eero_Discovery_Details_-_2025-11-04_081045.csv
  ✓ Loaded 15,793 Eero discovery records

Processing timestamps...
  ✓ Timestamps converted

✓ Found 153 unique properties
✓ Output directory: ./output/property-files

============================================================
PROCESSING PROPERTIES
============================================================

[1/153] 1506 PIIKOI
  Networks: 5
  Outages: 0
  Status: Skipped (no outages)

[2/153] 1510 AND 1504 LIHOLIHO
  Networks: 22
  Outages: 1
  Status: ✓ Created 1510_AND_1504_LIHOLIHO_outages.csv

...

============================================================
SUMMARY
============================================================
Total Properties: 153
Properties with Outages: 49
Properties without Outages: 104
Total Outages Processed: 5,404
Output Directory: ./output/property-files
Index File: ./output/property-files/00_INDEX.txt
============================================================
```

## Features

- **Automatic Validation** - Validates input files exist and contain required columns
- **Error Handling** - Clear error messages if files are missing or malformed
- **Progress Tracking** - Shows real-time progress as properties are processed
- **Summary Statistics** - Provides comprehensive summary at completion
- **Clean Output** - Sanitizes property names for safe filenames
- **Hourly Aggregation** - Automatically groups outages by hour
- **Network Details** - Includes customer and location information in reports

## Troubleshooting

### "File not found" error
Make sure the file paths are correct and the files exist.

### "Missing required columns" error
Verify your input files contain all the required columns listed above.

### "Cannot read file" error
Check that you have read permissions for the input files.

### Script runs but no output files
This means no outages were found for any properties. Check that:
- The network_id in the connectivity file matches the Eero Network ID in the discovery file
- The connectivity file actually contains outage records

## Version

Version 1.0.0

## License

This script is provided as-is for data analysis purposes.
