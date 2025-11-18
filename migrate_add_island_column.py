#!/usr/bin/env python3
"""
Database Migration: Add island column to properties table

This migration:
1. Adds an 'island' column to the properties table
2. Detects and populates island for all existing properties based on their networks
"""

import sqlite3
import sys
from island_detector import detect_island


DATABASE = './output/outages.db'


def migrate():
    """Add island column and populate data."""
    print("\n" + "="*80)
    print("DATABASE MIGRATION: Add Island Column to Properties")
    print("="*80)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Step 1: Check if column already exists
    print("\nStep 1: Checking if island column exists...")
    cursor.execute("PRAGMA table_info(properties)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'island' in columns:
        print("  ⚠️  Column 'island' already exists. Skipping column creation.")
    else:
        print("  Adding 'island' column to properties table...")
        cursor.execute("ALTER TABLE properties ADD COLUMN island TEXT")
        conn.commit()
        print("  ✓ Column added successfully")

    # Step 2: Populate island data for existing properties
    print("\nStep 2: Detecting and populating island data...")

    # Get all properties
    cursor.execute("SELECT property_id, property_name FROM properties")
    properties = cursor.fetchall()

    print(f"  Found {len(properties)} properties to process")

    updated_count = 0
    failed_count = 0
    island_stats = {}

    for property_id, property_name in properties:
        # Get all networks from this property to find one with location data
        cursor.execute("""
            SELECT city, postal_code, latitude, longitude
            FROM networks
            WHERE property_id = ?
            AND (city IS NOT NULL OR postal_code IS NOT NULL OR latitude IS NOT NULL)
        """, (property_id,))

        networks = cursor.fetchall()

        if not networks:
            # No networks with location data, try to infer from property name
            island = None
            # Check if property name contains island keywords
            name_upper = property_name.upper()
            if 'WAIKIKI' in name_upper or 'HONOLULU' in name_upper or 'ALA MOANA' in name_upper:
                island = 'Oahu'
            elif 'KAANAPALI' in name_upper or 'LAHAINA' in name_upper or 'WAILEA' in name_upper or 'KIHEI' in name_upper:
                island = 'Maui'
            elif 'KONA' in name_upper or 'HILO' in name_upper or 'WAIKOLOA' in name_upper:
                island = 'Hawaii'
            elif 'POIPU' in name_upper or 'PRINCEVILLE' in name_upper or 'KAPAA' in name_upper:
                island = 'Kauai'

            if not island:
                print(f"  ⚠️  No location data for property: {property_name}")
                failed_count += 1
                continue
        else:
            # Try each network until we find an island
            island = None
            for city, postal_code, latitude, longitude in networks:
                # Handle bytes postal_code
                if isinstance(postal_code, bytes):
                    postal_code = None

                # Detect island
                island = detect_island(
                    city=city,
                    postal_code=postal_code,
                    latitude=latitude,
                    longitude=longitude
                )

                if island:
                    break

        if island:
            # Update property with island
            cursor.execute("""
                UPDATE properties
                SET island = ?
                WHERE property_id = ?
            """, (island, property_id))

            updated_count += 1
            island_stats[island] = island_stats.get(island, 0) + 1
        else:
            print(f"  ⚠️  Could not detect island for: {property_name}")
            print(f"      City: {city}, ZIP: {postal_code}, Coords: ({latitude}, {longitude})")
            failed_count += 1

    conn.commit()

    # Step 3: Summary
    print("\n" + "="*80)
    print("MIGRATION SUMMARY")
    print("="*80)
    print(f"Total properties: {len(properties)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed to detect: {failed_count}")

    if island_stats:
        print("\nProperties by Island:")
        for island in sorted(island_stats.keys()):
            print(f"  {island}: {island_stats[island]}")

    # Verify the migration
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)

    cursor.execute("""
        SELECT island, COUNT(*) as count
        FROM properties
        GROUP BY island
        ORDER BY count DESC
    """)

    print("\nProperties table - Island distribution:")
    for row in cursor.fetchall():
        island = row[0] if row[0] else 'NULL'
        count = row[1]
        print(f"  {island}: {count}")

    conn.close()

    print("\n✓ Migration completed successfully!")
    return updated_count, failed_count


if __name__ == '__main__':
    try:
        updated, failed = migrate()

        if failed > 0:
            print(f"\n⚠️  Warning: {failed} properties could not be assigned an island")
            print("   These properties may need manual review.")
            sys.exit(0)
        else:
            print("\n✓ All properties successfully assigned to islands!")
            sys.exit(0)

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
