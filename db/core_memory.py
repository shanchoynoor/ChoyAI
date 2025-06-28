# db/core_memory.py
import sqlite3
from pathlib import Path
import logging
from config import config

logger = logging.getLogger(__name__)

class CoreMemory:
    def __init__(self, db_path=None):
        # Ensure Path object is used consistently
        self.db_path = Path(db_path) if db_path else config.CORE_MEMORY_DB
        
        # Convert to string only for SQLite operations
        self.db_path_str = str(self.db_path)
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        
    def _init_db(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path_str) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        user_id TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, key)
                    )
                    """
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def store(self, user_id: str, key: str, value: str):
        """Store a key-value pair"""
        try:
            with sqlite3.connect(self.db_path_str) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO memories VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                    (user_id, key, str(value))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    def retrieve(self, user_id: str, key: str) -> str:
        """Retrieve a stored value"""
        try:
            with sqlite3.connect(self.db_path_str) as conn:
                cursor = conn.execute(
                    "SELECT value FROM memories WHERE user_id = ? AND key = ?",
                    (user_id, key)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return None
