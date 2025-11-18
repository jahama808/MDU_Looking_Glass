#!/usr/bin/env python3
"""
Script to track and update multi-day outages using the Eero API.

This script identifies outages that may still be ongoing and queries the Eero API
to get their actual end times, fixing the issue where multi-day outages are split
across multiple daily CSV files.

Usage:
    python track_multiday_outages.py [--days N] [--update]
"""

import requests
import sqlite3
import argparse
from datetime import datetime, timedelta
import time
from pushover_notifier import PushoverNotifier

# Configuration
EERO_API_TOKEN = '49925579|dofa12u9hkcopvr801gcqs7hge'
DATABASE_PATH = './output/outages.db'
API_BASE_URL = 'https://api-user.e2ro.com/2.2/organizations/self/network_outages'


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_potentially_ongoing_outages(days_back=3):
    """
    Get outages that might still be ongoing or have incomplete end times.

    Args:
        days_back: Number of days to look back for potentially ongoing outages

    Returns:
        List of outage records
    """
    conn = get_db_connection()

    cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

    # Get outages that might be ongoing or suspicious
    # (very long duration or ended very recently)
    outages = conn.execute("""
        SELECT
            o.outage_id,
            o.network_id,
            o.wan_down_start,
            o.wan_down_end,
            o.reason,
            n.street_address,
            n.subloc,
            p.property_name
        FROM outages o
        JOIN networks n ON o.network_id = n.network_id
        JOIN properties p ON n.property_id = p.property_id
        WHERE o.wan_down_start >= ?
        AND (
            o.wan_down_end IS NULL
            OR julianday(o.wan_down_end) - julianday(o.wan_down_start) > 1
        )
        ORDER BY o.wan_down_start DESC
    """, (cutoff_date,)).fetchall()

    conn.close()
    return outages


