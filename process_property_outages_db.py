#!/usr/bin/env python3
"""
Property Outage Analysis Script - Database Version

This script processes network outage data and optionally Eero discovery details
and stores the results in a SQLite database for use by a web application.

Usage:
    python process_property_outages_db.py --outages-file <path> [--discovery-file <path>] [--database <path>]

Example:
    python process_property_outages_db.py \
        --outages-file network_outages-2025-11-06.csv \
        --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv \
        --database outages.db
"""

import pandas as pd
import argparse
import os
import sys
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from island_detector import detect_island
from pushover_notifier import PushoverNotifier


# Check if running in virtual environment
def check_venv():
    """Check if script is running in a virtual environment."""
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠️  WARNING: Not running in a virtual environment!")
        print("   It's recommended to run this script in a venv.")
        print("   Run: source venv/bin/activate  (or venv\\Scripts\\activate on Windows)")
        print()
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(0)
        print()


def validate_file(filepath, file_type, required=True):
    """Validate that the file exists and is readable."""
    if not filepath and not required:
        return False

    if not filepath and required:
        print(f"Error: {file_type} file is required")
        sys.exit(1)

    if not os.path.exists(filepath):
        if required:
            print(f"Error: {file_type} file not found: {filepath}")
            sys.exit(1)
        return False

    if not os.path.isfile(filepath):
        if required:
            print(f"Error: {file_type} path is not a file: {filepath}")
            sys.exit(1)
        return False

    try:
        with open(filepath, 'r') as f:
            pass
    except Exception as e:
        if required:
            print(f"Error: Cannot read {file_type} file: {e}")
            sys.exit(1)
        return False

    return True


