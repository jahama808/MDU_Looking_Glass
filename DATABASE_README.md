# Database Backend Documentation

## Overview

The `process_property_outages_db.py` script processes outage data and stores it in a SQLite database, providing a structured backend for your web application.

## Database Schema

### Tables

#### 1. `properties`
Stores property-level summary information.

| Column | Type | Description |
|--------|------|-------------|
| property_id | INTEGER | Primary key (auto-increment) |
| property_name | TEXT | Unique property name |
| total_networks | INTEGER | Number of networks in property |
| total_outages | INTEGER | Total outages for property |
| last_updated | TIMESTAMP | When data was last processed |

#### 2. `networks`
Stores network details for each property.

| Column | Type | Description |
|--------|------|-------------|
| network_id | INTEGER | Primary key (Eero Network ID) |
| property_id | INTEGER | Foreign key to properties table |
| street_address | TEXT | Street address |
| subloc | TEXT | Sub-location (apt/unit number) |
| customer_name | TEXT | Customer identifier |
| total_outages | INTEGER | Total outages for this network |

#### 3. `property_hourly_outages`
Aggregated hourly outage counts per property.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| property_id | INTEGER | Foreign key to properties table |
| outage_hour | TIMESTAMP | Hour when outages occurred |
| total_outage_count | INTEGER | Sum of outages across all networks in that hour |

#### 4. `network_hourly_outages`
Hourly outage counts per individual network.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| network_id | INTEGER | Foreign key to networks table |
| outage_hour | TIMESTAMP | Hour when outages occurred |
| outage_count | INTEGER | Number of outages for this network in that hour |

#### 5. `outages`
Raw outage records (for detailed analysis).

| Column | Type | Description |
|--------|------|-------------|
| outage_id | INTEGER | Primary key (auto-increment) |
| network_id | INTEGER | Foreign key to networks table |
| wan_down_start | TIMESTAMP | When outage started |
| wan_down_end | TIMESTAMP | When outage ended |
| duration | REAL | Duration in seconds |
| reason | TEXT | Reason code (DNS_UNREACHABLE, UNKNOWN, etc.) |

## Sample Queries

### Python Examples

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('output/outages.db')
cursor = conn.cursor()

# Query 1: Get all properties with outages
cursor.execute("""
    SELECT property_name, total_networks, total_outages 
    FROM properties 
    WHERE total_outages > 0
    ORDER BY total_outages DESC
""")
properties = cursor.fetchall()
for prop in properties:
    print(f"{prop[0]}: {prop[2]} outages across {prop[1]} networks")

# Query 2: Get hourly outage trend for a specific property
cursor.execute("""
    SELECT pho.outage_hour, pho.total_outage_count
    FROM property_hourly_outages pho
    JOIN properties p ON pho.property_id = p.property_id
    WHERE p.property_name = 'WAIKIKI BEACH TOWER'
    ORDER BY pho.outage_hour
""")
hourly_data = cursor.fetchall()
for hour, count in hourly_data:
    print(f"{hour}: {count} outages")

# Query 3: Get networks with most outages in a property
cursor.execute("""
    SELECT n.network_id, n.street_address, n.subloc, n.total_outages
    FROM networks n
    JOIN properties p ON n.property_id = p.property_id
    WHERE p.property_name = 'ASTON KAANAPALI SHORES'
    AND n.total_outages > 0
    ORDER BY n.total_outages DESC
""")
networks = cursor.fetchall()

# Query 4: Get outage reasons for a property
cursor.execute("""
    SELECT o.reason, COUNT(*) as count
    FROM outages o
    JOIN networks n ON o.network_id = n.network_id
    JOIN properties p ON n.property_id = p.property_id
    WHERE p.property_name = 'WAIKIKI BEACH TOWER'
    GROUP BY o.reason
    ORDER BY count DESC
""")
reasons = cursor.fetchall()

conn.close()
```

### SQL Examples

```sql
-- Get properties with most outages
SELECT property_name, total_outages 
FROM properties 
WHERE total_outages > 0
ORDER BY total_outages DESC 
LIMIT 10;

-- Get hourly outage pattern for a property
SELECT outage_hour, total_outage_count
FROM property_hourly_outages pho
JOIN properties p ON pho.property_id = p.property_id
WHERE p.property_name = 'WAIKIKI BEACH TOWER'
ORDER BY outage_hour;

-- Get network details for a property
SELECT network_id, street_address, subloc, total_outages
FROM networks
WHERE property_id = (
    SELECT property_id FROM properties WHERE property_name = 'WAIKIKI BEACH TOWER'
)
ORDER BY total_outages DESC;

