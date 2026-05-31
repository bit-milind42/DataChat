#!/usr/bin/env python
"""Reset database with correct schema"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from databases.models import Base, engine

def reset_database():
    """Drop and recreate all tables"""
    try:
        # Remove old database file
        db_path = Path("datachat.db")
        if db_path.exists():
            db_path.unlink()
            print("✓ Deleted old database")
        
        # Create all tables with new schema
        Base.metadata.create_all(bind=engine)
        print("✓ Created all tables with correct schema")
        print("\n✅ Database reset complete!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    reset_database()