def create_database_schema(conn):
    """Create the database schema."""
    cursor = conn.cursor()

    # Properties table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            property_id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_name TEXT UNIQUE NOT NULL,
            total_networks INTEGER,
            total_outages INTEGER,
            island TEXT,
            last_updated TIMESTAMP
        )
    """)

    # Networks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS networks (
            network_id INTEGER PRIMARY KEY,
            property_id INTEGER NOT NULL,
            street_address TEXT,
            subloc TEXT,
            customer_name TEXT,
            total_outages INTEGER,
            download_target REAL,
            upload_target REAL,
            gateway_speed_down REAL,
            gateway_speed_up REAL,
            speed_test_date TEXT,
            country_code TEXT,
            country_name TEXT,
            city TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            timezone TEXT,
            postal_code TEXT,
            region_name TEXT,
            FOREIGN KEY (property_id) REFERENCES properties(property_id)
        )
    """)

    # Hourly aggregated outages by property
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_hourly_outages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            outage_hour TIMESTAMP,
            total_outage_count INTEGER,
            FOREIGN KEY (property_id) REFERENCES properties(property_id),
            UNIQUE(property_id, outage_hour)
        )
    """)

    # Hourly outages by network
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_hourly_outages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            network_id INTEGER,
            outage_hour TIMESTAMP,
            outage_count INTEGER,
            FOREIGN KEY (network_id) REFERENCES networks(network_id),
            UNIQUE(network_id, outage_hour)
        )
    """)

    # Raw outages table (for detailed analysis)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outages (
            outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            network_id INTEGER,
            wan_down_start TIMESTAMP,
            wan_down_end TIMESTAMP,
            duration REAL,
            reason TEXT,
            FOREIGN KEY (network_id) REFERENCES networks(network_id)
        )
    """)

    # Ongoing outages table (for tracking current/unresolved outages)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ongoing_outages (
            ongoing_outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            network_id INTEGER,
            wan_down_start TIMESTAMP NOT NULL,
            wan_down_end TIMESTAMP,
            reason TEXT,
            first_detected TIMESTAMP NOT NULL,
            last_checked TIMESTAMP NOT NULL,
            FOREIGN KEY (network_id) REFERENCES networks(network_id),
            UNIQUE(network_id, wan_down_start)
        )
    """)

    # xPON Shelves table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xpon_shelves (
            shelf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shelf_name TEXT UNIQUE NOT NULL,
            total_properties INTEGER DEFAULT 0,
            total_networks INTEGER DEFAULT 0
        )
    """)

    # 7x50 Routers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS router_7x50s (
            router_id INTEGER PRIMARY KEY AUTOINCREMENT,
            router_name TEXT UNIQUE NOT NULL,
            total_properties INTEGER DEFAULT 0,
            total_networks INTEGER DEFAULT 0
        )
    """)

    # Property to xPON Shelf relationship (many-to-many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_xpon_shelves (
            property_id INTEGER,
            shelf_id INTEGER,
            network_count INTEGER DEFAULT 0,
            slots TEXT,
            pons TEXT,
            PRIMARY KEY (property_id, shelf_id),
            FOREIGN KEY (property_id) REFERENCES properties(property_id),
            FOREIGN KEY (shelf_id) REFERENCES xpon_shelves(shelf_id)
        )
    """)

    # Property to 7x50 Router relationship (many-to-many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_7x50s (
            property_id INTEGER,
            router_id INTEGER,
            network_count INTEGER DEFAULT 0,
            saps TEXT,
            PRIMARY KEY (property_id, router_id),
            FOREIGN KEY (property_id) REFERENCES properties(property_id),
            FOREIGN KEY (router_id) REFERENCES router_7x50s(router_id)
        )
    """)

    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_networks_property ON networks(property_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_hourly_property ON property_hourly_outages(property_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_hourly_hour ON property_hourly_outages(outage_hour)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_network_hourly_network ON network_hourly_outages(network_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_network_hourly_hour ON network_hourly_outages(outage_hour)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outages_network ON outages(network_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outages_start ON outages(wan_down_start)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_xpon_property ON property_xpon_shelves(property_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_xpon_shelf ON property_xpon_shelves(shelf_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_7x50_property ON property_7x50s(property_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_7x50_router ON property_7x50s(router_id)")

    conn.commit()
    print("✓ Database schema created")


def reconcile_ongoing_outages(cursor):
    """
    Reconcile ongoing outages with newly processed historical outages.

    If an outage that was marked as ongoing now appears in the historical
    outages table with an end time, remove it from the ongoing_outages table.

    Returns:
        Number of ongoing outages reconciled (removed from ongoing table)
    """
    # Find ongoing outages that now have matching completed outages
    reconciled = cursor.execute("""
        SELECT oo.ongoing_outage_id, oo.network_id, oo.wan_down_start
        FROM ongoing_outages oo
        INNER JOIN outages o
            ON oo.network_id = o.network_id
            AND oo.wan_down_start = o.wan_down_start
        WHERE oo.wan_down_end IS NULL
            AND o.wan_down_end IS NOT NULL
    """).fetchall()

    reconciled_count = 0
    for row in reconciled:
        # Remove from ongoing_outages since it's now in historical outages
        cursor.execute("""
            DELETE FROM ongoing_outages
            WHERE ongoing_outage_id = ?
        """, (row['ongoing_outage_id'],))
        reconciled_count += 1

    return reconciled_count


def parse_ont_name(ont_name):
    """
    Parse ONT name to extract xPON shelf information.

    Format: ONT-{SHELF_NAME}-{SHELF#}-{SLOT}-{PON}-{ONT}
    Example: ONT-HNLLHIMNOL7-01-10-13-25

    Returns: tuple of (shelf_name, slot, pon) or (None, None, None) if invalid
             Example: ('HNLLHIMNOL7', '10', '13')
    """
    if not ont_name or not isinstance(ont_name, str):
        return None, None, None

    parts = ont_name.split('-')
    # Should have at least: ONT, SHELF_NAME, SHELF#, SLOT, PON, ONT
    if len(parts) >= 6 and parts[0] == 'ONT':
        # The shelf name is the second part
        shelf_name = parts[1]
        # The slot is the fourth part (index 3)
        slot = parts[3]
        # The PON is the fifth part (index 4)
        pon = parts[4]
        return shelf_name, slot, pon

    return None, None, None


def parse_sap_lag(sap):
    """
    Parse SAP field to extract lag portion.

    Format: lag-{LAG#}.{OTHER_INFO}
    Example: lag-26.3001.694

    Returns: lag portion (e.g., 'lag-26') or None if invalid
    """
    if not sap or not isinstance(sap, str):
        return None

    # Check if it starts with 'lag-'
    if sap.startswith('lag-'):
        # Split by '.' and take the first part which includes 'lag-{LAG#}'
        parts = sap.split('.')
        if parts:
            return parts[0]  # Returns 'lag-26' from 'lag-26.3001.694'

    return None


def parse_service_config_speeds(service_config):
    """
    Parse Service Config Name to extract download and upload speed targets.

    Formats:
        - NG-HSI.600MB.600MB.XGSPON
        - NG-HSI.400MB.400MB
        - NGTV+HSI.1G.600MB

    Returns: tuple of (download_mbps, upload_mbps) or (None, None) if invalid
    """
    import re

    if not service_config or not isinstance(service_config, str):
        return None, None

    # Split by '.' and look for speed values
    parts = service_config.split('.')

    speeds = []
    for part in parts:
        # Match patterns like "600MB" or "1G"
        match = re.match(r'^(\d+(?:\.\d+)?)(G|MB)$', part, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            unit = match.group(2).upper()

            # Convert to Mbps
            if unit == 'G':
                mbps = value * 1000
            else:  # MB (Mbps)
                mbps = value

            speeds.append(mbps)

    # Expect 2 speeds: download and upload
    if len(speeds) >= 2:
        return speeds[0], speeds[1]

    return None, None


def parse_speed_value(speed_str):
    """
    Parse speed string to extract numeric value in Mbps.

    Format: "625.42 Mbps" or "604.34 Mbps"

    Returns: float value in Mbps or None if invalid
    """
    import re

    if not speed_str or not isinstance(speed_str, str):
        return None

    # Match pattern like "625.42 Mbps"
    match = re.match(r'^(\d+(?:\.\d+)?)\s*Mbps$', speed_str.strip(), re.IGNORECASE)
    if match:
        return float(match.group(1))

    return None


def clear_old_data(conn, days_to_keep=7):
    """Remove data older than specified days to maintain a rolling window."""
    cursor = conn.cursor()
    from datetime import datetime, timedelta

    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

    # Delete old outages
    cursor.execute("DELETE FROM outages WHERE wan_down_start < ?", (cutoff_date,))
    deleted_outages = cursor.rowcount

    # Delete old hourly aggregations
    cursor.execute("DELETE FROM network_hourly_outages WHERE outage_hour < ?", (cutoff_date,))
    cursor.execute("DELETE FROM property_hourly_outages WHERE outage_hour < ?", (cutoff_date,))

    # NOTE: We do NOT delete networks without outages - those are valid networks
    # that should remain in the database for speedtest tracking and reporting.
    # Networks are only removed if they're no longer in the discovery file
    # (handled by the main processing logic).

    # Clean up orphaned properties (properties with no networks and no recent data)
    cursor.execute("""
        DELETE FROM properties
        WHERE property_id NOT IN (SELECT DISTINCT property_id FROM networks)
        AND last_updated < ?
    """, (cutoff_date,))

    conn.commit()
    print(f"✓ Removed data older than {days_to_keep} days (cutoff: {cutoff_date[:10]})")
    print(f"  Deleted {deleted_outages} old outage records")


def clear_existing_data(conn):
    """Clear ALL existing data from all tables (for full rebuild)."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM outages")
    cursor.execute("DELETE FROM network_hourly_outages")
    cursor.execute("DELETE FROM property_hourly_outages")
    cursor.execute("DELETE FROM property_xpon_shelves")
    cursor.execute("DELETE FROM property_7x50s")
    cursor.execute("DELETE FROM networks")
    cursor.execute("DELETE FROM properties")
    cursor.execute("DELETE FROM xpon_shelves")
    cursor.execute("DELETE FROM router_7x50s")
    conn.commit()
    print("✓ All existing data cleared (full rebuild mode)")


def generate_processing_report(report_data, report_dir='./processing_reports'):
    """Generate a processing report showing networks added and removed.

    Args:
        report_data: Dictionary containing report information
        report_dir: Directory to store the report
    """
    # Create report directory if it doesn't exist
    os.makedirs(report_dir, exist_ok=True)

    # Generate report filename with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    report_filename = f"processing_report_{timestamp}.txt"
    report_path = os.path.join(report_dir, report_filename)

    # Build report content
    lines = []
    lines.append("=" * 80)
    lines.append("NETWORK PROCESSING REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Processing Mode: {report_data.get('mode', 'N/A')}")
    lines.append("")

    lines.append("FILES PROCESSED:")
    lines.append("-" * 80)
    lines.append(f"Outages File: {report_data.get('outages_file', 'N/A')}")
    lines.append(f"Discovery File: {report_data.get('discovery_file', 'Not provided')}")
    lines.append(f"Database: {report_data.get('database', 'N/A')}")
    lines.append("")

    # Networks Added
    networks_added = report_data.get('networks_added', {})
    lines.append("NETWORKS ADDED:")
    lines.append("-" * 80)
    if networks_added:
        lines.append(f"Total Networks Added: {len(networks_added)}")
        lines.append("")
        for network_id, info in sorted(networks_added.items()):
            lines.append(f"  Network ID: {network_id}")
            if info.get('property'):
                lines.append(f"    Property: {info['property']}")
            if info.get('address'):
                lines.append(f"    Address: {info['address']}")
            if info.get('customer'):
                lines.append(f"    Customer: {info['customer']}")
            lines.append("")
    else:
        lines.append("  No networks added")
        lines.append("")

    # Networks Removed
    networks_removed = report_data.get('networks_removed', {})
    lines.append("NETWORKS REMOVED:")
    lines.append("-" * 80)
    if networks_removed:
        lines.append(f"Total Networks Removed: {len(networks_removed)}")
        lines.append("")
        for network_id, info in sorted(networks_removed.items()):
            lines.append(f"  Network ID: {network_id}")
            if info.get('property'):
                lines.append(f"    Property: {info['property']}")
            if info.get('address'):
                lines.append(f"    Address: {info['address']}")
            if info.get('customer'):
                lines.append(f"    Customer: {info['customer']}")
            lines.append("")
    else:
        lines.append("  No networks removed")
        lines.append("")

    # Properties Removed
    properties_removed = report_data.get('properties_removed', 0)
    if properties_removed > 0:
        lines.append("PROPERTIES REMOVED:")
        lines.append("-" * 80)
        lines.append(f"  {properties_removed} properties removed (no remaining networks)")
        lines.append("")

    # Summary Statistics
    lines.append("SUMMARY STATISTICS:")
    lines.append("-" * 80)
    lines.append(f"Total Outages Processed: {report_data.get('total_outages_processed', 0):,}")
    lines.append(f"Networks in Database (after processing): {report_data.get('final_network_count', 0):,}")
    lines.append(f"Properties in Database (after processing): {report_data.get('final_property_count', 0):,}")
    lines.append("")

    lines.append("=" * 80)

    # Write report to file
    report_content = "\n".join(lines)
    with open(report_path, 'w') as f:
        f.write(report_content)

    return report_path


def process_outages_to_db(outages_file, discovery_file, database_path, mode='append', retain_days=7):
    """Process the outage data and store in database.

    Args:
        outages_file: Path to network outages CSV
        discovery_file: Path to Eero discovery CSV (optional)
        database_path: Path to SQLite database
        mode: 'append' to add new data and clean old, 'rebuild' to clear all and rebuild
        retain_days: Number of days of data to keep (only used in append mode)
    """

    # Initialize Pushover notifier
    notifier = PushoverNotifier()
    start_time = time.time()

    # Initialize report tracking
    report_data = {
        'mode': mode,
        'outages_file': outages_file,
        'discovery_file': discovery_file if discovery_file else 'Not provided',
        'database': database_path,
        'networks_added': {},
        'networks_removed': {},
        'properties_removed': 0,
        'total_outages_processed': 0,
        'final_network_count': 0,
        'final_property_count': 0
    }

    print(f"\n{'='*60}")
    print("PROPERTY OUTAGE ANALYSIS - DATABASE VERSION")
    print(f"{'='*60}\n")

    # Send notification that processing is starting
    notifier.notify_processing_start(
        filename=os.path.basename(outages_file),
        mode=mode
    )

    # Read the network outages file
    print(f"Reading network outages file: {outages_file}")
    try:
        network_outages = pd.read_csv(outages_file)
        print(f"  ✓ Loaded {len(network_outages):,} network outage records")
    except Exception as e:
        print(f"  ✗ Error reading outages file: {e}")
        sys.exit(1)

    # Validate required columns
    required_outage_cols = ['network_id', 'start_time', 'end_time']
    missing_outage_cols = [col for col in required_outage_cols if col not in network_outages.columns]

    if missing_outage_cols:
        print(f"\n✗ Error: Outages file missing required columns: {missing_outage_cols}")
        sys.exit(1)

    # Convert timestamps to datetime and calculate duration
    print("\nProcessing timestamps...")
    try:
        network_outages['start_time'] = pd.to_datetime(network_outages['start_time'])
        network_outages['end_time'] = pd.to_datetime(network_outages['end_time'])
        # Calculate duration in hours
        network_outages['duration'] = (network_outages['end_time'] - network_outages['start_time']).dt.total_seconds() / 3600
        print("  ✓ Timestamps converted and duration calculated")
    except Exception as e:
        print(f"  ✗ Error converting timestamps: {e}")
        sys.exit(1)

    # Extract hour from start time for grouping
    network_outages['outage_hour'] = network_outages['start_time'].dt.floor('h')

    # Read Eero discovery file if provided
    eero_details = None
    has_discovery = discovery_file and validate_file(discovery_file, "Discovery", required=False)

    if has_discovery:
        print(f"\nReading discovery file: {discovery_file}")
        try:
            eero_details = pd.read_csv(discovery_file)
            print(f"  ✓ Loaded {len(eero_details):,} Eero discovery records")

            # Validate required columns
            required_eero_cols = ['MDU Name', 'Eero Network ID']
            missing_eero_cols = [col for col in required_eero_cols if col not in eero_details.columns]

            if missing_eero_cols:
                print(f"  ⚠ Warning: Discovery file missing some columns: {missing_eero_cols}")
                print(f"  Continuing without full discovery data...")
                eero_details = None
        except Exception as e:
            print(f"  ⚠ Warning: Error reading discovery file: {e}")
            print(f"  Continuing without discovery data...")
            eero_details = None
    else:
        print("\n⚠ No Eero discovery file provided - processing outages only")

    # Connect to database
    print(f"\nConnecting to database: {database_path}")
    print(f"Mode: {mode}")
    if mode == 'append':
        print(f"Retaining data for: {retain_days} days")
    conn = sqlite3.connect(database_path)

    # Create schema
    create_database_schema(conn)

    # Clear data based on mode
    if mode == 'rebuild':
        clear_existing_data(conn)
    else:  # append mode
        clear_old_data(conn, days_to_keep=retain_days)

    cursor = conn.cursor()

    # Process data
    print(f"\n{'='*60}")
    print("PROCESSING DATA")
    print(f"{'='*60}\n")

    total_outages_processed = 0

    if eero_details is not None:
        # Process by property when we have discovery data
        properties = eero_details['MDU Name'].dropna().unique()
        print(f"✓ Found {len(properties)} unique properties")

        properties_with_outages = 0
        properties_without_outages = 0

        for idx, property_name in enumerate(sorted(properties), 1):
            print(f"[{idx}/{len(properties)}] {property_name}")

            # Get all networks for this property
            property_networks = eero_details[eero_details['MDU Name'] == property_name]
            network_ids = property_networks['Eero Network ID'].dropna().unique()

            print(f"  Networks: {len(network_ids)}")

            # Get all outages for these networks
            property_outages = network_outages[network_outages['network_id'].isin(network_ids)]

            print(f"  Outages: {len(property_outages)}")

            # Detect island from network data (try first network with location data)
            detected_island = None
            for _, network_row in property_networks.iterrows():
                # Get city and zip from discovery file first, then fall back to outages location data
                city = network_row.get('City') if 'City' in network_row and pd.notna(network_row.get('City')) else None
                postal_code = network_row.get('Zip') if 'Zip' in network_row and pd.notna(network_row.get('Zip')) else None

                # Get location data from network outages as fallback
                network_outages_for_id = property_outages[property_outages['network_id'] == network_row['Eero Network ID']]
                location_data = network_outages_for_id.iloc[0] if len(network_outages_for_id) > 0 else None

                # Use location data only if not found in discovery file
                if not city:
                    city = location_data.get('city') if location_data is not None and 'city' in location_data else None
                if not postal_code:
                    postal_code = location_data.get('postal_code') if location_data is not None and 'postal_code' in location_data else None
                latitude = location_data.get('latitude') if location_data is not None and 'latitude' in location_data else None
                longitude = location_data.get('longitude') if location_data is not None and 'longitude' in location_data else None

                detected_island = detect_island(
                    city=city,
                    postal_code=postal_code,
                    latitude=latitude,
                    longitude=longitude
                )

                if detected_island:
                    break

            # If no island detected from data, try property name
            if not detected_island:
                name_upper = property_name.upper()
                if 'WAIKIKI' in name_upper or 'HONOLULU' in name_upper or 'ALA MOANA' in name_upper:
                    detected_island = 'Oahu'
                elif 'KAANAPALI' in name_upper or 'LAHAINA' in name_upper or 'WAILEA' in name_upper or 'KIHEI' in name_upper:
                    detected_island = 'Maui'
                elif 'KONA' in name_upper or 'HILO' in name_upper or 'WAIKOLOA' in name_upper:
                    detected_island = 'Hawaii'
                elif 'POIPU' in name_upper or 'PRINCEVILLE' in name_upper or 'KAPAA' in name_upper:
                    detected_island = 'Kauai'

            # Insert or update property
            cursor.execute("""
                INSERT INTO properties (property_name, total_networks, total_outages, island, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(property_name) DO UPDATE SET
                    total_networks = excluded.total_networks,
                    total_outages = total_outages + excluded.total_outages,
                    island = COALESCE(excluded.island, island),
                    last_updated = excluded.last_updated
            """, (property_name, len(network_ids), len(property_outages), detected_island, datetime.now()))

            # Get the property_id
            cursor.execute("SELECT property_id FROM properties WHERE property_name = ?", (property_name,))
            property_id = cursor.fetchone()[0]

            # Track statistics
            if len(property_outages) == 0:
                properties_without_outages += 1
            else:
                properties_with_outages += 1
                total_outages_processed += len(property_outages)

            # Insert networks
            network_info = property_networks[['Eero Network ID', 'Street Address', 'Subloc', 'Customer Name', 'Service Config Name', 'Gateway Speed Down', 'Gateway Speed Up', 'Gateway Speed Date']].drop_duplicates()

            for _, network_row in network_info.iterrows():
                network_id = int(network_row['Eero Network ID'])
                network_outages_for_id = property_outages[property_outages['network_id'] == network_id]

                # Check if this is a new network (for reporting)
                cursor.execute("SELECT network_id FROM networks WHERE network_id = ?", (network_id,))
                is_new_network = cursor.fetchone() is None

                # Get location data from outages if available
                location_data = network_outages_for_id.iloc[0] if len(network_outages_for_id) > 0 else None

                # Parse speed targets from Service Config Name
                download_target, upload_target = parse_service_config_speeds(network_row.get('Service Config Name'))

                # Parse actual speeds from Gateway Speed columns
                gateway_speed_down = parse_speed_value(network_row.get('Gateway Speed Down'))
                gateway_speed_up = parse_speed_value(network_row.get('Gateway Speed Up'))

                # Get speed test date
                speed_test_date = network_row.get('Gateway Speed Date')
                if pd.notna(speed_test_date):
                    speed_test_date = str(speed_test_date)
                else:
                    speed_test_date = None

                cursor.execute("""
                    INSERT INTO networks
                    (network_id, property_id, street_address, subloc, customer_name, total_outages,
                     download_target, upload_target, gateway_speed_down, gateway_speed_up, speed_test_date,
                     country_code, country_name, city, region, latitude, longitude, timezone, postal_code, region_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(network_id) DO UPDATE SET
                        total_outages = total_outages + excluded.total_outages,
                        street_address = excluded.street_address,
                        subloc = excluded.subloc,
                        customer_name = excluded.customer_name,
                        download_target = excluded.download_target,
                        upload_target = excluded.upload_target,
                        gateway_speed_down = excluded.gateway_speed_down,
                        gateway_speed_up = excluded.gateway_speed_up,
                        speed_test_date = excluded.speed_test_date,
                        country_code = excluded.country_code,
                        country_name = excluded.country_name,
                        city = excluded.city,
                        region = excluded.region,
                        latitude = excluded.latitude,
                        longitude = excluded.longitude,
                        timezone = excluded.timezone,
                        postal_code = excluded.postal_code,
                        region_name = excluded.region_name
                """, (
                    network_id,
                    property_id,
                    network_row.get('Street Address'),
                    network_row.get('Subloc'),
                    network_row.get('Customer Name'),
                    len(network_outages_for_id),
                    download_target,
                    upload_target,
                    gateway_speed_down,
                    gateway_speed_up,
                    speed_test_date,
                    location_data.get('country_code') if location_data is not None else None,
                    location_data.get('country_name') if location_data is not None else None,
                    city,  # Use city from discovery file
                    location_data.get('region') if location_data is not None else None,
                    latitude,
                    longitude,
                    location_data.get('timezone') if location_data is not None else None,
                    postal_code,  # Use postal_code from discovery file

                    location_data.get('region_name') if location_data is not None else None
                ))

                # Track new networks in report
                if is_new_network:
                    report_data['networks_added'][network_id] = {
                        'property': property_name,
                        'address': network_row.get('Street Address'),
                        'customer': network_row.get('Customer Name')
                    }

            # Process equipment (xPON shelves and 7x50 routers)
            equipment_cols = ['Equip Name', '7x50']
            if 'SAP' in property_networks.columns:
                equipment_cols.append('SAP')
            equipment_info = property_networks[equipment_cols].dropna(subset=['Equip Name'])

            # Track unique shelves and routers for this property
            property_shelves = {}
            property_routers = {}

            for _, equip_row in equipment_info.iterrows():
                # Parse xPON shelf from Equip Name
                shelf_name, slot, pon = parse_ont_name(equip_row['Equip Name'])
                if shelf_name:
                    if shelf_name not in property_shelves:
                        property_shelves[shelf_name] = {'count': 0, 'slots': set(), 'pons': set()}
                    property_shelves[shelf_name]['count'] += 1
                    if slot:
                        property_shelves[shelf_name]['slots'].add(slot)
                    if pon:
                        property_shelves[shelf_name]['pons'].add(pon)

                # Extract 7x50 router name and SAP
                router_name = equip_row['7x50']
                if router_name and isinstance(router_name, str) and router_name.strip():
                    router_name = router_name.strip()
                    if router_name not in property_routers:
                        property_routers[router_name] = {'count': 0, 'saps': set()}
                    property_routers[router_name]['count'] += 1

                    if 'SAP' in equip_row and equip_row['SAP']:
                        sap_lag = parse_sap_lag(equip_row['SAP'])
                        if sap_lag:
                            property_routers[router_name]['saps'].add(sap_lag)

            # Insert xPON shelves and create relationships
            for shelf_name, shelf_data in property_shelves.items():
                cursor.execute("INSERT OR IGNORE INTO xpon_shelves (shelf_name) VALUES (?)", (shelf_name,))
                cursor.execute("SELECT shelf_id FROM xpon_shelves WHERE shelf_name = ?", (shelf_name,))
                shelf_id = cursor.fetchone()[0]

                slots_str = ','.join(sorted(shelf_data['slots'], key=lambda x: int(x) if x.isdigit() else 0)) if shelf_data['slots'] else ''
                pons_str = ','.join(sorted(shelf_data['pons'], key=lambda x: int(x) if x.isdigit() else 0)) if shelf_data['pons'] else ''

                cursor.execute("""
                    INSERT OR REPLACE INTO property_xpon_shelves (property_id, shelf_id, network_count, slots, pons)
                    VALUES (?, ?, ?, ?, ?)
                """, (property_id, shelf_id, shelf_data['count'], slots_str, pons_str))

            # Insert 7x50 routers and create relationships
            for router_name, router_data in property_routers.items():
                cursor.execute("INSERT OR IGNORE INTO router_7x50s (router_name) VALUES (?)", (router_name,))
                cursor.execute("SELECT router_id FROM router_7x50s WHERE router_name = ?", (router_name,))
                router_id = cursor.fetchone()[0]

                saps_str = ','.join(sorted(router_data['saps'])) if router_data['saps'] else ''

                cursor.execute("""
                    INSERT OR REPLACE INTO property_7x50s (property_id, router_id, network_count, saps)
                    VALUES (?, ?, ?, ?)
                """, (property_id, router_id, router_data['count'], saps_str))

            # Process outage data
            if len(property_outages) > 0:
                # Insert raw outages
                for _, outage in property_outages.iterrows():
                    cursor.execute("""
                        INSERT INTO outages (network_id, wan_down_start, wan_down_end, duration, reason)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        int(outage['network_id']),
                        str(outage['start_time']),
                        str(outage['end_time']),
                        outage['duration'],
                        None  # network_outages doesn't have a reason field
                    ))

                # Calculate and insert aggregated hourly outages
                aggregated_outages = property_outages.groupby('outage_hour').size().reset_index(name='total_outage_count')

                for _, agg_row in aggregated_outages.iterrows():
                    cursor.execute("""
                        INSERT INTO property_hourly_outages (property_id, outage_hour, total_outage_count)
                        VALUES (?, ?, ?)
                        ON CONFLICT(property_id, outage_hour) DO UPDATE SET
                            total_outage_count = total_outage_count + excluded.total_outage_count
                    """, (property_id, str(agg_row['outage_hour']), agg_row['total_outage_count']))

                # Calculate and insert network hourly outages
                hourly_outages = property_outages.groupby(['network_id', 'outage_hour']).size().reset_index(name='outage_count')

                for _, hour_row in hourly_outages.iterrows():
                    cursor.execute("""
                        INSERT INTO network_hourly_outages (network_id, outage_hour, outage_count)
                        VALUES (?, ?, ?)
                        ON CONFLICT(network_id, outage_hour) DO UPDATE SET
                            outage_count = outage_count + excluded.outage_count
                    """, (int(hour_row['network_id']), str(hour_row['outage_hour']), hour_row['outage_count']))

                print(f"  Status: ✓ Data inserted into database (with outages)\n")
            else:
                print(f"  Status: ✓ Equipment relationships stored (no outages)\n")

            conn.commit()

        # Reconcile ongoing outages with newly processed outages
        print("Reconciling ongoing outages with new data...")
        reconciled_count = reconcile_ongoing_outages(cursor)
        print(f"  ✓ Reconciled {reconciled_count} ongoing outage(s)\n")

        # Update equipment statistics
        print("Updating equipment statistics...")

        # Update xPON shelf statistics
        cursor.execute("""
            UPDATE xpon_shelves
            SET total_properties = (
                SELECT COUNT(DISTINCT property_id)
                FROM property_xpon_shelves
                WHERE shelf_id = xpon_shelves.shelf_id
            ),
            total_networks = (
                SELECT SUM(network_count)
                FROM property_xpon_shelves
                WHERE shelf_id = xpon_shelves.shelf_id
            )
        """)

        # Update 7x50 router statistics
        cursor.execute("""
            UPDATE router_7x50s
            SET total_properties = (
                SELECT COUNT(DISTINCT property_id)
                FROM property_7x50s
                WHERE router_id = router_7x50s.router_id
            ),
            total_networks = (
                SELECT SUM(network_count)
                FROM property_7x50s
                WHERE router_id = router_7x50s.router_id
            )
        """)

        conn.commit()
        print("  ✓ Equipment statistics updated\n")

        # Remove networks that are no longer in the discovery file
        print("Checking for networks to remove...")

        # Get all network IDs from the discovery file
        discovery_network_ids = set(eero_details['Eero Network ID'].dropna().astype(int).unique())

        # Get all network IDs currently in the database
        cursor.execute("SELECT network_id FROM networks")
        db_network_ids = set(row[0] for row in cursor.fetchall())

        # Find networks in DB but not in discovery file
        networks_to_remove = db_network_ids - discovery_network_ids

        if networks_to_remove:
            print(f"  Found {len(networks_to_remove)} networks to remove (no longer in discovery file)")

            # Delete related data first (to maintain referential integrity)
            for network_id in networks_to_remove:
                # Get network info before deleting (for reporting)
                cursor.execute("""
                    SELECT n.network_id, n.street_address, n.customer_name, p.property_name
                    FROM networks n
                    JOIN properties p ON n.property_id = p.property_id
                    WHERE n.network_id = ?
                """, (network_id,))
                network_info = cursor.fetchone()
                if network_info:
                    report_data['networks_removed'][network_id] = {
                        'property': network_info[3],
                        'address': network_info[1],
                        'customer': network_info[2]
                    }

                # Delete network hourly outages
                cursor.execute("DELETE FROM network_hourly_outages WHERE network_id = ?", (network_id,))

                # Delete raw outages
                cursor.execute("DELETE FROM outages WHERE network_id = ?", (network_id,))

                # Delete the network itself
                cursor.execute("DELETE FROM networks WHERE network_id = ?", (network_id,))

            # Recalculate property totals after network removal
            cursor.execute("""
                UPDATE properties
                SET total_networks = (
                    SELECT COUNT(*)
                    FROM networks
                    WHERE property_id = properties.property_id
                ),
                total_outages = (
                    SELECT COUNT(*)
                    FROM outages o
                    JOIN networks n ON o.network_id = n.network_id
                    WHERE n.property_id = properties.property_id
                )
            """)

            # Remove properties that now have no networks
            cursor.execute("""
                DELETE FROM properties
                WHERE property_id NOT IN (SELECT DISTINCT property_id FROM networks)
            """)
            removed_properties = cursor.rowcount
            report_data['properties_removed'] = removed_properties

            if removed_properties > 0:
                print(f"  Removed {removed_properties} properties that no longer have networks")

            conn.commit()
            print(f"  ✓ Removed {len(networks_to_remove)} networks from database\n")
        else:
            print(f"  ✓ All networks in discovery file are current (no removals needed)\n")

        print(f"Total Properties: {len(properties)}")
        print(f"Properties with Outages: {properties_with_outages}")
        print(f"Properties without Outages: {properties_without_outages}")

    else:
        # Process outages for existing networks only (no discovery file)
        print("Processing outages for existing networks only...")

        # Get all existing network IDs from the database
        cursor.execute("SELECT network_id FROM networks")
        existing_networks = set(row[0] for row in cursor.fetchall())

        if len(existing_networks) == 0:
            print("  ⚠ WARNING: No networks found in database!")
            print("  You must process an Eero Discovery file first to establish properties and networks.")
            print("  Skipping outage processing.")

            # Generate report even for failed processing
            cursor.execute("SELECT COUNT(*) FROM networks")
            report_data['final_network_count'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM properties")
            report_data['final_property_count'] = cursor.fetchone()[0]
            conn.close()

            report_path = generate_processing_report(report_data)
            print(f"\n✓ Processing report saved to: {report_path}")
            return 0

        print(f"  Found {len(existing_networks)} existing networks in database")

        # Filter outages to only include those for existing networks
        valid_outages = network_outages[network_outages['network_id'].isin(existing_networks)]
        skipped_count = len(network_outages) - len(valid_outages)

        print(f"  Found {len(valid_outages):,} outages for existing networks")
        if skipped_count > 0:
            print(f"  Skipped {skipped_count:,} outages for networks not in database")

        if len(valid_outages) == 0:
            print("  No matching outages to process")

            # Generate report even when no outages processed
            cursor.execute("SELECT COUNT(*) FROM networks")
            report_data['final_network_count'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM properties")
            report_data['final_property_count'] = cursor.fetchone()[0]
            conn.close()

            report_path = generate_processing_report(report_data)
            print(f"\n✓ Processing report saved to: {report_path}")
            return 0

        # Insert outages for existing networks only
        print(f"  Inserting outages...")
        outages_inserted = 0
        for _, outage in valid_outages.iterrows():
            cursor.execute("""
                INSERT INTO outages (network_id, wan_down_start, wan_down_end, duration, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(outage['network_id']),
                str(outage['start_time']),
                str(outage['end_time']),
                outage['duration'],
                None
            ))
            outages_inserted += 1

        # Update network outage counts
        print(f"  Updating network outage counts...")
        for network_id in valid_outages['network_id'].unique():
            network_outage_count = len(valid_outages[valid_outages['network_id'] == network_id])
            cursor.execute("""
                UPDATE networks
                SET total_outages = total_outages + ?
                WHERE network_id = ?
            """, (network_outage_count, int(network_id)))

        # Update location data for networks if available from outages
        print(f"  Updating network location data...")
        for network_id in valid_outages['network_id'].unique():
            network_outages_for_id = valid_outages[valid_outages['network_id'] == network_id]
            if len(network_outages_for_id) > 0:
                location_data = network_outages_for_id.iloc[0]
                cursor.execute("""
                    UPDATE networks
                    SET country_code = COALESCE(country_code, ?),
                        country_name = COALESCE(country_name, ?),
                        city = COALESCE(city, ?),
                        region = COALESCE(region, ?),
                        latitude = COALESCE(latitude, ?),
                        longitude = COALESCE(longitude, ?),
                        timezone = COALESCE(timezone, ?),
                        postal_code = COALESCE(postal_code, ?),
                        region_name = COALESCE(region_name, ?)
                    WHERE network_id = ?
                """, (
                    location_data.get('country_code'),
                    location_data.get('country_name'),
                    location_data.get('city'),
                    location_data.get('region'),
                    location_data.get('latitude'),
                    location_data.get('longitude'),
                    location_data.get('timezone'),
                    location_data.get('postal_code'),
                    location_data.get('region_name'),
                    int(network_id)
                ))

        # Calculate hourly aggregations by property
        print(f"  Calculating hourly aggregations...")

        # Get property_id for each network
        for network_id in valid_outages['network_id'].unique():
            cursor.execute("SELECT property_id FROM networks WHERE network_id = ?", (int(network_id),))
            result = cursor.fetchone()
            if result:
                property_id = result[0]
                network_outages_subset = valid_outages[valid_outages['network_id'] == network_id]

                # Property hourly aggregations
                aggregated_outages = network_outages_subset.groupby('outage_hour').size().reset_index(name='total_outage_count')
                for _, agg_row in aggregated_outages.iterrows():
                    cursor.execute("""
                        INSERT INTO property_hourly_outages (property_id, outage_hour, total_outage_count)
                        VALUES (?, ?, ?)
                        ON CONFLICT(property_id, outage_hour) DO UPDATE SET
                            total_outage_count = total_outage_count + excluded.total_outage_count
                    """, (property_id, str(agg_row['outage_hour']), agg_row['total_outage_count']))

                # Network hourly outages
                hourly_outages = network_outages_subset.groupby('outage_hour').size().reset_index(name='outage_count')
                for _, hour_row in hourly_outages.iterrows():
                    cursor.execute("""
                        INSERT INTO network_hourly_outages (network_id, outage_hour, outage_count)
                        VALUES (?, ?, ?)
                        ON CONFLICT(network_id, outage_hour) DO UPDATE SET
                            outage_count = outage_count + excluded.outage_count
                    """, (int(network_id), str(hour_row['outage_hour']), hour_row['outage_count']))

        # Update property totals
        print(f"  Updating property totals...")
        cursor.execute("""
            UPDATE properties
            SET total_outages = (
                SELECT COUNT(*)
                FROM outages o
                JOIN networks n ON o.network_id = n.network_id
                WHERE n.property_id = properties.property_id
            ),
            last_updated = ?
        """, (datetime.now(),))

        conn.commit()
        print(f"  ✓ Inserted {outages_inserted:,} outages for existing networks")

        total_outages_processed = outages_inserted

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total Outages Processed: {total_outages_processed:,}")
    print(f"Database: {database_path}")
    print(f"{'='*60}\n")

    # Print some sample queries
    print("Sample Database Queries:")
    print("-" * 60)

    cursor.execute("SELECT COUNT(*) FROM properties WHERE total_outages > 0")
    count = cursor.fetchone()[0]
    print(f"Properties with outages in DB: {count}")

    cursor.execute("SELECT COUNT(*) FROM networks")
    count = cursor.fetchone()[0]
    print(f"Total networks in DB: {count}")

    cursor.execute("SELECT COUNT(*) FROM outages")
    count = cursor.fetchone()[0]
    print(f"Total outage records in DB: {count}")

    cursor.execute("SELECT COUNT(*) FROM xpon_shelves")
    count = cursor.fetchone()[0]
    print(f"Total xPON shelves in DB: {count}")

    cursor.execute("SELECT COUNT(*) FROM router_7x50s")
    count = cursor.fetchone()[0]
    print(f"Total 7x50 routers in DB: {count}")

    print("-" * 60)

    # Update report data with final statistics
    report_data['total_outages_processed'] = total_outages_processed

    cursor.execute("SELECT COUNT(*) FROM networks")
    report_data['final_network_count'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM properties")
    report_data['final_property_count'] = cursor.fetchone()[0]

    # Check for property-wide outages and send notification
    print("\nChecking for property-wide outages...")
    cursor = conn.cursor()
    twenty_four_hours_ago = (datetime.now() - pd.Timedelta(hours=24)).isoformat()

    cursor.execute("""
        SELECT
            p.property_name,
            p.island,
            p.total_networks,
            COUNT(DISTINCT n.network_id) as networks_down,
            CAST(COUNT(DISTINCT n.network_id) AS FLOAT) / p.total_networks * 100 as outage_percentage
        FROM properties p
        JOIN networks n ON p.property_id = n.property_id
        JOIN outages o ON n.network_id = o.network_id
        WHERE o.wan_down_start >= ?
            AND p.total_networks > 0
        GROUP BY p.property_id, p.property_name, p.island, p.total_networks
        HAVING outage_percentage >= 75
        ORDER BY outage_percentage DESC
    """, (twenty_four_hours_ago,))

    property_wide_outages = []
    for row in cursor.fetchall():
        property_wide_outages.append({
            'property_name': row[0],
            'island': row[1] or '',
            'total_networks': row[2],
            'networks_down': row[3],
            'outage_percentage': row[4]
        })

    if property_wide_outages:
        print(f"  ⚠ Found {len(property_wide_outages)} property-wide outages (≥75% networks down)")
        notifier.notify_property_wide_outages(property_wide_outages)
    else:
        print(f"  ✓ No property-wide outages detected")

    conn.close()

    # Calculate processing time
    processing_time = time.time() - start_time
    processing_time_str = f"{int(processing_time // 60)}m {int(processing_time % 60)}s"

    # Generate processing report
    print("\nGenerating processing report...")
    report_path = generate_processing_report(report_data)
    print(f"✓ Processing report saved to: {report_path}\n")

    # Send processing complete notification
    notifier.notify_processing_complete(
        filename=os.path.basename(outages_file),
        stats={
            'properties': report_data['final_property_count'],
            'networks': report_data['final_network_count'],
            'outages': total_outages_processed,
            'processing_time': processing_time_str
        }
    )

    return total_outages_processed


def main():
    """Main entry point for the script."""
    # Check virtual environment
    check_venv()

    parser = argparse.ArgumentParser(
        description='Process network outages and optionally Eero discovery data into a database.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process with discovery data
  %(prog)s --outages-file network_outages-2025-11-06.csv --discovery-file eero_discovery.csv

  # Process without discovery data
  %(prog)s --outages-file network_outages-2025-11-06.csv

  # Full example with custom database path
  %(prog)s \\
    --outages-file /path/to/network_outages-2025-11-06.csv \\
    --discovery-file /path/to/Eero_Discovery_Details.csv \\
    --database ./output/outages.db
        """
    )

    parser.add_argument(
        '--outages-file',
        required=True,
        help='Path to the network outages CSV file (contains outage data)'
    )

    parser.add_argument(
        '--discovery-file',
        required=False,
        help='Path to the Eero discovery details CSV file (optional - contains property and network data)'
    )

    parser.add_argument(
        '--database',
        default='./output/outages.db',
        help='Path to the SQLite database file (default: ./output/outages.db)'
    )

    parser.add_argument(
        '--mode',
        choices=['append', 'rebuild'],
        default='append',
        help='Processing mode: "append" keeps existing data and adds new (default), "rebuild" clears all data and rebuilds from scratch'
    )

    parser.add_argument(
        '--retain-days',
        type=int,
        default=7,
        help='Number of days of data to retain when in append mode (default: 7)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )

    args = parser.parse_args()

    # Validate input files
    validate_file(args.outages_file, "Network Outages", required=True)

    # Create output directory if needed
    db_dir = os.path.dirname(args.database)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # Initialize notifier for error handling
    notifier = PushoverNotifier()

    # Process the data
    try:
        num_outages = process_outages_to_db(
            args.outages_file,
            args.discovery_file,
            args.database,
            mode=args.mode,
            retain_days=args.retain_days
        )

        print(f"\n✓ SUCCESS: Processed {num_outages} outages into database")
        print(f"✓ Database ready for web application: {args.database}")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n✗ Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Send error notification
        notifier.notify_processing_error(
            filename=os.path.basename(args.outages_file),
            error_message=str(e)
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
