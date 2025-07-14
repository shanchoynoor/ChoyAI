"""
Database Schema Initialization for ChoyAI Brain

This script creates the necessary database tables for the memory system.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_core_memory_db(db_path: Path):
    """Create core memory database and tables"""
    logger.info(f"Creating core memory database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Core memory facts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS core_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            fact TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, fact)
        )
    ''')
    
    # System capabilities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_capabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capability TEXT NOT NULL UNIQUE,
            description TEXT,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default core facts
    default_facts = [
        ('system', 'I am Choy AI, an advanced personal assistant'),
        ('system', 'I have long-term memory capabilities'),
        ('system', 'I can switch between different personas'),
        ('system', 'I support multiple AI providers (DeepSeek, OpenAI, Claude, etc.)'),
        ('capabilities', 'Natural conversation with context awareness'),
        ('capabilities', 'Memory management and recall'),
        ('capabilities', 'Persona-based responses'),
        ('capabilities', 'Multi-provider AI routing')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO core_facts (category, fact) VALUES (?, ?)
    ''', default_facts)
    
    # Insert default capabilities
    default_capabilities = [
        ('chat', 'Natural language conversation'),
        ('memory', 'Long-term memory storage and retrieval'),
        ('personas', 'Multiple AI personality support'),
        ('providers', 'Multi-AI provider management'),
        ('telegram', 'Telegram bot integration')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO system_capabilities (capability, description) VALUES (?, ?)
    ''', default_capabilities)
    
    conn.commit()
    conn.close()
    logger.info("Core memory database created successfully")

def create_user_memory_db(db_path: Path):
    """Create user memory database and tables"""
    logger.info(f"Creating user memory database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # User profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            bio TEXT,
            location TEXT,
            age INTEGER,
            profession TEXT,
            preferred_persona TEXT DEFAULT 'choy',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User memories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT NOT NULL,
            memory_type TEXT DEFAULT 'manual',
            importance REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
            UNIQUE(user_id, memory_key)
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            preference_key TEXT NOT NULL,
            preference_value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
            UNIQUE(user_id, preference_key)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("User memory database created successfully")

def create_conversation_db(db_path: Path):
    """Create conversation database and tables"""
    logger.info(f"Creating conversation database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            platform TEXT NOT NULL DEFAULT 'telegram',
            persona TEXT NOT NULL DEFAULT 'choy',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            UNIQUE(user_id, session_id)
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
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
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)')
    
    conn.commit()
    conn.close()
    logger.info("Conversation database created successfully")

def initialize_databases():
    """Initialize all ChoyAI databases"""
    logger.info("🗄️  Initializing ChoyAI databases...")
    
    # Create data directories
    data_dir = Path(__file__).parent.parent / "data"
    db_dir = data_dir / "databases"
    logs_dir = data_dir / "logs"
    
    # Ensure directories exist
    db_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Database paths
    core_memory_db = db_dir / "core_memory.db"
    user_memory_db = db_dir / "user_memories.db"
    conversation_db = db_dir / "conversations.db"
    
    try:
        # Create all databases
        create_core_memory_db(core_memory_db)
        create_user_memory_db(user_memory_db)
        create_conversation_db(conversation_db)
        
        logger.info("✅ All databases initialized successfully!")
        print("\n🎯 Database initialization complete!")
        print(f"📁 Databases created in: {db_dir}")
        print(f"📊 Core Memory: {core_memory_db}")
        print(f"👤 User Memory: {user_memory_db}")
        print(f"💬 Conversations: {conversation_db}")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    initialize_databases()
