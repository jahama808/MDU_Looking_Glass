#!/usr/bin/env python3
"""
Script to track ongoing network outages using the Eero API.

This script identifies networks with recent outages and queries the Eero API
to check if they are still experiencing outages (no end time). Stores ongoing
outages in the ongoing_outages table for real-time visibility.

Usage:
    python track_ongoing_outages.py [--lookback-hours N] [--notify]
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


def get_networks_with_recent_outages(lookback_hours=48):
    """
    Get networks that had outages in the past N hours.
    These are candidates for ongoing outage checks.

    Args:
        lookback_hours: Number of hours to look back for recent outages

    Returns:
        List of network records
    """
    conn = get_db_connection()

    cutoff_time = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()

    # Get networks with recent outages (either in outages or ongoing_outages table)
    networks = conn.execute("""
        SELECT DISTINCT
            n.network_id,
            n.street_address,
            n.subloc,
            p.property_name,
            p.island,
            MAX(o.wan_down_start) as last_outage_start
        FROM networks n
        JOIN properties p ON n.property_id = p.property_id
        LEFT JOIN outages o ON n.network_id = o.network_id
        WHERE o.wan_down_start >= ?
        GROUP BY n.network_id, n.street_address, n.subloc, p.property_name, p.island

        UNION

        SELECT DISTINCT
            n.network_id,
            n.street_address,
            n.subloc,
            p.property_name,
            p.island,
            MAX(oo.wan_down_start) as last_outage_start
        FROM networks n
        JOIN properties p ON n.property_id = p.property_id
        LEFT JOIN ongoing_outages oo ON n.network_id = oo.network_id
        WHERE oo.wan_down_start >= ?
        GROUP BY n.network_id, n.street_address, n.subloc, p.property_name, p.island

        ORDER BY last_outage_start DESC
    """, (cutoff_time, cutoff_time)).fetchall()

    conn.close()
    return networks


def query_eero_outage_api(network_id, lookback_hours=48):
    """
    Query the Eero API for outage details for a specific network.

    Args:
        network_id: Network ID to query
        lookback_hours: How far back to query (default 48 hours)

    Returns:
        API response JSON or None if error
    """
    # Calculate start time
    start_time_dt = datetime.now() - timedelta(hours=lookback_hours)
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


def store_ongoing_outage(network_id, start_time, end_time=None, reason=None):
    """
    Store or update an ongoing outage in the database.

    Args:
        network_id: Network ID
        start_time: Outage start time (ISO format)
        end_time: Outage end time if resolved (ISO format)
        reason: Outage reason
    """
    conn = get_db_connection()
    now = datetime.now().isoformat()

    # Convert API format (Z) to database format (+00:00)
    if start_time:
        start_time = start_time.replace('Z', '+00:00')
    if end_time:
        end_time = end_time.replace('Z', '+00:00')

    # Check if this ongoing outage already exists
    existing = conn.execute("""
        SELECT ongoing_outage_id, wan_down_end
        FROM ongoing_outages
        WHERE network_id = ? AND wan_down_start = ?
    """, (network_id, start_time)).fetchone()

    if existing:
        # Update existing record
        conn.execute("""
            UPDATE ongoing_outages
            SET wan_down_end = ?, reason = ?, last_checked = ?
            WHERE ongoing_outage_id = ?
        """, (end_time, reason, now, existing['ongoing_outage_id']))
    else:
        # Insert new ongoing outage
        conn.execute("""
            INSERT INTO ongoing_outages (network_id, wan_down_start, wan_down_end, reason, first_detected, last_checked)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (network_id, start_time, end_time, reason, now, now))

    conn.commit()
    conn.close()


def remove_resolved_outage(network_id, start_time):
    """
    Remove an outage from ongoing_outages table (it has been resolved).

    Args:
        network_id: Network ID
        start_time: Outage start time
    """
    conn = get_db_connection()

    # Convert API format (Z) to database format (+00:00)
    start_time = start_time.replace('Z', '+00:00')

    conn.execute("""
        DELETE FROM ongoing_outages
        WHERE network_id = ? AND wan_down_start = ?
    """, (network_id, start_time))

    conn.commit()
    conn.close()


