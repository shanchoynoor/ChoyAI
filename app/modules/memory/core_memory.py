"""
Core Memory Manager for Choy AI Brain

Manages long-term core facts and knowledge
"""

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from app.config.settings import settings


class CoreMemoryManager:
    """Manages core facts and system knowledge"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path = settings.core_memory_db
        self.connection: Optional[sqlite3.Connection] = None
        
    async def initialize(self):
        """Initialize core memory database"""
        self.logger.info("🧠 Initializing Core Memory Manager...")
        
        try:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Create tables
            await self._create_tables()
            
            # Load initial knowledge if empty
            await self._load_initial_knowledge()
            
            self.logger.info("✅ Core Memory Manager initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Core Memory Manager: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Core facts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS core_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category VARCHAR(100) NOT NULL,
            key VARCHAR(200) NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            source VARCHAR(100),
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, key)
        )
        """)
        
        # Knowledge base table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            importance INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # System preferences table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        self.connection.commit()
        self.logger.debug("📝 Core memory tables created")
    
    async def _load_initial_knowledge(self):
        """Load initial core knowledge if database is empty"""
        cursor = self.connection.cursor()
        
        # Check if we have any core facts
        cursor.execute("SELECT COUNT(*) as count FROM core_facts")
        fact_count = cursor.fetchone()['count']
        
        if fact_count == 0:
            self.logger.info("📚 Loading initial core knowledge...")
            
            initial_facts = [
                # System facts
                ("system", "name", "Choy AI Brain", "The name of this AI system"),
                ("system", "version", "1.0.0", "Current system version"),
                ("system", "purpose", "Personal AI assistant with long-term memory and multiple personalities", "Main purpose of the system"),
                
                # Developer information
                ("developer", "name", "Shanchoy Noor", "Developer and founder of Choy AI"),
                ("developer", "display_name", "Choy (Choy AI Developer)", "Developer display name"),
                ("developer", "birthplace", "Bheramara, Kushtia", "Developer birthplace"),
                ("developer", "moved_to_dhaka", "2012", "Year moved to Dhaka"),
                ("developer", "experience", "8+ years", "Years of experience in design, AI, automation"),
                ("developer", "current_role", "UI/UX Designer & Video Editor at Iqrasys Solutions Ltd.", "Current primary employment"),
                ("developer", "social_media_management", "YouTube Village Park, AroundMeBD, Village Grandpa's Cooking", "Platforms managed"),
                ("developer", "company_founded", "Choy Agency Ltd", "Company founded by developer"),
                ("developer", "team_size", "30+ members", "Size of developer's agency team"),
                ("developer", "creator_of", "Choy AI", "What the developer created"),
                
                # Capabilities
                ("capabilities", "memory", "Long-term memory with semantic search", "Memory system capabilities"),
                ("capabilities", "personas", "Multiple AI personalities for different interaction styles", "Persona system capabilities"),
                ("capabilities", "integrations", "Telegram bot with planned expansions", "Integration capabilities"),
                
                # Personas
                ("personas", "default", "choy", "Default persona"),
                ("personas", "available", "choy,stark,rose", "Available personas"),
                
                # Platform info
                ("platform", "telegram", "Active", "Telegram integration status"),
                ("platform", "web", "Planned", "Web interface status"),
                ("platform", "mobile", "Planned", "Mobile app status"),
            ]
            
            for category, key, value, description in initial_facts:
                await self.save_core_fact(category, key, value, description, "system_init")
            
            # Load developer profile from YAML if it exists
            await self._load_developer_profile()
            
            self.logger.info(f"✅ Loaded {len(initial_facts)} initial core facts")
    
    async def _load_developer_profile(self):
        """Load developer profile from YAML file"""
        if not YAML_AVAILABLE:
            self.logger.warning("PyYAML not available, skipping developer profile loading")
            return
            
        try:
            profile_path = Path(settings.data_dir) / "core_memory" / "developer_profile.yaml"
            if profile_path.exists():
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = yaml.safe_load(f)
                
                # Store developer bio as a knowledge base entry
                await self.save_knowledge(
                    topic="developer_biography",
                    content=profile_data.get('short_bio', ''),
                    tags="developer,biography,founder",
                    importance=5
                )
                
                # Store privacy policy
                await self.save_knowledge(
                    topic="developer_privacy_policy",
                    content=profile_data.get('privacy_policy', ''),
                    tags="developer,privacy,policy",
                    importance=5
                )
                
                self.logger.info("✅ Loaded developer profile from YAML")
                
        except Exception as e:
            self.logger.warning(f"Could not load developer profile: {e}")
            # This is not critical, so we continue
    
    async def save_core_fact(
        self,
        category: str,
        key: str,
        value: str,
        description: Optional[str] = None,
        source: str = "user",
        confidence: float = 1.0
    ) -> bool:
        """Save a core fact"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            INSERT OR REPLACE INTO core_facts 
            (category, key, value, description, source, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (category, key, value, description, source, confidence))
            
            self.connection.commit()
            
            self.logger.debug(f"💾 Saved core fact: {category}.{key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save core fact: {e}")
            return False
    
    async def get_core_fact(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific core fact"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT * FROM core_facts 
            WHERE category = ? AND key = ?
            """, (category, key))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get core fact: {e}")
            return None
    
    async def get_facts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all facts in a category"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT * FROM core_facts 
            WHERE category = ?
            ORDER BY key
            """, (category,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get facts by category: {e}")
            return []
    
    async def search_facts(self, search_term: str) -> List[Dict[str, Any]]:
        """Search core facts"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT * FROM core_facts 
            WHERE key LIKE ? OR value LIKE ? OR description LIKE ?
            ORDER BY confidence DESC, updated_at DESC
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to search facts: {e}")
            return []
    
    async def add_knowledge(
        self,
        topic: str,
        content: str,
        tags: Optional[List[str]] = None,
        importance: int = 1
    ) -> bool:
        """Add knowledge to the knowledge base"""
        try:
            cursor = self.connection.cursor()
            
            tags_str = ",".join(tags) if tags else ""
            
            cursor.execute("""
            INSERT INTO knowledge_base (topic, content, tags, importance)
            VALUES (?, ?, ?, ?)
            """, (topic, content, tags_str, importance))
            
            self.connection.commit()
            
            self.logger.debug(f"📚 Added knowledge: {topic}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add knowledge: {e}")
            return False
    
    async def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT * FROM knowledge_base 
            WHERE topic LIKE ? OR content LIKE ? OR tags LIKE ?
            ORDER BY importance DESC, updated_at DESC
            LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to search knowledge: {e}")
            return []
    
    async def set_system_preference(self, key: str, value: str, description: str = None) -> bool:
        """Set a system preference"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            INSERT OR REPLACE INTO system_preferences (key, value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value, description))
            
            self.connection.commit()
            
            self.logger.debug(f"⚙️ Set system preference: {key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to set system preference: {e}")
            return False
    
    async def get_system_preference(self, key: str) -> Optional[str]:
        """Get a system preference"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            SELECT value FROM system_preferences WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            return row['value'] if row else None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get system preference: {e}")
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get core memory statistics"""
        try:
            cursor = self.connection.cursor()
            
            # Count facts by category
            cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM core_facts 
            GROUP BY category
            """)
            category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Total knowledge entries
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_base")
            knowledge_count = cursor.fetchone()['count']
            
            # Total preferences
            cursor.execute("SELECT COUNT(*) as count FROM system_preferences")
            preferences_count = cursor.fetchone()['count']
            
            return {
                "total_facts": sum(category_counts.values()),
                "facts_by_category": category_counts,
                "total_knowledge": knowledge_count,
                "total_preferences": preferences_count
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get stats: {e}")
            return {}
    
    async def shutdown(self):
        """Shutdown core memory manager"""
        if self.connection:
            self.connection.close()
            self.logger.info("💾 Core Memory Manager shutdown complete")


# Export the main class
__all__ = ["CoreMemoryManager"]
