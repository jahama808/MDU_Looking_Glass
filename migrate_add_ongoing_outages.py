#!/usr/bin/env python3
"""
Migration script to add ongoing_outages table to the property outages database.

This table tracks current/unresolved network outages for real-time monitoring.

Usage:
    python migrate_add_ongoing_outages.py [--database path/to/database.db]
"""

import sqlite3
import argparse
import sys
from datetime import datetime


def add_ongoing_outages_table(db_path):
    """Add ongoing_outages table to the database."""
    print(f"Connecting to database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='ongoing_outages'
        """)
        existing = cursor.fetchone()

        if existing:
            print("⚠️  ongoing_outages table already exists!")
            response = input("Do you want to recreate it? This will DELETE all ongoing outage data! (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False

            print("Dropping existing table...")
            cursor.execute("DROP TABLE IF EXISTS ongoing_outages")

        print("Creating ongoing_outages table...")
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

        # Create indexes for better performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ongoing_network_id ON ongoing_outages(network_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ongoing_wan_down_end ON ongoing_outages(wan_down_end)")

        conn.commit()
        print("✓ ongoing_outages table created successfully!")

        # Show table info
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"✓ Database now has {table_count} tables")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Add ongoing_outages table to property outages database'
    )
    parser.add_argument(
        '--database',
        default='property_outages.db',
        help='Path to SQLite database (default: property_outages.db)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Ongoing Outages Table Migration")
    print("=" * 60)
    print()

    success = add_ongoing_outages_table(args.database)

    print()
    if success:
        print("Migration completed successfully!")
        print()
        print("The ongoing_outages table is now available for tracking")
        print("real-time network outages.")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
