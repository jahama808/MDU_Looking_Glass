#!/usr/bin/env python3
"""
Create an admin user for the MDU Performance Dashboard

Usage:
    python create_admin_user.py [--database path/to/database.db]
"""

import sqlite3
import argparse
import sys
import getpass
import bcrypt


def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_admin_user(db_path):
    """Create an admin user interactively."""
    print("=" * 60)
    print("Create Admin User for MDU Performance Dashboard")
    print("=" * 60)
    print()

    # Get user input
    username = input("Enter admin username: ").strip()
    if not username:
        print("✗ Username cannot be empty")
        return False

    email = input("Enter admin email: ").strip()
    if not email:
        print("✗ Email cannot be empty")
        return False

    while True:
        password = getpass.getpass("Enter password (min 8 characters): ")
        if len(password) < 8:
            print("✗ Password must be at least 8 characters. Try again.")
            continue

        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("✗ Passwords don't match. Try again.")
            continue

        break

    print()
    print(f"Creating admin user '{username}'...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if username or email already exists
        existing = cursor.execute("""
            SELECT username, email FROM users
            WHERE username = ? OR email = ?
        """, (username, email)).fetchone()

        if existing:
            conn.close()
            if existing[0] == username:
                print(f"✗ Username '{username}' already exists")
            else:
                print(f"✗ Email '{email}' already exists")
            return False

        # Hash password and create user
        password_hash = hash_password(password)

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (?, ?, ?, 'admin', 1)
        """, (username, email, password_hash))

        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        print(f"✓ Admin user created successfully!")
        print()
        print(f"User ID: {user_id}")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Role: admin")
        print()
        print("You can now login with these credentials.")

        return True

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Create an admin user for the MDU Performance Dashboard'
    )
    parser.add_argument(
        '--database',
        default='property_outages.db',
        help='Path to SQLite database (default: property_outages.db)'
    )

    args = parser.parse_args()

    # Check if database exists
    import os
    if not os.path.exists(args.database):
        print(f"✗ Database not found: {args.database}")
        print()
        print("Please run the migration script first:")
        print(f"  python migrate_add_auth_tables.py --database {args.database}")
        sys.exit(1)

    # Check if users table exists
    try:
        conn = sqlite3.connect(args.database)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            conn.close()
            print("✗ Users table not found in database")
            print()
            print("Please run the migration script first:")
            print(f"  python migrate_add_auth_tables.py --database {args.database}")
            sys.exit(1)
        conn.close()
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)

    success = create_admin_user(args.database)

    if success:
        print()
        print("Next steps:")
        print("1. Start the API server: python api_server.py")
        print("2. Test login at: POST http://localhost:5000/api/auth/login")
        print("3. Use the frontend login page once it's implemented")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
