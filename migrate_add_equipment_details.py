#!/usr/bin/env python3
"""
Database Migration Script: Add Equipment Details Columns

This script adds the slots, pons, and saps columns to the database
to support displaying detailed equipment information.
"""

import sqlite3
import sys

DATABASE = './output/outages.db'

def migrate_database():
    """Add new columns to existing tables."""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        print("Starting database migration...")
        print(f"Database: {DATABASE}\n")

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(property_xpon_shelves)")
        xpon_cols = [col[1] for col in cursor.fetchall()]

        cursor.execute("PRAGMA table_info(property_7x50s)")
        router_cols = [col[1] for col in cursor.fetchall()]

        # Add slots and pons columns to property_xpon_shelves if they don't exist
        if 'slots' not in xpon_cols:
            print("Adding 'slots' column to property_xpon_shelves...")
            cursor.execute("ALTER TABLE property_xpon_shelves ADD COLUMN slots TEXT")
            print("✓ Added 'slots' column")
        else:
            print("• 'slots' column already exists in property_xpon_shelves")

        if 'pons' not in xpon_cols:
            print("Adding 'pons' column to property_xpon_shelves...")
            cursor.execute("ALTER TABLE property_xpon_shelves ADD COLUMN pons TEXT")
            print("✓ Added 'pons' column")
        else:
            print("• 'pons' column already exists in property_xpon_shelves")

        # Add saps column to property_7x50s if it doesn't exist
        if 'saps' not in router_cols:
            print("Adding 'saps' column to property_7x50s...")
            cursor.execute("ALTER TABLE property_7x50s ADD COLUMN saps TEXT")
            print("✓ Added 'saps' column")
        else:
            print("• 'saps' column already exists in property_7x50s")

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
