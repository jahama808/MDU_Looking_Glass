#!/usr/bin/env python3
"""
Simple Flask API for Property Outage Database

This provides a REST API to query the outage database.

Install dependencies:
    pip install flask flask-cors

Run the server:
    python api_server.py

API will be available at http://localhost:5000
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import anthropic
import hashlib
import json


# Check if running in virtual environment
def check_venv():
    """Check if script is running in a virtual environment."""
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠️  WARNING: Not running in a virtual environment!")
        print("   Flask and dependencies may not be available.")
        print("   Run: source venv/bin/activate  (or venv\\Scripts\\activate on Windows)")
        print()
        sys.exit(1)


# Run check before creating app
check_venv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Database configuration
DATABASE = os.environ.get('OUTAGES_DB', './output/outages.db')

# Cache for AI analysis - stores analysis until input data changes
# Format: {cache_key: {'analysis': ..., 'timestamp': ..., 'data_hash': ...}}
analysis_cache = {}


def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


@app.route('/')
def index():
    """API documentation."""
    return jsonify({
        'name': 'Property Outage API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/properties': 'Get all properties with outages',
            'GET /api/property/<id>': 'Get property details',
            'GET /api/property/<id>/hourly': 'Get hourly outage data for property',
            'GET /api/property/<id>/networks': 'Get networks for property',
            'GET /api/network/<id>': 'Get network details',
            'GET /api/network/<id>/hourly': 'Get hourly outage data for network',
            'GET /api/xpon-shelves': 'Get all xPON shelves',
            'GET /api/xpon-shelf/<id>': 'Get xPON shelf details and associated properties',
            'GET /api/7x50s': 'Get all 7x50 routers',
            'GET /api/7x50/<id>': 'Get 7x50 router details and associated properties',
            'GET /api/property-wide-outages': 'Get properties with property-wide outages in last 24 hours',
            'GET /api/speedtest-performance': 'Get speedtest performance for all properties',
            'GET /api/speedtest-performance-table': 'Get speedtest performance with equipment details for table view',
            'GET /api/stats': 'Get overall statistics'
        }
    })


@app.route('/api/properties')
def get_properties():
    """Get all properties with outage count from the past 24 hours."""
    conn = get_db_connection()

    # Calculate 24 hours ago
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    properties = conn.execute("""
        SELECT
            p.property_id,
            p.property_name,
            p.total_networks,
            COALESCE(COUNT(DISTINCT CASE WHEN o.wan_down_start >= ? THEN o.outage_id END), 0) as total_outages,
            p.island,
            p.last_updated
        FROM properties p
        LEFT JOIN networks n ON p.property_id = n.property_id
        LEFT JOIN outages o ON n.network_id = o.network_id
        GROUP BY p.property_id, p.property_name, p.total_networks, p.island, p.last_updated
        ORDER BY total_outages DESC, p.property_name ASC
    """, (twenty_four_hours_ago.isoformat(),)).fetchall()
    conn.close()

    return jsonify([dict(p) for p in properties])


@app.route('/api/property/<int:property_id>')
def get_property(property_id):
    """Get detailed information about a specific property."""
    conn = get_db_connection()
    
    # Get property info
    property_info = conn.execute("""
        SELECT property_id, property_name, total_networks, total_outages, island, last_updated
        FROM properties
        WHERE property_id = ?
    """, (property_id,)).fetchone()
    
    if not property_info:
        conn.close()
        return jsonify({'error': 'Property not found'}), 404
    
    # Get top networks
    top_networks = conn.execute("""
        SELECT network_id, street_address, subloc, total_outages
        FROM networks
        WHERE property_id = ?
        AND total_outages > 0
        ORDER BY total_outages DESC
        LIMIT 5
    """, (property_id,)).fetchall()

    # Get associated xPON shelves
    xpon_shelves = conn.execute("""
        SELECT xs.shelf_id, xs.shelf_name, pxs.network_count, pxs.slots, pxs.pons
        FROM xpon_shelves xs
        JOIN property_xpon_shelves pxs ON xs.shelf_id = pxs.shelf_id
        WHERE pxs.property_id = ?
        ORDER BY pxs.network_count DESC
    """, (property_id,)).fetchall()

    # Get associated 7x50 routers
    routers_7x50 = conn.execute("""
        SELECT r.router_id, r.router_name, p7.network_count, p7.saps
        FROM router_7x50s r
        JOIN property_7x50s p7 ON r.router_id = p7.router_id
        WHERE p7.property_id = ?
        ORDER BY p7.network_count DESC
    """, (property_id,)).fetchall()

    conn.close()

    return jsonify({
        'property': dict(property_info),
        'top_networks': [dict(n) for n in top_networks],
        'xpon_shelves': [dict(xs) for xs in xpon_shelves],
        'routers_7x50': [dict(r) for r in routers_7x50]
    })


@app.route('/api/property/<int:property_id>/hourly')
def get_property_hourly(property_id):
    """Get hourly outage data for a property (most recent 24 hours of data)."""
    conn = get_db_connection()

    # Get the most recent 24 hours of data that exists for this property
    # (not 24 hours from now, but the most recent 24 hours worth of data)
    hourly = conn.execute("""
        SELECT outage_hour, total_outage_count
        FROM property_hourly_outages
        WHERE property_id = ?
        AND outage_hour >= (
            SELECT datetime(MAX(outage_hour), '-24 hours')
            FROM property_hourly_outages
            WHERE property_id = ?
        )
        ORDER BY outage_hour
    """, (property_id, property_id)).fetchall()

    conn.close()

    return jsonify([dict(h) for h in hourly])


@app.route('/api/property/<int:property_id>/hourly-7days')
def get_property_hourly_7days(property_id):
    """Get hourly outage data for a property for the last 7 days."""
    conn = get_db_connection()

    # Calculate the cutoff date (7 days ago)
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

    hourly = conn.execute("""
        SELECT outage_hour, total_outage_count
        FROM property_hourly_outages
        WHERE property_id = ?
        AND outage_hour >= ?
        ORDER BY outage_hour
    """, (property_id, seven_days_ago)).fetchall()

    conn.close()

    return jsonify([dict(h) for h in hourly])


@app.route('/api/property/<int:property_id>/networks')
def get_property_networks(property_id):
    """Get all networks for a property, including chronic problem network detection."""
    conn = get_db_connection()

    # Calculate 24 hours ago
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    # Get networks with chronic problem detection (>8 outages in last 24 hours)
    networks = conn.execute("""
        SELECT
            n.network_id,
            n.street_address,
            n.subloc,
            n.customer_name,
            n.total_outages,
            n.city,
            n.region,
            n.country_name,
            n.latitude,
            n.longitude,
            n.download_target,
            n.upload_target,
            n.gateway_speed_down,
            n.gateway_speed_up,
            n.speed_test_date,
            COALESCE(recent_outages.outage_count_24h, 0) as outages_last_24h,
            CASE WHEN COALESCE(recent_outages.outage_count_24h, 0) > 8
                 THEN 1
                 ELSE 0
            END as is_chronic_problem
        FROM networks n
        LEFT JOIN (
            SELECT network_id, COUNT(*) as outage_count_24h
            FROM outages
            WHERE wan_down_start >= ?
            GROUP BY network_id
        ) recent_outages ON n.network_id = recent_outages.network_id
        WHERE n.property_id = ?
        ORDER BY is_chronic_problem DESC, total_outages DESC
    """, (twenty_four_hours_ago.isoformat(), property_id)).fetchall()

    conn.close()

    return jsonify([dict(n) for n in networks])


@app.route('/api/network/<int:network_id>')
def get_network(network_id):
    """Get detailed information about a specific network."""
    conn = get_db_connection()

    # Get network info
    network_info = conn.execute("""
        SELECT n.network_id, n.street_address, n.subloc, n.customer_name,
               n.total_outages, p.property_name, p.property_id,
               n.city, n.region, n.country_name, n.country_code,
               n.latitude, n.longitude, n.timezone, n.postal_code,
               n.download_target, n.upload_target,
               n.gateway_speed_down, n.gateway_speed_up, n.speed_test_date
        FROM networks n
        JOIN properties p ON n.property_id = p.property_id
        WHERE n.network_id = ?
    """, (network_id,)).fetchone()

    if not network_info:
        conn.close()
        return jsonify({'error': 'Network not found'}), 404

    conn.close()

    # Convert to dict and handle bytes fields
    result = dict(network_info)

    # Convert bytes to string or None
    for key, value in result.items():
        if isinstance(value, bytes):
            try:
                result[key] = value.decode('utf-8')
            except:
                result[key] = None

    return jsonify(result)


@app.route('/api/network/<int:network_id>/hourly')
def get_network_hourly(network_id):
    """Get hourly outage data for a network."""
    conn = get_db_connection()
    
    hourly = conn.execute("""
        SELECT outage_hour, outage_count
        FROM network_hourly_outages
        WHERE network_id = ?
        ORDER BY outage_hour
    """, (network_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(h) for h in hourly])


@app.route('/api/stats')
def get_stats():
    """Get overall statistics."""
    conn = get_db_connection()
    
    stats = {}
    
    # Total properties with outages
    result = conn.execute("SELECT COUNT(*) FROM properties WHERE total_outages > 0").fetchone()
    stats['properties_with_outages'] = result[0]
    
    # Total outages
    result = conn.execute("SELECT SUM(total_outages) FROM properties").fetchone()
    stats['total_outages'] = result[0] or 0
    
    # Total networks
    result = conn.execute("SELECT COUNT(*) FROM networks").fetchone()
    stats['total_networks'] = result[0]
    
    # Networks with outages
    result = conn.execute("SELECT COUNT(*) FROM networks WHERE total_outages > 0").fetchone()
    stats['networks_with_outages'] = result[0]
    
    # Outage reasons breakdown
    reasons = conn.execute("""
        SELECT reason, COUNT(*) as count
        FROM outages
        GROUP BY reason
        ORDER BY count DESC
    """).fetchall()
    stats['outage_reasons'] = {(r['reason'] or 'UNKNOWN'): r['count'] for r in reasons}
    
    # Property with most outages in the past 24 hours
    twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
    top_property = conn.execute("""
        SELECT
            p.property_id,
            p.property_name,
            COUNT(DISTINCT o.outage_id) as outages_24h
        FROM properties p
        LEFT JOIN networks n ON p.property_id = n.property_id
        LEFT JOIN outages o ON n.network_id = o.network_id
            AND o.wan_down_start >= ?
        GROUP BY p.property_id, p.property_name
        ORDER BY outages_24h DESC
        LIMIT 1
    """, (twenty_four_hours_ago,)).fetchone()
    if top_property:
        stats['top_property'] = {
            'id': top_property['property_id'],
            'name': top_property['property_name'],
            'outages': top_property['outages_24h']
        }
    
    conn.close()
    
    return jsonify(stats)


@app.route('/api/ongoing-outages')
def get_ongoing_outages():
    """Get all currently ongoing outages."""
    conn = get_db_connection()

    outages = conn.execute("""
        SELECT
            oo.ongoing_outage_id,
            oo.network_id,
            oo.wan_down_start,
            oo.reason,
            oo.first_detected,
            oo.last_checked,
            n.street_address,
            n.subloc,
            n.customer_name,
            p.property_id,
            p.property_name,
            p.island
        FROM ongoing_outages oo
        JOIN networks n ON oo.network_id = n.network_id
        JOIN properties p ON n.property_id = p.property_id
        WHERE oo.wan_down_end IS NULL
        ORDER BY oo.wan_down_start DESC
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in outages])


