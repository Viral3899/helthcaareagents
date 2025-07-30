#!/usr/bin/env python3
"""
Reset database with updated schema
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import db_manager

def reset_database():
    """Drop and recreate all database tables"""
    try:
        print("Initializing database manager...")
        db_manager.initialize()
        print("Database manager initialized")
        
        print("Dropping all tables...")
        db_manager.drop_tables()
        print("Tables dropped successfully")
        
        print("Creating tables with updated schema...")
        db_manager.create_tables()
        print("Tables created successfully!")
        
        print("Database reset completed successfully!")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_database() 