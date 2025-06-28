import sqlite3
from pathlib import Path

def initialize_database():
    # Ensure directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Initialize user_memories.db
    with sqlite3.connect("user_memories.db") as conn:
        cursor = conn.cursor()
        
        # Create personas table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            name TEXT PRIMARY KEY,
            creator TEXT DEFAULT 'system',
            style TEXT NOT NULL,
            purpose TEXT NOT NULL,
            rules TEXT,
            persona_core TEXT,
            persona_traits TEXT,
            persona_refs TEXT,
            catchphrases TEXT,
            modes TEXT,
            is_active BOOLEAN DEFAULT 0,
            system_prompt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create other tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key)
        )
        """)
        
        # Insert default personas
        default_personas = [
            {
                'name': 'choy',
                'style': 'Confident, strategic, no-fluff',
                'purpose': 'Primary assistant persona',
                'system_prompt': 'You are Choy...'
            },
            {
                'name': 'stark',
                'style': 'Tech genius, sarcastic',
                'purpose': 'Technical discussions',
                'system_prompt': 'You are Tony Stark...'
            },
            {
                'name': 'rose',
                'style': 'Charming, flirtatious',
                'purpose': 'Social interactions',
                'system_prompt': 'You are Rose...'
            }
        ]
        
        for persona in default_personas:
            cursor.execute(
                """INSERT OR IGNORE INTO personas 
                (name, style, purpose, system_prompt) 
                VALUES (?, ?, ?, ?)""",
                (persona['name'], persona['style'], 
                 persona['purpose'], persona['system_prompt'])
            )
        
        conn.commit()
        print("✅ Database initialized successfully")

if __name__ == "__main__":
    initialize_database()