@app.route('/api/ongoing-outages/count')
def get_ongoing_outages_count():
    """Get count of currently ongoing outages."""
    conn = get_db_connection()

    result = conn.execute("""
        SELECT COUNT(*) as count
        FROM ongoing_outages
        WHERE wan_down_end IS NULL
    """).fetchone()

    conn.close()

    return jsonify({'count': result['count']})


@app.route('/api/ongoing-outages/by-property')
def get_ongoing_outages_by_property():
    """Get ongoing outages grouped by property."""
    conn = get_db_connection()

    properties = conn.execute("""
        SELECT
            p.property_id,
            p.property_name,
            p.island,
            COUNT(oo.ongoing_outage_id) as ongoing_count
        FROM properties p
        JOIN networks n ON p.property_id = n.property_id
        JOIN ongoing_outages oo ON n.network_id = oo.network_id
        WHERE oo.wan_down_end IS NULL
        GROUP BY p.property_id, p.property_name, p.island
        ORDER BY ongoing_count DESC
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in properties])


@app.route('/api/property/<int:property_id>/ongoing-outages')
def get_property_ongoing_outages(property_id):
    """Get ongoing outages for a specific property."""
    conn = get_db_connection()

    outages = conn.execute("""
        SELECT
            oo.ongoing_outage_id,
            oo.network_id,
            oo.wan_down_start,
            oo.reason,
            oo.first_detected,
            oo.last_checked,
            n.street_address,
            n.subloc,
            n.customer_name
        FROM ongoing_outages oo
        JOIN networks n ON oo.network_id = n.network_id
        WHERE n.property_id = ? AND oo.wan_down_end IS NULL
        ORDER BY oo.wan_down_start DESC
    """, (property_id,)).fetchall()

    conn.close()

    return jsonify([dict(row) for row in outages])


@app.route('/api/search')
def search():
    """Search for properties by name."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    conn = get_db_connection()
    
    properties = conn.execute("""
        SELECT property_id, property_name, total_networks, total_outages
        FROM properties
        WHERE property_name LIKE ?
        ORDER BY total_outages DESC
    """, (f'%{query}%',)).fetchall()
    
    conn.close()
    
    return jsonify([dict(p) for p in properties])


@app.route('/api/xpon-shelves')
def get_xpon_shelves():
    """Get all xPON shelves with statistics."""
    conn = get_db_connection()

    shelves = conn.execute("""
        SELECT
            xs.shelf_id,
            xs.shelf_name,
            xs.total_properties,
            xs.total_networks,
            GROUP_CONCAT(p.property_name, ', ') as property_names
        FROM xpon_shelves xs
        LEFT JOIN property_xpon_shelves pxs ON xs.shelf_id = pxs.shelf_id
        LEFT JOIN properties p ON pxs.property_id = p.property_id
        GROUP BY xs.shelf_id, xs.shelf_name, xs.total_properties, xs.total_networks
        ORDER BY xs.total_properties DESC, xs.shelf_name
    """).fetchall()

    conn.close()

    return jsonify([dict(s) for s in shelves])


@app.route('/api/xpon-shelf/<int:shelf_id>')
def get_xpon_shelf(shelf_id):
    """Get detailed information about a specific xPON shelf."""
    conn = get_db_connection()

    # Get shelf info
    shelf_info = conn.execute("""
        SELECT shelf_id, shelf_name, total_properties, total_networks
        FROM xpon_shelves
        WHERE shelf_id = ?
    """, (shelf_id,)).fetchone()

    if not shelf_info:
        conn.close()
        return jsonify({'error': 'xPON shelf not found'}), 404

    # Get associated properties
    properties = conn.execute("""
        SELECT p.property_id, p.property_name, p.total_outages, pxs.network_count, pxs.slots, pxs.pons
        FROM properties p
        JOIN property_xpon_shelves pxs ON p.property_id = pxs.property_id
        WHERE pxs.shelf_id = ?
        ORDER BY p.total_outages DESC
    """, (shelf_id,)).fetchall()

    conn.close()

    return jsonify({
        'shelf': dict(shelf_info),
        'properties': [dict(p) for p in properties]
    })


@app.route('/api/7x50s')
def get_7x50s():
    """Get all 7x50 routers with statistics."""
    conn = get_db_connection()

    routers = conn.execute("""
        SELECT
            r7.router_id,
            r7.router_name,
            r7.total_properties,
            r7.total_networks,
            GROUP_CONCAT(p.property_name, ', ') as property_names
        FROM router_7x50s r7
        LEFT JOIN property_7x50s p7 ON r7.router_id = p7.router_id
        LEFT JOIN properties p ON p7.property_id = p.property_id
        GROUP BY r7.router_id, r7.router_name, r7.total_properties, r7.total_networks
        ORDER BY r7.total_properties DESC, r7.router_name
    """).fetchall()

    conn.close()

    return jsonify([dict(r) for r in routers])


@app.route('/api/7x50/<int:router_id>')
def get_7x50(router_id):
    """Get detailed information about a specific 7x50 router."""
    conn = get_db_connection()

    # Get router info
    router_info = conn.execute("""
        SELECT router_id, router_name, total_properties, total_networks
        FROM router_7x50s
        WHERE router_id = ?
    """, (router_id,)).fetchone()

    if not router_info:
        conn.close()
        return jsonify({'error': '7x50 router not found'}), 404

    # Get associated properties
    properties = conn.execute("""
        SELECT p.property_id, p.property_name, p.total_outages, p7.network_count, p7.saps
        FROM properties p
        JOIN property_7x50s p7 ON p.property_id = p7.property_id
        WHERE p7.router_id = ?
        ORDER BY p.total_outages DESC
    """, (router_id,)).fetchall()

    conn.close()

    return jsonify({
        'router': dict(router_info),
        'properties': [dict(p) for p in properties]
    })


@app.route('/api/property-wide-outages')
def get_property_wide_outages():
    """
    Get properties that experienced property-wide outages in the last 24 hours.
    A property-wide outage is when MORE than 80% of networks on that property have an outage within the same hour.
    """
    conn = get_db_connection()

    # Calculate 24 hours ago
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    # Query for property-wide outages
    # A property-wide outage requires MORE than 80% of networks to have outages in the same hour
    # This means we need to count unique networks with outages per hour, not just total outage count
    property_wide_outages = conn.execute("""
        SELECT
            p.property_id,
            p.property_name,
            p.total_networks,
            nho.outage_hour,
            COUNT(DISTINCT nho.network_id) as networks_with_outages,
            ROUND(CAST(COUNT(DISTINCT nho.network_id) AS FLOAT) / p.total_networks * 100, 1) as outage_percentage
        FROM properties p
        JOIN networks n ON p.property_id = n.property_id
        JOIN network_hourly_outages nho ON n.network_id = nho.network_id
        WHERE nho.outage_hour >= ?
        GROUP BY p.property_id, p.property_name, p.total_networks, nho.outage_hour
        HAVING CAST(COUNT(DISTINCT nho.network_id) AS FLOAT) / p.total_networks > 0.8
        ORDER BY nho.outage_hour DESC, outage_percentage DESC
    """, (twenty_four_hours_ago.isoformat(),)).fetchall()

    conn.close()

    # Format results
    results = []
    seen_properties = set()

    for row in property_wide_outages:
        property_id = row['property_id']
        if property_id not in seen_properties:
            seen_properties.add(property_id)
            results.append({
                'property_id': property_id,
                'property_name': row['property_name'],
                'total_networks': row['total_networks'],
                'outage_hour': row['outage_hour'],
                'networks_with_outages': row['networks_with_outages'],
                'outage_percentage': row['outage_percentage']
            })

    return jsonify({
        'has_property_wide_outages': len(results) > 0,
        'count': len(results),
        'properties': results
    })


@app.route('/api/speedtest-performance')
def get_speedtest_performance():
    """
    Get speedtest performance data for all properties.
    Returns count of tests that meet/don't meet 85% threshold for each property.
    """
    conn = get_db_connection()

    # Get speedtest performance by property
    # Count networks where actual speed >= 85% of target speed
    performance = conn.execute("""
        SELECT
            p.property_id,
            p.property_name,
            p.total_networks,
            p.island,
            SUM(CASE
                WHEN n.download_target IS NOT NULL
                     AND n.gateway_speed_down IS NOT NULL
                     AND n.gateway_speed_down >= (n.download_target * 0.85)
                THEN 1 ELSE 0
            END) as download_tests_passing,
            SUM(CASE
                WHEN n.download_target IS NOT NULL
                     AND n.gateway_speed_down IS NOT NULL
                     AND n.gateway_speed_down < (n.download_target * 0.85)
                THEN 1 ELSE 0
            END) as download_tests_failing,
            SUM(CASE
                WHEN n.upload_target IS NOT NULL
                     AND n.gateway_speed_up IS NOT NULL
                     AND n.gateway_speed_up >= (n.upload_target * 0.85)
                THEN 1 ELSE 0
            END) as upload_tests_passing,
            SUM(CASE
                WHEN n.upload_target IS NOT NULL
                     AND n.gateway_speed_up IS NOT NULL
                     AND n.gateway_speed_up < (n.upload_target * 0.85)
                THEN 1 ELSE 0
            END) as upload_tests_failing,
            SUM(CASE
                WHEN n.download_target IS NOT NULL
                     AND n.gateway_speed_down IS NOT NULL
                THEN 1 ELSE 0
            END) as download_tests_total,
            SUM(CASE
                WHEN n.upload_target IS NOT NULL
                     AND n.gateway_speed_up IS NOT NULL
                THEN 1 ELSE 0
            END) as upload_tests_total
        FROM properties p
        LEFT JOIN networks n ON p.property_id = n.property_id
        GROUP BY p.property_id, p.property_name, p.total_networks, p.island
        HAVING download_tests_total > 0 OR upload_tests_total > 0
        ORDER BY p.property_name
    """).fetchall()

    conn.close()

    results = []
    for row in performance:
        results.append({
            'property_id': row['property_id'],
            'property_name': row['property_name'],
            'total_networks': row['total_networks'],
            'island': row['island'],
            'download': {
                'tests_passing': row['download_tests_passing'],
                'tests_failing': row['download_tests_failing'],
                'tests_total': row['download_tests_total'],
                'pass_percentage': round((row['download_tests_passing'] / row['download_tests_total'] * 100) if row['download_tests_total'] > 0 else 0, 1)
            },
            'upload': {
                'tests_passing': row['upload_tests_passing'],
                'tests_failing': row['upload_tests_failing'],
                'tests_total': row['upload_tests_total'],
                'pass_percentage': round((row['upload_tests_passing'] / row['upload_tests_total'] * 100) if row['upload_tests_total'] > 0 else 0, 1)
            }
        })

    return jsonify(results)


@app.route('/api/speedtest-performance-table')
def get_speedtest_performance_table():
    """
    Get speedtest performance data with equipment details for table view.
    Includes xPON OLT and 7x50 router information.
    """
    conn = get_db_connection()

    # Get speedtest performance with equipment info
    performance = conn.execute("""
        SELECT
            p.property_id,
            p.property_name,
            p.total_networks,
            p.island,
            SUM(CASE
                WHEN n.download_target IS NOT NULL
                     AND n.gateway_speed_down IS NOT NULL
                     AND n.gateway_speed_down >= (n.download_target * 0.85)
                THEN 1 ELSE 0
            END) as download_tests_passing,
            SUM(CASE
                WHEN n.download_target IS NOT NULL
                     AND n.gateway_speed_down IS NOT NULL
                     AND n.gateway_speed_down < (n.download_target * 0.85)
                THEN 1 ELSE 0
            END) as download_tests_failing,
            SUM(CASE
                WHEN n.upload_target IS NOT NULL
                     AND n.gateway_speed_up IS NOT NULL
                     AND n.gateway_speed_up >= (n.upload_target * 0.85)
                THEN 1 ELSE 0
            END) as upload_tests_passing,
            SUM(CASE
                WHEN n.upload_target IS NOT NULL
                     AND n.gateway_speed_up IS NOT NULL
                     AND n.gateway_speed_up < (n.upload_target * 0.85)
                THEN 1 ELSE 0
            END) as upload_tests_failing,
            SUM(CASE
                WHEN n.download_target IS NOT NULL
                     AND n.gateway_speed_down IS NOT NULL
                THEN 1 ELSE 0
            END) as download_tests_total,
            SUM(CASE
                WHEN n.upload_target IS NOT NULL
                     AND n.gateway_speed_up IS NOT NULL
                THEN 1 ELSE 0
            END) as upload_tests_total
        FROM properties p
        LEFT JOIN networks n ON p.property_id = n.property_id
        GROUP BY p.property_id, p.property_name, p.total_networks, p.island
        HAVING download_tests_total > 0 OR upload_tests_total > 0
        ORDER BY p.property_name
    """).fetchall()

    # Get equipment info for each property
    equipment_query = """
        SELECT
            p.property_id,
            GROUP_CONCAT(DISTINCT x.shelf_name) as xpon_shelves,
            GROUP_CONCAT(DISTINCT r.router_name) as routers_7x50
        FROM properties p
        LEFT JOIN property_xpon_shelves px ON p.property_id = px.property_id
        LEFT JOIN xpon_shelves x ON px.shelf_id = x.shelf_id
        LEFT JOIN property_7x50s p7 ON p.property_id = p7.property_id
        LEFT JOIN router_7x50s r ON p7.router_id = r.router_id
        GROUP BY p.property_id
    """
    equipment_data = {}
    for row in conn.execute(equipment_query).fetchall():
        equipment_data[row['property_id']] = {
            'xpon_shelves': row['xpon_shelves'] if row['xpon_shelves'] else 'N/A',
            'routers_7x50': row['routers_7x50'] if row['routers_7x50'] else 'N/A'
        }

    conn.close()

    results = []
    for row in performance:
        prop_id = row['property_id']
        equipment = equipment_data.get(prop_id, {'xpon_shelves': 'N/A', 'routers_7x50': 'N/A'})

        results.append({
            'property_id': prop_id,
            'property_name': row['property_name'],
            'total_networks': row['total_networks'],
            'island': row['island'],
            'xpon_shelves': equipment['xpon_shelves'],
            'routers_7x50': equipment['routers_7x50'],
            'download': {
                'tests_passing': row['download_tests_passing'],
                'tests_failing': row['download_tests_failing'],
                'tests_total': row['download_tests_total'],
                'pass_percentage': round((row['download_tests_passing'] / row['download_tests_total'] * 100) if row['download_tests_total'] > 0 else 0, 1)
            },
            'upload': {
                'tests_passing': row['upload_tests_passing'],
                'tests_failing': row['upload_tests_failing'],
                'tests_total': row['upload_tests_total'],
                'pass_percentage': round((row['upload_tests_passing'] / row['upload_tests_total'] * 100) if row['upload_tests_total'] > 0 else 0, 1)
            }
        })

    return jsonify(results)


@app.route('/api/dashboard/outage-analysis')
def analyze_dashboard_outages():
    """
    Generate AI analysis of ALL property-wide outages using Claude.
    Analyzes patterns across multiple properties to identify common causes.
    Returns top 2 theories in concise format.
    """
    try:
        # Check for API key
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'ANTHROPIC_API_KEY not configured',
                'analysis': 'AI analysis unavailable: API key not configured in environment variables.'
            }), 500

        conn = get_db_connection()

        # Get all properties with property-wide outages in last 24 hours
        property_wide_outages = conn.execute("""
            SELECT
                p.property_id,
                p.property_name,
                p.island,
                p.total_networks,
                nho.outage_hour,
                COUNT(DISTINCT nho.network_id) as networks_with_outages,
                CAST(COUNT(DISTINCT nho.network_id) AS FLOAT) / p.total_networks * 100 as percentage_affected
            FROM properties p
            JOIN network_hourly_outages nho ON p.property_id = (
                SELECT n.property_id
                FROM networks n
                WHERE n.network_id = nho.network_id
            )
            WHERE nho.outage_hour >= datetime('now', '-24 hours')
            GROUP BY p.property_id, p.property_name, p.island, p.total_networks, nho.outage_hour
            HAVING percentage_affected > 80
            ORDER BY nho.outage_hour DESC, percentage_affected DESC
        """).fetchall()

        # Create a hash of the outage data to use as cache key
        # This ensures we only regenerate analysis when the actual data changes
        outage_data_for_hash = []
        for outage in property_wide_outages:
            outage_data_for_hash.append({
                'property_id': outage['property_id'],
                'property_name': outage['property_name'],
                'outage_hour': outage['outage_hour'],
                'networks_with_outages': outage['networks_with_outages'],
                'percentage_affected': round(outage['percentage_affected'], 1)
            })

        data_hash = hashlib.md5(
            json.dumps(outage_data_for_hash, sort_keys=True).encode()
        ).hexdigest()

        # Check if we have a cached analysis for this exact data
        if 'dashboard' in analysis_cache and analysis_cache['dashboard']['data_hash'] == data_hash:
            print(f"[CACHE HIT] Returning cached analysis (hash: {data_hash[:8]}...)")
            return jsonify(analysis_cache['dashboard']['response'])

        if not property_wide_outages:
            conn.close()
            return jsonify({
                'analysis': 'No property-wide outages detected in the last 24 hours.',
                'model': None,
                'timestamp': datetime.now().isoformat()
            })

        # Group properties by outage hour and island for pattern detection
        properties_by_pattern = {}
        all_property_ids = set()
        islands_affected = set()

        for outage in property_wide_outages:
            all_property_ids.add(outage['property_id'])
            if outage['island']:
                islands_affected.add(outage['island'])

            if outage['property_name'] not in properties_by_pattern:
                properties_by_pattern[outage['property_name']] = {
                    'property_id': outage['property_id'],
                    'island': outage['island'],
                    'total_networks': outage['total_networks'],
                    'outage_hours': [],
                    'max_percentage': 0
                }

            properties_by_pattern[outage['property_name']]['outage_hours'].append({
                'hour': outage['outage_hour'],
                'networks_affected': outage['networks_with_outages'],
                'percentage': round(outage['percentage_affected'], 1)
            })

            if outage['percentage_affected'] > properties_by_pattern[outage['property_name']]['max_percentage']:
                properties_by_pattern[outage['property_name']]['max_percentage'] = outage['percentage_affected']

        # Get equipment for all affected properties
        all_xpon = set()
        all_routers = set()

        for prop_id in all_property_ids:
            xpon = conn.execute("""
                SELECT DISTINCT xs.shelf_name
                FROM xpon_shelves xs
                JOIN property_xpon_shelves pxs ON xs.shelf_id = pxs.shelf_id
                WHERE pxs.property_id = ?
            """, (prop_id,)).fetchall()

            routers = conn.execute("""
                SELECT DISTINCT r.router_name
                FROM router_7x50s r
                JOIN property_7x50s p7 ON r.router_id = p7.router_id
                WHERE p7.property_id = ?
            """, (prop_id,)).fetchall()

            all_xpon.update([x['shelf_name'] for x in xpon])
            all_routers.update([r['router_name'] for r in routers])

        conn.close()

        # Find common equipment across multiple properties
        equipment_counts = {}
        for prop_id in all_property_ids:
            conn = get_db_connection()
            xpon = conn.execute("""
                SELECT xs.shelf_name
                FROM xpon_shelves xs
                JOIN property_xpon_shelves pxs ON xs.shelf_id = pxs.shelf_id
                WHERE pxs.property_id = ?
            """, (prop_id,)).fetchall()

            routers = conn.execute("""
                SELECT r.router_name
                FROM router_7x50s r
                JOIN property_7x50s p7 ON r.router_id = p7.router_id
                WHERE p7.property_id = ?
            """, (prop_id,)).fetchall()
            conn.close()

            for x in xpon:
                equipment_counts[x['shelf_name']] = equipment_counts.get(x['shelf_name'], 0) + 1
            for r in routers:
                equipment_counts[r['router_name']] = equipment_counts.get(r['router_name'], 0) + 1

        # Find equipment shared by multiple properties (potential common point of failure)
        common_equipment = {name: count for name, count in equipment_counts.items() if count > 1}

        # Create concise prompt for Claude - requesting only top 2 theories
        prompt = f"""Analyze property-wide network outages and provide ONLY your TOP 2 root cause theories in a concise, readable format.

**Affected Properties:** {len(properties_by_pattern)} properties
**Islands Affected:** {', '.join(islands_affected) if islands_affected else 'Unknown'}
**Total Properties with >80% Networks Down**

**Properties and Timing:**
"""

        for prop_name, prop_data in list(properties_by_pattern.items())[:10]:
            prompt += f"\n{prop_name} ({prop_data['island'] or 'Unknown island'})\n"
            prompt += f"  - Networks: {prop_data['total_networks']}\n"
            for hour_data in prop_data['outage_hours'][:3]:  # Show first 3 outage hours
                prompt += f"  - {hour_data['hour']}: {hour_data['networks_affected']} networks ({hour_data['percentage']}% affected)\n"

        if len(properties_by_pattern) > 10:
            prompt += f"\n... and {len(properties_by_pattern) - 10} more properties\n"

        if common_equipment:
            prompt += f"\n**Shared Equipment (Potential Common Points of Failure):**\n"
            for equip_name, count in sorted(common_equipment.items(), key=lambda x: x[1], reverse=True)[:5]:
                prompt += f"  - {equip_name}: Serves {count} affected properties\n"
        else:
            prompt += f"\n**Equipment:** No shared equipment detected between properties\n"

        prompt += f"""
**Geographic Pattern:** {"Single island (" + list(islands_affected)[0] + ")" if len(islands_affected) == 1 else str(len(islands_affected)) + " islands affected"}

---

Provide your analysis in this EXACT format:

**THEORY 1: [Brief title]**
[2-3 sentence explanation with supporting evidence from the data]

**THEORY 2: [Brief title]**
[2-3 sentence explanation with supporting evidence from the data]

Keep it concise and data-driven. Focus on what the patterns reveal."""

        # Call Claude API
        client = anthropic.Anthropic(api_key=api_key)
        model_name = "claude-sonnet-4-20250514"

        message = client.messages.create(
            model=model_name,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        analysis_text = message.content[0].text

        # Prepare response
        response_data = {
            'analysis': analysis_text,
            'model': model_name,
            'timestamp': datetime.now().isoformat(),
            'properties_analyzed': len(properties_by_pattern),
            'islands_affected': list(islands_affected)
        }

        # Cache the result with the data hash
        analysis_cache['dashboard'] = {
            'data_hash': data_hash,
            'response': response_data,
            'cached_at': datetime.now().isoformat()
        }
        print(f"[CACHE MISS] Generated new analysis and cached (hash: {data_hash[:8]}...)")

        return jsonify(response_data)

    except Exception as e:
        print(f"Error generating outage analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'analysis': f'Error generating analysis: {str(e)}'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DATABASE):
        print(f"Error: Database file not found: {DATABASE}")
        print("Please run process_property_outages_db.py first to create the database.")
        exit(1)
    
    print(f"Starting API server...")
    print(f"Database: {DATABASE}")
    print(f"API will be available at: http://localhost:5000")
    print(f"API documentation at: http://localhost:5000/")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
