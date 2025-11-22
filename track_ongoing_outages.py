#!/usr/bin/env python3
"""
Script to track ongoing network outages using the Eero bulk API.

This script fetches all currently ongoing outages from the Eero API and updates
the ongoing_outages table for networks in our database. Much more efficient than
the old method of querying individual networks.

Usage:
    python track_ongoing_outages.py [--notify] [--dry-run]
"""

import requests
import sqlite3
import argparse
from datetime import datetime
from urllib.parse import urljoin
from pushover_notifier import PushoverNotifier

# Configuration
EERO_API_TOKEN = '49925579|dofa12u9hkcopvr801gcqs7hge'
DATABASE_PATH = 'property_outages.db'
API_BASE_URL = 'https://api-user.e2ro.com'
BULK_OUTAGES_ENDPOINT = '/2.2/organizations/self/network_outages/networks'


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all_ongoing_outages():
    """
    Fetch all pages of ongoing outages from the Eero bulk API.

    Returns:
        List of network outage dictionaries with end_time=null
    """
    all_ongoing = []
    url = BULK_OUTAGES_ENDPOINT
    headers = {'X-User-Token': EERO_API_TOKEN}
    page = 1

    print(f"Fetching ongoing outages from Eero API...")

    while url:
        full_url = urljoin(API_BASE_URL, url)

        try:
            response = requests.get(full_url, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"  ✗ API error {response.status_code} on page {page}")
                print(f"    Response: {response.text[:200]}")
                break

            data = response.json()

            if 'data' in data and 'networks' in data['data']:
                networks = data['data']['networks']

                # Filter for ongoing outages (end_time is null)
                ongoing = [n for n in networks if n.get('end_time') is None]
                all_ongoing.extend(ongoing)

                print(f"  Page {page}: {len(ongoing)} ongoing outages")
            else:
                print(f"  ✗ Unexpected response format on page {page}")
                break

            # Check for next page
            if 'pagination' in data and 'next' in data['pagination']:
                url = data['pagination']['next']
                page += 1
            else:
                url = None

        except Exception as e:
            print(f"  ✗ Exception on page {page}: {e}")
            break

    print(f"  Total ongoing outages from API: {len(all_ongoing)}")
    return all_ongoing


def get_db_network_ids():
    """
    Get all network IDs in our database.

    Returns:
        Set of network IDs
    """
    conn = get_db_connection()
    networks = conn.execute("SELECT network_id FROM networks").fetchall()
    conn.close()

    return set(row['network_id'] for row in networks)


def get_current_tracked_outages():
    """
    Get currently tracked ongoing outages from database.

    Returns:
        Dict mapping network_id to outage record
    """
    conn = get_db_connection()

    outages = conn.execute("""
        SELECT ongoing_outage_id, network_id, wan_down_start
        FROM ongoing_outages
        WHERE wan_down_end IS NULL
    """).fetchall()

    conn.close()

    return {row['network_id']: dict(row) for row in outages}


def store_or_update_outage(network_id, start_time, reason=None, dry_run=False):
    """
    Store or update an ongoing outage in the database.

    Args:
        network_id: Network ID
        start_time: Outage start time (ISO format from API)
        reason: Outage reason (usually None/Unknown from this API)
        dry_run: If True, don't actually update database

    Returns:
        'inserted' or 'updated' or 'unchanged'
    """
    if dry_run:
        return 'dry_run'

    conn = get_db_connection()
    now = datetime.now().isoformat()

    # Convert API format (Z) to database format (+00:00)
    start_time_db = start_time.replace('Z', '+00:00')

    # Check if this outage already exists
    existing = conn.execute("""
        SELECT ongoing_outage_id, wan_down_start, last_checked
        FROM ongoing_outages
        WHERE network_id = ? AND wan_down_end IS NULL
    """, (network_id,)).fetchone()

    if existing:
        # Check if it's the same outage (same start time)
        if existing['wan_down_start'] == start_time_db:
            # Just update last_checked timestamp
            conn.execute("""
                UPDATE ongoing_outages
                SET last_checked = ?
                WHERE ongoing_outage_id = ?
            """, (now, existing['ongoing_outage_id']))
            conn.commit()
            conn.close()
            return 'updated'
        else:
            # Different outage - close the old one and insert new one
            conn.execute("""
                UPDATE ongoing_outages
                SET wan_down_end = ?, last_checked = ?
                WHERE ongoing_outage_id = ?
            """, (start_time_db, now, existing['ongoing_outage_id']))

            conn.execute("""
                INSERT INTO ongoing_outages
                (network_id, wan_down_start, wan_down_end, reason, first_detected, last_checked)
                VALUES (?, ?, NULL, ?, ?, ?)
            """, (network_id, start_time_db, reason or 'Unknown', now, now))

            conn.commit()
            conn.close()
            return 'inserted'
    else:
        # New outage - insert it
        conn.execute("""
            INSERT INTO ongoing_outages
            (network_id, wan_down_start, wan_down_end, reason, first_detected, last_checked)
            VALUES (?, ?, NULL, ?, ?, ?)
        """, (network_id, start_time_db, reason or 'Unknown', now, now))

        conn.commit()
        conn.close()
        return 'inserted'