-- Get outage reasons breakdown
SELECT reason, COUNT(*) as count
FROM outages
GROUP BY reason
ORDER BY count DESC;

-- Get average outages per property
SELECT AVG(total_outages) as avg_outages
FROM properties
WHERE total_outages > 0;

-- Find properties with outages in specific time range
SELECT DISTINCT p.property_name, COUNT(o.outage_id) as count
FROM properties p
JOIN networks n ON p.property_id = n.property_id
JOIN outages o ON n.network_id = o.network_id
WHERE o.wan_down_start BETWEEN '2025-11-06 00:00:00' AND '2025-11-06 23:59:59'
GROUP BY p.property_name
ORDER BY count DESC;
```

## Web Application Integration

### Flask Example

```python
from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'output/outages.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/properties')
def get_properties():
    """Get all properties with outages"""
    conn = get_db_connection()
    properties = conn.execute("""
        SELECT property_id, property_name, total_networks, total_outages 
        FROM properties 
        WHERE total_outages > 0
        ORDER BY total_outages DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(p) for p in properties])

@app.route('/api/property/<int:property_id>/hourly')
def get_property_hourly(property_id):
    """Get hourly outage data for a property"""
    conn = get_db_connection()
    hourly = conn.execute("""
        SELECT outage_hour, total_outage_count
        FROM property_hourly_outages
        WHERE property_id = ?
        ORDER BY outage_hour
    """, (property_id,)).fetchall()
    conn.close()
    return jsonify([dict(h) for h in hourly])

@app.route('/api/property/<int:property_id>/networks')
def get_property_networks(property_id):
    """Get networks for a property"""
    conn = get_db_connection()
    networks = conn.execute("""
        SELECT network_id, street_address, subloc, total_outages
        FROM networks
        WHERE property_id = ?
        ORDER BY total_outages DESC
    """, (property_id,)).fetchall()
    conn.close()
    return jsonify([dict(n) for n in networks])

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Example

```python
from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from typing import List

app = FastAPI()
DATABASE = 'output/outages.db'

class Property(BaseModel):
    property_id: int
    property_name: str
    total_networks: int
    total_outages: int

class HourlyOutage(BaseModel):
    outage_hour: str
    total_outage_count: int

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/properties", response_model=List[Property])
def read_properties():
    """Get all properties with outages"""
    conn = get_db_connection()
    properties = conn.execute("""
        SELECT property_id, property_name, total_networks, total_outages 
        FROM properties 
        WHERE total_outages > 0
        ORDER BY total_outages DESC
    """).fetchall()
    conn.close()
    return [dict(p) for p in properties]

@app.get("/api/property/{property_id}/hourly", response_model=List[HourlyOutage])
def read_property_hourly(property_id: int):
    """Get hourly outage data for a property"""
    conn = get_db_connection()
    hourly = conn.execute("""
        SELECT outage_hour, total_outage_count
        FROM property_hourly_outages
        WHERE property_id = ?
        ORDER BY outage_hour
    """, (property_id,)).fetchall()
    conn.close()
    return [dict(h) for h in hourly]
```

## Usage

### 1. Setup Virtual Environment (Required)

```bash
# Install and create venv
./install.sh  # Linux/Mac
# OR
install.bat  # Windows

# Activate venv (REQUIRED for all commands below)
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows
```

### 2. Process Data into Database

```bash
# Make sure venv is activated!
python process_property_outages_db.py \
  --outages-file wan_connectivity.csv \
  --discovery-file eero_discovery.csv \
  --database output/outages.db
```

### 3. Query Database

```bash
# Using Python (venv must be activated)
python3 << EOF
import sqlite3
conn = sqlite3.connect('output/outages.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM properties WHERE total_outages > 0")
print(f"Properties with outages: {cursor.fetchone()[0]}")
conn.close()
EOF

# Using sqlite3 command-line tool (doesn't require venv)
sqlite3 output/outages.db "SELECT property_name, total_outages FROM properties ORDER BY total_outages DESC LIMIT 5"
```

### 4. Build Web Application

```bash
# Make sure venv is activated!
python api_server.py
```

Use the Flask or FastAPI examples above as a starting point for your web backend.

## Performance Notes

- All tables have appropriate indexes for common queries
- SQLite is serverless and embedded - perfect for small to medium datasets
- For very large datasets (millions of outages), consider PostgreSQL or MySQL
- Database file is portable - can be copied between systems

## Data Updates

To update the database with new data:

1. Run the processing script again with new CSV files
2. The script will clear and repopulate all tables
3. Existing data will be replaced (not appended)

For incremental updates, you'll need to modify the script to append instead of replace.
