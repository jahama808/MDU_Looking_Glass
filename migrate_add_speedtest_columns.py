#!/usr/bin/env python3
"""
Database Migration Script: Add Speedtest Columns

This script adds speedtest-related columns to the networks table:
- download_target: Target download speed in Mbps
- upload_target: Target upload speed in Mbps
- gateway_speed_down: Actual download speed in Mbps
- gateway_speed_up: Actual upload speed in Mbps
- speed_test_date: Date of the speed test
"""

import sqlite3
import sys

DATABASE = './output/outages.db'

def migrate_database():
    """Add new speedtest columns to networks table."""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        print("Starting database migration...")
        print(f"Database: {DATABASE}\n")

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(networks)")
        network_cols = [col[1] for col in cursor.fetchall()]

        # Add speedtest columns to networks if they don't exist
        columns_to_add = [
            ('download_target', 'REAL'),
            ('upload_target', 'REAL'),
            ('gateway_speed_down', 'REAL'),
            ('gateway_speed_up', 'REAL'),
            ('speed_test_date', 'TEXT')
        ]

        for col_name, col_type in columns_to_add:
            if col_name not in network_cols:
                print(f"Adding '{col_name}' column to networks...")
                cursor.execute(f"ALTER TABLE networks ADD COLUMN {col_name} {col_type}")
                print(f"✓ Added '{col_name}' column")
            else:
                print(f"• '{col_name}' column already exists in networks")

        conn.commit()
        conn.close()

        print("\n✓ Migration completed successfully!")
        print("\nNote: The new columns are empty. You need to reprocess your data")
        print("to populate them. Run:")
        print("  python process_property_outages_db.py --connectivity-file <file> --discovery-file <file> --mode rebuild")

        return 0

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(migrate_database())