def query_eero_outage_api(network_id, start_time):
    """
    Query the Eero API for outage details for a specific network.

    Args:
        network_id: Network ID to query
        start_time: Start time in ISO format (will be converted to GMT)

    Returns:
        API response JSON or None if error
    """
    # Convert start time to GMT if needed
    if isinstance(start_time, str):
        # Remove timezone info and treat as UTC
        start_time = start_time.replace('+00:00', '').replace('Z', '')
        start_time_dt = datetime.fromisoformat(start_time)
    else:
        start_time_dt = start_time

    # Format as required by API (GMT with Z suffix)
    start_param = start_time_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    url = f"{API_BASE_URL}/networks/{network_id}?start={start_param}"
    headers = {
        'X-User-Token': EERO_API_TOKEN
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ✗ API error {response.status_code} for network {network_id}: {response.text}")
            return None

    except Exception as e:
        print(f"  ✗ Exception querying API for network {network_id}: {e}")
        return None


def update_outage_in_db(outage_id, end_time, reason=None):
    """
    Update an outage record with correct end time and reason.

    Args:
        outage_id: Database outage ID
        end_time: Corrected end time
        reason: Updated reason (optional)
    """
    conn = get_db_connection()

    if reason:
        conn.execute("""
            UPDATE outages
            SET wan_down_end = ?, reason = ?
            WHERE outage_id = ?
        """, (end_time, reason, outage_id))
    else:
        conn.execute("""
            UPDATE outages
            SET wan_down_end = ?
            WHERE outage_id = ?
        """, (end_time, outage_id))

    conn.commit()
    conn.close()


def process_multiday_outages(days_back=3, dry_run=True):
    """
    Main function to process and update multi-day outages.

    Args:
        days_back: Number of days to look back
        dry_run: If True, don't actually update the database

    Returns:
        Number of outages updated
    """
    print("\n" + "="*80)
    print("MULTI-DAY OUTAGE TRACKER")
    print("="*80)
    print(f"Mode: {'DRY RUN (no updates)' if dry_run else 'UPDATE DATABASE'}")
    print(f"Looking back: {days_back} days")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get potentially ongoing outages
    print("Querying database for potentially ongoing/multi-day outages...")
    outages = get_potentially_ongoing_outages(days_back)
    print(f"Found {len(outages)} outages to check\n")

    if not outages:
        print("No outages to process.")
        return 0

    updates_made = 0
    errors = 0

    for i, outage in enumerate(outages, 1):
        network_id = outage['network_id']
        outage_id = outage['outage_id']
        start_time = outage['wan_down_start']
        current_end_time = outage['wan_down_end']

        print(f"[{i}/{len(outages)}] Network {network_id} ({outage['property_name']})")
        print(f"  Address: {outage['street_address']} {outage['subloc'] or ''}")
        print(f"  DB Start: {start_time}")
        print(f"  DB End: {current_end_time or 'NULL (ongoing?)'}")

        # Query the Eero API
        api_response = query_eero_outage_api(network_id, start_time)

        if api_response:
            # Parse the API response
            if 'data' in api_response and 'outages' in api_response['data']:
                api_outages = api_response['data']['outages']

                if api_outages:
                    # Find the matching outage (by start time)
                    # API uses 'start' and 'end' fields, not 'wan_down_start'/'wan_down_end'
                    matching_outage = None
                    for api_outage in api_outages:
                        api_start = api_outage.get('start')
                        # Normalize both times for comparison
                        if api_start and api_start.replace('Z', '+00:00') == start_time:
                            matching_outage = api_outage
                            break

                    if matching_outage:
                        api_end_time = matching_outage.get('end')
                        api_reason = matching_outage.get('reason')

                        # Convert API format (Z) to database format (+00:00)
                        if api_end_time:
                            api_end_time = api_end_time.replace('Z', '+00:00')

                        print(f"  API End: {api_end_time or 'NULL'}")
                        print(f"  API Reason: {api_reason or 'Unknown'}")

                        # Check if we need to update
                        needs_update = False

                        if api_end_time and api_end_time != current_end_time:
                            needs_update = True
                            print(f"  ⚠ End time mismatch! Will update to: {api_end_time}")

                        if needs_update:
                            if not dry_run:
                                update_outage_in_db(outage_id, api_end_time, api_reason)
                                print(f"  ✓ Updated outage {outage_id}")
                                updates_made += 1
                            else:
                                print(f"  → Would update outage {outage_id} (dry run)")
                                updates_made += 1
                        else:
                            print(f"  ✓ No update needed")
                    else:
                        print(f"  ⚠ No matching outage found in API response")
                else:
                    print(f"  ℹ No outages in API response (may have been resolved)")
            else:
                print(f"  ⚠ Unexpected API response format")
                errors += 1
        else:
            print(f"  ✗ Failed to get API response")
            errors += 1

        print()

        # Rate limiting - be nice to the API
        time.sleep(0.5)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Outages checked: {len(outages)}")
    print(f"Updates {'made' if not dry_run else 'needed'}: {updates_made}")
    print(f"Errors: {errors}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    return updates_made


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Track and update multi-day outages using the Eero API.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check for multi-day outages in the past 3 days (dry run)
  %(prog)s

  # Check for multi-day outages in the past 7 days (dry run)
  %(prog)s --days 7

  # Actually update the database with corrected end times
  %(prog)s --update

  # Update outages from the past 5 days
  %(prog)s --days 5 --update
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=3,
        help='Number of days to look back for outages (default: 3)'
    )

    parser.add_argument(
        '--update',
        action='store_true',
        help='Actually update the database (default is dry run)'
    )

    parser.add_argument(
        '--notify',
        action='store_true',
        help='Send Pushover notification when updates are made'
    )

    args = parser.parse_args()

    # Process outages
    try:
        updates = process_multiday_outages(
            days_back=args.days,
            dry_run=not args.update
        )

        # Send notification if requested
        if args.notify and args.update and updates > 0:
            notifier = PushoverNotifier()
            notifier.send_notification(
                message=f"Updated {updates} multi-day outage(s) with corrected end times from Eero API.",
                title="Multi-Day Outages Updated",
                priority=0,
                sound="climb"
            )

        if not args.update and updates > 0:
            print(f"ℹ️  DRY RUN MODE: {updates} outage(s) would be updated.")
            print("   Run with --update to actually update the database.")

    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
