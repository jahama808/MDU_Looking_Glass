#!/usr/bin/env python3
"""
Migration script to add authentication tables to the property outages database.

This adds:
- users table: Store user credentials and roles
- sessions table: Track active user sessions

Usage:
    python migrate_add_auth_tables.py [--database path/to/database.db]
"""

import sqlite3
import argparse
import sys
from datetime import datetime


def add_auth_tables(db_path):
    """Add authentication tables to the database."""
    print(f"Connecting to database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if tables already exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('users', 'sessions')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]

        if 'users' in existing_tables and 'sessions' in existing_tables:
            print("⚠️  Authentication tables already exist!")
            response = input("Do you want to recreate them? This will DELETE all user data! (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False

            print("Dropping existing tables...")
            cursor.execute("DROP TABLE IF EXISTS sessions")
            cursor.execute("DROP TABLE IF EXISTS users")

        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)

        print("Creating sessions table...")
        cursor.execute("""
            CREATE TABLE sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # Create indexes for better performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX idx_sessions_token ON sessions(session_token)")
        cursor.execute("CREATE INDEX idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX idx_sessions_expires ON sessions(expires_at)")
        cursor.execute("CREATE INDEX idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")

        conn.commit()
        print("✓ Authentication tables created successfully!")

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
        description='Add authentication tables to property outages database'
    )
    parser.add_argument(
        '--database',
        default='property_outages.db',
        help='Path to SQLite database (default: property_outages.db)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Authentication Tables Migration")
    print("=" * 60)
    print()

    success = add_auth_tables(args.database)

    print()
    if success:
        print("Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Install bcrypt: pip install bcrypt")
        print("2. Update api_server.py with authentication endpoints")
        print("3. Create an initial admin user")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
