import sqlite3
from datetime import datetime
from typing import Optional, Dict, List

class UserMemory:
    def __init__(self, db_path: str = 'user_memories.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize user memory database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    bio TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, key)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    persona_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()
    
    def get_or_create_user(self, user_id: int, **kwargs):
        """Get or create user profile"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Try to get existing user
                user = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
                
                if not user:
                    # Create new user
                    conn.execute("""
                        INSERT INTO users 
                        (user_id, username, first_name, last_name) 
                        VALUES (?, ?, ?, ?)
                    """, (
                        user_id,
                        kwargs.get('username'),
                        kwargs.get('first_name'),
                        kwargs.get('last_name')
                    ))
                    conn.commit()
                    return self.get_or_create_user(user_id, **kwargs)
                return dict(user)
        except sqlite3.Error as e:
            raise Exception(f"User memory error: {str(e)}")
    
    def add_memory(self, user_id: int, key: str, value: str, context: str = None) -> bool:
        """Add user memory with context"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_memories 
                    (user_id, key, value, context)
                    VALUES (?, ?, ?, ?)
                """, (user_id, key.lower(), value.strip(), context))
                conn.commit()
                return True
        except sqlite3.Error as e:
            raise Exception(f"User memory error: {str(e)}")
    
    def get_memories(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get user memories"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT key, value, context FROM user_memories 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise Exception(f"User memory error: {str(e)}")
    
    def log_conversation(self, user_id: int, persona_name: str, message: str, response: str):
        """Log conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO conversations 
                    (user_id, persona_name, message, response)
                    VALUES (?, ?, ?, ?)
                """, (user_id, persona_name, message, response))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"User memory error: {str(e)}")
