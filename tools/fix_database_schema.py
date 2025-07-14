#!/usr/bin/env python3
"""
Database Schema Fix Script for ChoyAI
Fixes all known database schema issues
"""

import sqlite3
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    return logging.getLogger(__name__)

def fix_conversations_table(db_path: Path, logger):
    """Fix conversations table schema"""
    logger.info(f"Fixing conversations table in {db_path}")
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Check if status column exists
            cursor.execute("PRAGMA table_info(conversations)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'status' not in columns:
                logger.info("Adding missing 'status' column to conversations table")
                cursor.execute("ALTER TABLE conversations ADD COLUMN status TEXT DEFAULT 'active'")
                conn.commit()
                logger.info("✅ Added status column to conversations table")
            else:
                logger.info("Status column already exists in conversations table")
                
    except Exception as e:
        logger.error(f"❌ Error fixing conversations table: {e}")

def fix_messages_table(db_path: Path, logger):
    """Fix messages table schema"""
    logger.info(f"Fixing messages table in {db_path}")
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Check current table structure
            cursor.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Check if we have role column
            has_role = 'role' in columns
            has_message_type = 'message_type' in columns
            
            if not has_role and has_message_type:
                logger.info("Renaming 'message_type' column to 'role' in messages table")
                # Create new table with correct schema
                cursor.execute("""
                    CREATE TABLE messages_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id INTEGER NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        provider TEXT,
                        model TEXT,
                        persona TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """)
                
                # Copy data from old table, mapping message_type to role
                cursor.execute("""
                    INSERT INTO messages_new (id, conversation_id, user_id, role, content, provider, model, persona, timestamp, metadata)
                    SELECT id, conversation_id, user_id, 
                           CASE WHEN message_type = 'ai' THEN 'assistant' ELSE message_type END as role,
                           content, provider, model, persona, timestamp, metadata
                    FROM messages
                """)
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE messages")
                cursor.execute("ALTER TABLE messages_new RENAME TO messages")
                
                # Recreate indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
                
                conn.commit()
                logger.info("✅ Fixed messages table schema - renamed message_type to role")
                
            elif not has_role and not has_message_type:
                logger.info("Adding missing 'role' column to messages table")
                cursor.execute("ALTER TABLE messages ADD COLUMN role TEXT DEFAULT 'user'")
                conn.commit()
                logger.info("✅ Added role column to messages table")
            elif has_role:
                logger.info("Role column already exists in messages table")
            else:
                logger.info("Messages table schema looks correct")
                
    except Exception as e:
        logger.error(f"❌ Error fixing messages table: {e}")

def fix_conversations_unique_constraint(db_path: Path, logger):
    """Fix UNIQUE constraint issues in conversations table"""
    logger.info(f"Fixing UNIQUE constraint in conversations table")
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Check for duplicate conversations
            cursor.execute("""
                SELECT user_id, session_id, COUNT(*) as count 
                FROM conversations 
                GROUP BY user_id, session_id 
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                logger.info(f"Found {len(duplicates)} duplicate conversation entries")
                
                for user_id, session_id, count in duplicates:
                    # Keep the latest conversation, delete older ones
                    cursor.execute("""
                        DELETE FROM conversations 
                        WHERE user_id = ? AND session_id = ? 
                        AND id NOT IN (
                            SELECT id FROM conversations 
                            WHERE user_id = ? AND session_id = ? 
                            ORDER BY created_at DESC 
                            LIMIT 1
                        )
                    """, (user_id, session_id, user_id, session_id))
                
                conn.commit()
                logger.info("✅ Removed duplicate conversations")
            else:
                logger.info("No duplicate conversations found")
                
    except Exception as e:
        logger.error(f"❌ Error fixing UNIQUE constraint: {e}")

def main():
    """Main migration function"""
    logger = setup_logging()
    logger.info("🔧 Starting database schema fix...")
    
    # Define database paths
    databases = [
        Path("data/databases/conversations.db"),
        Path("data/databases/conversation_memory.db"),
        Path("conversations.db"),  # Legacy location
        Path("conversation_memory.db"),  # Legacy location
    ]
    
    for db_path in databases:
        if db_path.exists():
            logger.info(f"📁 Processing database: {db_path}")
            
            # Fix conversations table
            fix_conversations_table(db_path, logger)
            
            # Fix messages table
            fix_messages_table(db_path, logger)
            
            # Fix UNIQUE constraint issues
            fix_conversations_unique_constraint(db_path, logger)
            
        else:
            logger.info(f"📁 Database not found: {db_path}")
    
    logger.info("✅ Database schema fix complete!")

if __name__ == "__main__":
    main()