def track_ongoing_outages(lookback_hours=48):
    """
    Main function to track ongoing outages.

    Args:
        lookback_hours: Number of hours to look back for recent outages

    Returns:
        Dictionary with statistics
    """
    print("\n" + "="*80)
    print("ONGOING OUTAGE TRACKER")
    print("="*80)
    print(f"Lookback window: {lookback_hours} hours")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get networks with recent outages
    print("Querying database for networks with recent outages...")
    networks = get_networks_with_recent_outages(lookback_hours)
    print(f"Found {len(networks)} networks to check\n")

    if not networks:
        print("No networks with recent outages found.")
        return {
            'networks_checked': 0,
            'ongoing_outages_found': 0,
            'resolved_outages': 0,
            'errors': 0
        }

    ongoing_count = 0
    resolved_count = 0
    errors = 0

    for i, network in enumerate(networks, 1):
        network_id = network['network_id']

        print(f"[{i}/{len(networks)}] Network {network_id}")
        print(f"  Property: {network['property_name']}")
        print(f"  Address: {network['street_address']} {network['subloc'] or ''}")

        # Query the Eero API
        api_response = query_eero_outage_api(network_id, lookback_hours)

        if api_response:
            # Parse the API response
            if 'data' in api_response and 'outages' in api_response['data']:
                api_outages = api_response['data']['outages']

                if api_outages:
                    # Check each outage from the API
                    for outage in api_outages:
                        start_time = outage.get('start')
                        end_time = outage.get('end')
                        reason = outage.get('reason')

                        if not end_time:
                            # This is an ongoing outage!
                            print(f"  🔴 ONGOING OUTAGE detected")
                            print(f"     Start: {start_time}")
                            print(f"     Reason: {reason or 'Unknown'}")

                            # Store in ongoing_outages table
                            store_ongoing_outage(network_id, start_time, None, reason)
                            ongoing_count += 1
                        else:
                            # This outage has ended - remove from ongoing if it exists
                            remove_resolved_outage(network_id, start_time)
                            resolved_count += 1
                else:
                    print(f"  ✓ No outages in API response")
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
    print(f"Networks checked: {len(networks)}")
    print(f"Ongoing outages found: {ongoing_count}")
    print(f"Resolved outages: {resolved_count}")
    print(f"Errors: {errors}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    return {
        'networks_checked': len(networks),
        'ongoing_outages_found': ongoing_count,
        'resolved_outages': resolved_count,
        'errors': errors
    }


def get_current_ongoing_outages():
    """
    Get all currently ongoing outages from the database.

    Returns:
        List of ongoing outage records
    """
    conn = get_db_connection()

    outages = conn.execute("""
        SELECT
            oo.ongoing_outage_id,
            oo.network_id,
            oo.wan_down_start,
            oo.wan_down_end,
            oo.reason,
            oo.first_detected,
            oo.last_checked,
            n.street_address,
            n.subloc,
            p.property_name,
            p.island
        FROM ongoing_outages oo
        JOIN networks n ON oo.network_id = n.network_id
        JOIN properties p ON n.property_id = p.property_id
        WHERE oo.wan_down_end IS NULL
        ORDER BY oo.wan_down_start DESC
    """).fetchall()

    conn.close()
    return outages


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Track ongoing network outages using the Eero API.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check for ongoing outages (48 hour lookback)
  %(prog)s

  # Check with 24 hour lookback
  %(prog)s --lookback-hours 24

  # Check and send Pushover notification if ongoing outages found
  %(prog)s --notify

  # List current ongoing outages without checking API
  %(prog)s --list-only
        """
    )

    parser.add_argument(
        '--lookback-hours',
        type=int,
        default=48,
        help='Number of hours to look back for recent outages (default: 48)'
    )

    parser.add_argument(
        '--notify',
        action='store_true',
        help='Send Pushover notification if ongoing outages are found'
    )

    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Only list current ongoing outages without checking API'
    )

    args = parser.parse_args()

    try:
        if args.list_only:
            # Just list current ongoing outages
            print("\n" + "="*80)
            print("CURRENT ONGOING OUTAGES")
            print("="*80)

            outages = get_current_ongoing_outages()

            if outages:
                print(f"\nFound {len(outages)} ongoing outage(s):\n")
                for i, outage in enumerate(outages, 1):
                    start_time = datetime.fromisoformat(outage['wan_down_start'].replace('+00:00', ''))
                    duration = datetime.now() - start_time
                    hours = int(duration.total_seconds() / 3600)

                    print(f"{i}. Network {outage['network_id']}")
                    print(f"   Property: {outage['property_name']} ({outage['island']})")
                    print(f"   Address: {outage['street_address']} {outage['subloc'] or ''}")
                    print(f"   Start: {outage['wan_down_start']}")
                    print(f"   Duration: {hours} hours")
                    print(f"   Reason: {outage['reason'] or 'Unknown'}")
                    print()
            else:
                print("\n✓ No ongoing outages found\n")

            print("="*80 + "\n")
            return 0

        # Track ongoing outages
        stats = track_ongoing_outages(lookback_hours=args.lookback_hours)

        # Send notification if requested and ongoing outages found
        if args.notify and stats['ongoing_outages_found'] > 0:
            notifier = PushoverNotifier()

            # Get the ongoing outages for details
            outages = get_current_ongoing_outages()

            message = f"Found {stats['ongoing_outages_found']} ongoing outage(s)\n\n"

            # Add details for up to 5 outages
            for i, outage in enumerate(outages[:5], 1):
                start_time = datetime.fromisoformat(outage['wan_down_start'].replace('+00:00', ''))
                duration = datetime.now() - start_time
                hours = int(duration.total_seconds() / 3600)

                message += f"{i}. {outage['property_name']}\n"
                message += f"   Network {outage['network_id']}\n"
                message += f"   Duration: {hours}h\n"

            if len(outages) > 5:
                message += f"\n... and {len(outages) - 5} more"

            notifier.send_notification(
                message=message,
                title="Ongoing Outages Detected",
                priority=1,
                sound="siren"
            )

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
