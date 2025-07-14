"""
Conversation Memory Manager for Choy AI Brain

Manages conversation history and context
"""

import asyncio
import logging
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.config.settings import settings


class ConversationMemoryManager:
    """Manages conversation history and context"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path = settings.conversation_db
        self.connection: Optional[sqlite3.Connection] = None
        
    async def initialize(self):
        """Initialize conversation memory database"""
        self.logger.info("💬 Initializing Conversation Memory Manager...")
        
        try:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            # Create tables
            await self._create_tables()
            
            self.logger.info("✅ Conversation Memory Manager initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Conversation Memory Manager: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Conversations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(100) NOT NULL,
            platform VARCHAR(50) NOT NULL,
            session_id VARCHAR(200),
            persona VARCHAR(50),
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active'
        )
        """)
        
        # Messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            message_type VARCHAR(20) NOT NULL, -- 'user' or 'ai'
            content TEXT NOT NULL,
            persona VARCHAR(50),
            metadata TEXT, -- JSON metadata
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        """)
        
        # Conversation summaries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            summary TEXT NOT NULL,
            key_topics TEXT, -- JSON array of topics
            sentiment VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        """)
        
        self.connection.commit()
        self.logger.debug("📝 Conversation memory tables created")
    
    async def start_conversation(
        self,
        user_id: str,
        platform: str,
        session_id: Optional[str] = None,
        persona: str = "choy"
    ) -> int:
        """Start a new conversation"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            INSERT INTO conversations (user_id, platform, session_id, persona)
            VALUES (?, ?, ?, ?)
            """, (user_id, platform, session_id, persona))
            
            self.connection.commit()
            conversation_id = cursor.lastrowid
            
            self.logger.debug(f"🆕 Started conversation {conversation_id} for user {user_id}")
            return conversation_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start conversation: {e}")
            return 0
    
    async def log_message(
        self,
        conversation_id: int,
        user_id: str,
        role: str,  # 'user', 'assistant', or 'system'
        content: str,
        persona: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> bool:
        """Log a message in the conversation"""
        try:
            cursor = self.connection.cursor()
            
            # Convert legacy message_type to role format
            if role == "ai":
                role = "assistant"
            elif role not in ["user", "assistant", "system"]:
                role = "user"  # Default fallback
            
            # Handle metadata serialization safely
            metadata_json = None
            if metadata:
                try:
                    # Check if any value is a UserPersona object and convert to dict
                    serializable_metadata = {}
                    for key, value in metadata.items():
                        if hasattr(value, 'to_dict'):  # UserPersona or similar objects
                            serializable_metadata[key] = value.to_dict()
                        else:
                            serializable_metadata[key] = value
                    metadata_json = json.dumps(serializable_metadata)
                except (TypeError, AttributeError) as e:
                    self.logger.warning(f"Could not serialize metadata: {e}")
                    metadata_json = json.dumps({"error": "Failed to serialize metadata"})
            
            cursor.execute("""
            INSERT INTO messages (conversation_id, user_id, role, content, persona, metadata, provider, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (conversation_id, user_id, role, content, persona, metadata_json, provider, model))
            
            # Update conversation activity
            cursor.execute("""
            UPDATE conversations 
            SET last_activity = CURRENT_TIMESTAMP, 
                message_count = message_count + 1 
            WHERE id = ?
            """, (conversation_id,))
            
            self.connection.commit()
            
            self.logger.debug(f"💬 Logged {role} message in conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to log message: {e}")
            return False
    
    async def get_conversation_history(
        self,
        user_id: str,
        platform: str = None,
        limit: int = 20,
        conversation_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        try:
            cursor = self.connection.cursor()
            
            if conversation_id:
                # Get specific conversation
                cursor.execute("""
                SELECT m.*, c.persona as conversation_persona
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.conversation_id = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
                """, (conversation_id, limit))
            else:
                # Get recent messages across all conversations
                query = """
                SELECT m.*, c.persona as conversation_persona
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.user_id = ?
                """
                params = [user_id]
                
                if platform:
                    query += " AND c.platform = ?"
                    params.append(platform)
                
                query += " ORDER BY m.timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
            
            messages = []
            for row in cursor.fetchall():
                message = dict(row)
                # Parse metadata if present
                if message['metadata']:
                    try:
                        message['metadata'] = json.loads(message['metadata'])
                    except json.JSONDecodeError:
                        message['metadata'] = {}
                
                messages.append(message)
            
            return messages
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get conversation history: {e}")
            return []
    
    async def get_active_conversation(
        self,
        user_id: str,
        platform: str,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get active conversation for user"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT * FROM conversations 
            WHERE user_id = ? AND platform = ? AND status = 'active'
            """
            params = [user_id, platform]
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            query += " ORDER BY last_activity DESC LIMIT 1"
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get active conversation: {e}")
            return None
    
    async def close_conversation(self, conversation_id: int) -> bool:
        """Close a conversation"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
            UPDATE conversations 
            SET status = 'closed' 
            WHERE id = ?
            """, (conversation_id,))
            
            self.connection.commit()
            
            self.logger.debug(f"🔒 Closed conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to close conversation: {e}")
            return False
    
    async def create_conversation_summary(
        self,
        conversation_id: int,
        summary: str,
        key_topics: List[str] = None,
        sentiment: str = "neutral"
    ) -> bool:
        """Create a summary for a conversation"""
        try:
            cursor = self.connection.cursor()
            
            topics_json = json.dumps(key_topics) if key_topics else None
            
            cursor.execute("""
            INSERT INTO conversation_summaries (conversation_id, summary, key_topics, sentiment)
            VALUES (?, ?, ?, ?)
            """, (conversation_id, summary, topics_json, sentiment))
            
            self.connection.commit()
            
            self.logger.debug(f"📋 Created summary for conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create conversation summary: {e}")
            return False
    
    async def get_conversation_context(
        self,
        user_id: str,
        platform: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get conversation context for generating responses"""
        try:
            # Get recent messages
            recent_messages = await self.get_conversation_history(
                user_id=user_id,
                platform=platform,
                limit=limit
            )
            
            # Get active conversation
            active_conversation = await self.get_active_conversation(
                user_id=user_id,
                platform=platform
            )
            
            return {
                "recent_messages": recent_messages,
                "active_conversation": active_conversation,
                "message_count": len(recent_messages)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get conversation context: {e}")
            return {}
    
    async def save_conversation_state(self, conversation_id: str, context: Any) -> bool:
        """Save conversation state (placeholder for future implementation)"""
        # This could be implemented to save conversation state
        # For now, just log the action
        self.logger.debug(f"💾 Saving conversation state for {conversation_id}")
        return True
    
    async def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a user"""
        try:
            cursor = self.connection.cursor()
            
            # Total conversations
            cursor.execute("""
            SELECT COUNT(*) as count FROM conversations WHERE user_id = ?
            """, (user_id,))
            total_conversations = cursor.fetchone()['count']
            
            # Total messages
            cursor.execute("""
            SELECT COUNT(*) as count FROM messages WHERE user_id = ?
            """, (user_id,))
            total_messages = cursor.fetchone()['count']
            
            # Messages by type
            cursor.execute("""
            SELECT message_type, COUNT(*) as count 
            FROM messages 
            WHERE user_id = ? 
            GROUP BY message_type
            """, (user_id,))
            message_types = {row['message_type']: row['count'] for row in cursor.fetchall()}
            
            # Active conversations
            cursor.execute("""
            SELECT COUNT(*) as count 
            FROM conversations 
            WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            active_conversations = cursor.fetchone()['count']
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "messages_by_type": message_types,
                "active_conversations": active_conversations
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get conversation stats: {e}")
            return {}
    
    async def get_total_conversations(self) -> int:
        """Get total number of conversations"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM conversations")
            return cursor.fetchone()['count']
        except Exception as e:
            self.logger.error(f"❌ Failed to get total conversations: {e}")
            return 0
    
    async def cleanup_old_conversations(self, days_old: int = 30) -> int:
        """Clean up old conversations"""
        try:
            cursor = self.connection.cursor()
            
            # Close old inactive conversations
            cursor.execute("""
            UPDATE conversations 
            SET status = 'archived' 
            WHERE status = 'active' 
            AND last_activity < datetime('now', '-{} days')
            """.format(days_old))
            
            archived_count = cursor.rowcount
            self.connection.commit()
            
            self.logger.info(f"🧹 Archived {archived_count} old conversations")
            return archived_count
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup conversations: {e}")
            return 0
    
    async def shutdown(self):
        """Shutdown conversation memory manager"""
        if self.connection:
            self.connection.close()
            self.logger.info("💬 Conversation Memory Manager shutdown complete")


# Export the main class
__all__ = ["ConversationMemoryManager"]
