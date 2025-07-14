#!/usr/bin/env python3
"""
Migration script to add missing status column to conversations table
"""

import sqlite3
import logging
from pathlib import Path
from app.config.settings import settings

def migrate_conversations_table():
    """Add status column to conversations table if it doesn't exist"""
    db_path = settings.conversation_db
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if not db_path.exists():
        logger.info(f"Database {db_path} doesn't exist, skipping migration")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if status column exists
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            logger.info("Adding status column to conversations table...")
            cursor.execute("ALTER TABLE conversations ADD COLUMN status TEXT DEFAULT 'active'")
            conn.commit()
            logger.info("✅ Status column added successfully")
        else:
            logger.info("Status column already exists")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_conversations_table()
