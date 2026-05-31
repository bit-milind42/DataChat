#!/usr/bin/env python
"""Fix database schema by adding missing profile column"""
import sqlite3
import os
from pathlib import Path

db_path = Path("datachat.db")

if not db_path.exists():
    print("❌ Database file not found")
    exit(1)

try:
    conn = sqlite3.connect("datachat.db")
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(datasets)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns in datasets table: {columns}")
    
    # Check if profile column exists
    if 'profile' not in columns:
        print("Adding missing 'profile' column...")
        cursor.execute("ALTER TABLE datasets ADD COLUMN profile JSON")
        conn.commit()
        print("✓ Added profile column")
    else:
        print("✓ profile column already exists")
    
    # Verify
    cursor.execute("PRAGMA table_info(datasets)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Updated columns: {columns}")
    
    conn.close()
    print("\n✅ Schema fixed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