def remove_stale_outages(current_outage_network_ids, dry_run=False):
    """
    Remove outages from database that are no longer in the API response.

    Args:
        current_outage_network_ids: Set of network IDs currently down (from API)
        dry_run: If True, don't actually update database

    Returns:
        Number of stale outages removed
    """
    conn = get_db_connection()

    # Get all tracked ongoing outages
    tracked = conn.execute("""
        SELECT ongoing_outage_id, network_id
        FROM ongoing_outages
        WHERE wan_down_end IS NULL
    """).fetchall()

    stale_count = 0
    now = datetime.now().isoformat()

    for row in tracked:
        if row['network_id'] not in current_outage_network_ids:
            # This outage is no longer in API - mark as resolved
            if not dry_run:
                conn.execute("""
                    UPDATE ongoing_outages
                    SET wan_down_end = ?, last_checked = ?
                    WHERE ongoing_outage_id = ?
                """, (now, now, row['ongoing_outage_id']))
            stale_count += 1

    if not dry_run:
        conn.commit()

    conn.close()
    return stale_count


def track_ongoing_outages(notify=False, dry_run=False):
    """
    Main function to track ongoing outages using the bulk API.

    Args:
        notify: Send Pushover notification if ongoing outages found
        dry_run: Don't update database, just report what would happen

    Returns:
        Dictionary with statistics
    """
    print("\n" + "="*80)
    print("ONGOING OUTAGE TRACKER (BULK API)")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if dry_run:
        print("DRY RUN MODE - No database changes will be made")
    print()

    # Fetch all ongoing outages from API
    api_outages = fetch_all_ongoing_outages()

    # Get networks in our database
    print("\nChecking database...")
    db_network_ids = get_db_network_ids()
    print(f"  Networks in database: {len(db_network_ids)}")

    # Filter for outages affecting our networks
    our_outages = [o for o in api_outages if o['network_id'] in db_network_ids]
    print(f"  Ongoing outages affecting our networks: {len(our_outages)}")

    # Get currently tracked outages
    currently_tracked = get_current_tracked_outages()
    print(f"  Currently tracked in database: {len(currently_tracked)}")
    print()

    # Process outages
    print("Processing outages...")
    inserted = 0
    updated = 0

    current_outage_network_ids = set()

    for outage in our_outages:
        network_id = outage['network_id']
        start_time = outage['start_time']

        current_outage_network_ids.add(network_id)

        result = store_or_update_outage(network_id, start_time, dry_run=dry_run)

        if result == 'inserted':
            inserted += 1
            duration_hours = outage.get('duration', 0) / 3600
            print(f"  ✓ NEW: Network {network_id} (down {duration_hours:.1f}h)")
        elif result == 'updated':
            updated += 1

    # Remove stale outages
    print("\nRemoving stale outages...")
    stale_removed = remove_stale_outages(current_outage_network_ids, dry_run=dry_run)
    if stale_removed > 0:
        print(f"  ✓ Removed {stale_removed} resolved outage(s)")
    else:
        print(f"  No stale outages to remove")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total ongoing outages in API: {len(api_outages)}")
    print(f"Affecting our networks: {len(our_outages)}")
    print(f"New outages added: {inserted}")
    print(f"Existing outages updated: {updated}")
    print(f"Stale outages removed: {stale_removed}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    stats = {
        'total_api_outages': len(api_outages),
        'our_networks_affected': len(our_outages),
        'new_outages': inserted,
        'updated_outages': updated,
        'stale_removed': stale_removed
    }

    # Send notification if requested
    if notify and not dry_run and (inserted > 0 or len(our_outages) > 5):
        send_notification(our_outages, inserted)

    return stats


def send_notification(our_outages, new_count):
    """
    Send Pushover notification about ongoing outages.

    Args:
        our_outages: List of outages affecting our networks
        new_count: Number of new outages detected
    """
    try:
        notifier = PushoverNotifier()

        message = f"Ongoing outages: {len(our_outages)}"
        if new_count > 0:
            message += f"\nNew outages: {new_count}"

        # Add details for longest outages
        sorted_outages = sorted(our_outages, key=lambda x: x.get('duration', 0), reverse=True)

        if sorted_outages:
            message += "\n\nLongest outages:"
            for outage in sorted_outages[:5]:
                duration_hours = outage.get('duration', 0) / 3600
                message += f"\n• Network {outage['network_id']}: {duration_hours:.1f}h"

        notifier.send_notification(
            message=message,
            title="Network Outages Update",
            priority=0 if new_count == 0 else 1,
            sound="intermission" if new_count == 0 else "siren"
        )

        print("Pushover notification sent")

    except Exception as e:
        print(f"Failed to send notification: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Track ongoing network outages using the Eero bulk API.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update ongoing outages tracking
  %(prog)s

  # Send Pushover notification if outages detected
  %(prog)s --notify

  # Dry run - see what would happen without updating database
  %(prog)s --dry-run
        """
    )

    parser.add_argument(
        '--notify',
        action='store_true',
        help='Send Pushover notification if ongoing outages are found'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - report changes without updating database'
    )

    args = parser.parse_args()

    try:
        stats = track_ongoing_outages(notify=args.notify, dry_run=args.dry_run)
        return 0

    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
