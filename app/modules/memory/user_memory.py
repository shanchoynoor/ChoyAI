"""
User Memory Manager for Choy AI Brain

Manages user-specific memories and preferences
"""

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.config.settings import settings


class UserMemoryManager:
    """Manages user-specific memories and data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path = settings.user_memory_db
        self.connection: Optional[sqlite3.Connection] = None
        
    async def initialize(self):
        """Initialize user memory database"""
        self.logger.info("👤 Initializing User Memory Manager...")
        
        try:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            # Create tables
            await self._create_tables()
            
            self.logger.info("✅ User Memory Manager initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize User Memory Manager: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(100) UNIQUE NOT NULL,
            username VARCHAR(100),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            bio TEXT,
            preferred_persona VARCHAR(50) DEFAULT 'choy',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # User memories table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(100) NOT NULL,
            key VARCHAR(200) NOT NULL,
            value TEXT NOT NULL,
            context TEXT,
            category VARCHAR(100),
            importance INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key)
        )
        """)
        
        # User preferences table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(100) NOT NULL,
            key VARCHAR(100) NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key)
        )
        """)
        
        self.connection.commit()
        self.logger.debug("📝 User memory tables created")
    
    async def get_or_create_user(
        self,
        user_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing user or create new one"""
        try:
            cursor = self.connection.cursor()
            
            # Try to get existing user
            cursor.execute("""
            SELECT * FROM users WHERE user_id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            
            if user:
                # Update last active time
                cursor.execute("""
                UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?
                """, (user_id,))
                self.connection.commit()
                
                return dict(user)
            else:
                # Create new user
                cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                """, (user_id, username, first_name, last_name))
                self.connection.commit()
                
                self.logger.info(f"👋 Created new user: {user_id}")
                
                # Return the new user
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                return dict(cursor.fetchone())
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get/create user: {e}")
            return {}
    
    async def save_memory(
        self,
        user_id: str,
        key: str,
        value: str,
        context: Optional[str] = None,
        category: Optional[str] = None,
        importance: int = 1
    ) -> bool:
        """Save a user memory"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            INSERT OR REPLACE INTO user_memories 
            (user_id, key, value, context, category, importance, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, key, value, context, category, importance))
            
            self.connection.commit()
            
            self.logger.debug(f"💾 Saved memory for user {user_id}: {key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save memory: {e}")
            return False
    
    async def get_memory(self, user_id: str, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific user memory"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT * FROM user_memories 
            WHERE user_id = ? AND key = ?
            """, (user_id, key))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get memory: {e}")
            return None
    
    async def get_memories(
        self,
        user_id: str,
        limit: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user memories with optional filtering"""
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT * FROM user_memories WHERE user_id = ?"
            params = [user_id]
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY importance DESC, updated_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get memories: {e}")
            return []
    
    async def search_memories(self, user_id: str, search_term: str) -> List[Dict[str, Any]]:
        """Search user memories"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT * FROM user_memories 
            WHERE user_id = ? AND (key LIKE ? OR value LIKE ? OR context LIKE ?)
            ORDER BY importance DESC, updated_at DESC
            """, (user_id, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to search memories: {e}")
            return []
    
    async def delete_memory(self, user_id: str, key: str) -> bool:
        """Delete a user memory"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            DELETE FROM user_memories WHERE user_id = ? AND key = ?
            """, (user_id, key))
            
            self.connection.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.debug(f"🗑️ Deleted memory for user {user_id}: {key}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete memory: {e}")
            return False
    
    async def update_user_preference(self, user_id: str, key: str, value: str) -> bool:
        """Update user preference"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            INSERT OR REPLACE INTO user_preferences (user_id, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, key, value))
            
            self.connection.commit()
            
            self.logger.debug(f"⚙️ Updated preference for user {user_id}: {key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update preference: {e}")
            return False
    
    async def get_user_preference(self, user_id: str, key: str) -> Optional[str]:
        """Get user preference"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT value FROM user_preferences WHERE user_id = ? AND key = ?
            """, (user_id, key))
            
            row = cursor.fetchone()
            return row['value'] if row else None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get preference: {e}")
            return None
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            cursor = self.connection.cursor()
            
            # Get user info
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            # Count memories
            cursor.execute("SELECT COUNT(*) as count FROM user_memories WHERE user_id = ?", (user_id,))
            memory_count = cursor.fetchone()['count']
            
            # Count preferences
            cursor.execute("SELECT COUNT(*) as count FROM user_preferences WHERE user_id = ?", (user_id,))
            preferences_count = cursor.fetchone()['count']
            
            # Get memory categories
            cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM user_memories 
            WHERE user_id = ? AND category IS NOT NULL
            GROUP BY category
            """, (user_id,))
            category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
            
            return {
                "user_info": dict(user) if user else {},
                "total_memories": memory_count,
                "total_preferences": preferences_count,
                "memory_categories": category_counts
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get user stats: {e}")
            return {}
    
    async def get_total_users(self) -> int:
        """Get total number of users"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            return cursor.fetchone()['count']
        except Exception as e:
            self.logger.error(f"❌ Failed to get total users: {e}")
            return 0
    
    async def get_total_memories(self) -> int:
        """Get total number of memories"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM user_memories")
            return cursor.fetchone()['count']
        except Exception as e:
            self.logger.error(f"❌ Failed to get total memories: {e}")
            return 0
    
    async def shutdown(self):
        """Shutdown user memory manager"""
        if self.connection:
            self.connection.close()
            self.logger.info("👤 User Memory Manager shutdown complete")


# Export the main class
__all__ = ["UserMemoryManager"]
