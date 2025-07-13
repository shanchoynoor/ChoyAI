"""
Core AI Engine for Choy AI Brain

This is the central processing unit that handles:
- Conversation processing with long-term memory
- Persona-based response generation
- Context management across conversations
- Integration coordination
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from app.modules.memory.core_memory import CoreMemoryManager
from app.modules.memory.user_memory import UserMemoryManager
from app.modules.memory.conversation_memory import ConversationMemoryManager
from app.modules.personas.persona_manager import PersonaManager
from app.modules.chat.chat_engine import ChatEngine
from app.utils.deepseek_api import DeepSeekAPI
from app.config.settings import settings


@dataclass
class ConversationContext:
    """Context for a conversation"""
    user_id: str
    platform: str  # telegram, web, api
    persona: str
    session_id: str
    started_at: datetime
    last_activity: datetime
    message_count: int = 0
    context_data: Dict[str, Any] = None


class ChoyAIEngine:
    """Central AI processing engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.core_memory: Optional[CoreMemoryManager] = None
        self.user_memory: Optional[UserMemoryManager] = None
        self.conversation_memory: Optional[ConversationMemoryManager] = None
        self.persona_manager: Optional[PersonaManager] = None
        self.chat_engine: Optional[ChatEngine] = None
        self.deepseek_api: Optional[DeepSeekAPI] = None
        
        # Active conversations
        self.active_conversations: Dict[str, ConversationContext] = {}
        
        # Performance metrics
        self.total_messages_processed = 0
        self.total_personas_switched = 0
        self.average_response_time = 0.0
        
    async def initialize(self):
        """Initialize all AI engine components"""
        self.logger.info("🧠 Initializing AI Engine components...")
        
        try:
            # Initialize memory systems
            self.core_memory = CoreMemoryManager()
            await self.core_memory.initialize()
            
            self.user_memory = UserMemoryManager()
            await self.user_memory.initialize()
            
            self.conversation_memory = ConversationMemoryManager()
            await self.conversation_memory.initialize()
            
            # Initialize persona system
            self.persona_manager = PersonaManager()
            await self.persona_manager.initialize()
            
            # Initialize chat engine
            self.chat_engine = ChatEngine(
                core_memory=self.core_memory,
                user_memory=self.user_memory,
                conversation_memory=self.conversation_memory,
                persona_manager=self.persona_manager
            )
            await self.chat_engine.initialize()
            
            # Initialize DeepSeek API
            self.deepseek_api = DeepSeekAPI()
            
            self.logger.info("✅ AI Engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AI Engine: {e}")
            raise
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        platform: str = "telegram",
        persona: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a user message and generate AI response
        
        Args:
            user_id: Unique user identifier
            message: User message text
            platform: Platform source (telegram, web, api)
            persona: Requested persona (if any)
            context: Additional context data
            
        Returns:
            Generated AI response
        """
        start_time = datetime.now()
        
        try:
            # Get or create conversation context
            conversation_id = f"{platform}_{user_id}"
            conversation_ctx = await self._get_conversation_context(
                conversation_id, user_id, platform, persona
            )
            
            # Process the message through chat engine
            response = await self.chat_engine.process_message(
                user_id=user_id,
                message=message,
                conversation_context=conversation_ctx,
                additional_context=context
            )
            
            # Update conversation metrics
            conversation_ctx.message_count += 1
            conversation_ctx.last_activity = datetime.now()
            
            # Update performance metrics
            self.total_messages_processed += 1
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_response_time_metric(response_time)
            
            self.logger.debug(
                f"💬 Processed message for user {user_id} "
                f"in {response_time:.2f}s with persona '{conversation_ctx.persona}'"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error processing message for user {user_id}: {e}")
            return "I apologize, but I encountered an error processing your message. Please try again."
    
    async def switch_persona(
        self,
        user_id: str,
        persona_name: str,
        platform: str = "telegram"
    ) -> Dict[str, Any]:
        """
        Switch user's active persona
        
        Args:
            user_id: User identifier
            persona_name: Name of persona to switch to
            platform: Platform source
            
        Returns:
            Persona switch result with details
        """
        try:
            # Validate persona exists
            persona = await self.persona_manager.get_persona(persona_name)
            if not persona:
                return {
                    "success": False,
                    "error": f"Persona '{persona_name}' not found",
                    "available_personas": await self.persona_manager.list_persona_names()
                }
            
            # Update conversation context
            conversation_id = f"{platform}_{user_id}"
            if conversation_id in self.active_conversations:
                self.active_conversations[conversation_id].persona = persona_name
            
            # Update user's preferred persona
            await self.user_memory.update_user_preference(
                user_id, "preferred_persona", persona_name
            )
            
            # Update metrics
            self.total_personas_switched += 1
            
            self.logger.info(f"🎭 User {user_id} switched to persona '{persona_name}'")
            
            return {
                "success": True,
                "persona": {
                    "name": persona["name"],
                    "style": persona["style"],
                    "purpose": persona["purpose"],
                    "description": persona.get("description", "")
                },
                "message": f"Successfully switched to {persona_name} persona"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error switching persona for user {user_id}: {e}")
            return {
                "success": False,
                "error": "Failed to switch persona due to internal error"
            }
    
    async def get_user_memories(
        self,
        user_id: str,
        limit: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's memories with optional filtering"""
        try:
            return await self.user_memory.get_memories(
                user_id=user_id,
                limit=limit,
                category=category
            )
        except Exception as e:
            self.logger.error(f"❌ Error retrieving memories for user {user_id}: {e}")
            return []
    
    async def save_user_memory(
        self,
        user_id: str,
        key: str,
        value: str,
        context: Optional[str] = None,
        category: Optional[str] = None
    ) -> bool:
        """Save a user memory"""
        try:
            return await self.user_memory.save_memory(
                user_id=user_id,
                key=key,
                value=value,
                context=context,
                category=category
            )
        except Exception as e:
            self.logger.error(f"❌ Error saving memory for user {user_id}: {e}")
            return False
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 20,
        platform: str = "telegram"
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        try:
            return await self.conversation_memory.get_conversation_history(
                user_id=user_id,
                platform=platform,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"❌ Error retrieving conversation history for user {user_id}: {e}")
            return []
    
    async def get_ai_stats(self) -> Dict[str, Any]:
        """Get AI engine statistics"""
        return {
            "total_messages_processed": self.total_messages_processed,
            "total_personas_switched": self.total_personas_switched,
            "average_response_time": self.average_response_time,
            "active_conversations": len(self.active_conversations),
            "available_personas": await self.persona_manager.list_persona_names(),
            "memory_stats": {
                "total_users": await self.user_memory.get_total_users(),
                "total_memories": await self.user_memory.get_total_memories(),
                "total_conversations": await self.conversation_memory.get_total_conversations()
            }
        }
    
    async def _get_conversation_context(
        self,
        conversation_id: str,
        user_id: str,
        platform: str,
        requested_persona: Optional[str] = None
    ) -> ConversationContext:
        """Get or create conversation context"""
        
        if conversation_id not in self.active_conversations:
            # Get user's preferred persona or default to 'choy'
            user_persona = requested_persona
            if not user_persona:
                user_persona = await self.user_memory.get_user_preference(
                    user_id, "preferred_persona"
                ) or "choy"
            
            # Create new conversation context
            self.active_conversations[conversation_id] = ConversationContext(
                user_id=user_id,
                platform=platform,
                persona=user_persona,
                session_id=conversation_id,
                started_at=datetime.now(),
                last_activity=datetime.now(),
                context_data={}
            )
            
            self.logger.debug(f"📝 Created new conversation context for {conversation_id}")
        
        return self.active_conversations[conversation_id]
    
    def _update_response_time_metric(self, response_time: float):
        """Update average response time metric"""
        if self.total_messages_processed == 1:
            self.average_response_time = response_time
        else:
            # Calculate moving average
            weight = 0.1  # Weight for new response time
            self.average_response_time = (
                (1 - weight) * self.average_response_time + 
                weight * response_time
            )
    
    async def shutdown(self):
        """Gracefully shutdown the AI engine"""
        self.logger.info("🔄 Shutting down AI Engine...")
        
        try:
            # Save active conversation states
            for conversation_id, context in self.active_conversations.items():
                await self.conversation_memory.save_conversation_state(
                    conversation_id, context
                )
            
            # Shutdown components
            if self.chat_engine:
                await self.chat_engine.shutdown()
            
            if self.conversation_memory:
                await self.conversation_memory.shutdown()
            
            if self.user_memory:
                await self.user_memory.shutdown()
            
            if self.core_memory:
                await self.core_memory.shutdown()
            
            self.logger.info("✅ AI Engine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error during AI Engine shutdown: {e}")


# Export the main class
__all__ = ["ChoyAIEngine", "ConversationContext"]
