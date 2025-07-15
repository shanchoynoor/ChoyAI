"""
Core AI Engine for Choy AI Brain

This is the central processing unit tha            # Initialize persona manager
            self.persona_manager = PersonaManager()
            await self.persona_manager.initialize()
            
            # Initialize user profile manager
            self.user_profile_manager = UserProfileManager()
            
            # Initialize AI Provider Manager
            self.ai_provider_manager = AIProviderManager()
            await self.ai_provider_manager.initialize()es:
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
from app.modules.memory.vector_memory import VectorMemoryManager
from app.modules.personas.persona_manager import PersonaManager
from app.modules.chat.chat_engine import ChatEngine
from app.modules.users.user_profile_manager import UserProfileManager
from app.modules.rag_engine import RAGEngine
from app.modules.conversation_flow import ConversationFlowManager
from app.core.ai_providers import AIProviderManager, AIMessage, TaskType
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
        self.vector_memory: Optional[VectorMemoryManager] = None
        self.rag_engine: Optional[RAGEngine] = None
        self.conversation_flow: Optional[ConversationFlowManager] = None
        self.persona_manager: Optional[PersonaManager] = None
        self.chat_engine: Optional[ChatEngine] = None
        self.ai_provider_manager: Optional[AIProviderManager] = None
        self.user_profile_manager: Optional[UserProfileManager] = None
        
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
            
            # Initialize vector memory and RAG engine
            self.vector_memory = VectorMemoryManager()
            await self.vector_memory.initialize()
            
            self.rag_engine = RAGEngine()
            await self.rag_engine.initialize()
            
            # Initialize conversation flow manager
            self.conversation_flow = ConversationFlowManager(
                ai_engine=self,
                rag_engine=self.rag_engine
            )
            await self.conversation_flow.initialize()
            
            # Initialize persona system
            self.persona_manager = PersonaManager()
            await self.persona_manager.initialize()
            
            # Initialize user profile manager (no async init needed)
            self.user_profile_manager = UserProfileManager()
            
            # Initialize AI Provider Manager
            self.ai_provider_manager = AIProviderManager()
            await self.ai_provider_manager.initialize()
            
            # Initialize chat engine with AI provider manager
            self.chat_engine = ChatEngine(
                core_memory=self.core_memory,
                user_memory=self.user_memory,
                conversation_memory=self.conversation_memory,
                persona_manager=self.persona_manager,
                ai_provider_manager=self.ai_provider_manager,
                rag_engine=self.rag_engine
            )
            await self.chat_engine.initialize()
            
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
        Process a user message and generate AI response with enhanced conversation flow
        
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
            
            # Process user message for profiling
            platform_data = context.get('platform_data', {}) if context else {}
            
            # Extract user information and save conversation
            extracted_info, updated_profile = await self.user_profile_manager.process_conversation(
                user_id=user_id,
                message=message,
                message_type="user_message",
                platform=platform,
                persona_used=conversation_ctx.persona,
                platform_data=platform_data,
                session_id=conversation_ctx.session_id
            )
            
            # Get user profile for enhanced context
            user_profile = await self.user_profile_manager.get_user_profile(user_id)
            
            # Enhanced context with user profile
            enhanced_context = context.copy() if context else {}
            enhanced_context.update({
                'user_profile': user_profile,
                'extracted_info': extracted_info,
                'updated_profile': updated_profile
            })
            
            # Process through LangGraph conversation flow if available
            if self.conversation_flow:
                try:
                    response, flow_metadata = await self.conversation_flow.process_conversation(
                        user_id=user_id,
                        message=message,
                        conversation_context={
                            'platform': platform,
                            'session_id': conversation_ctx.session_id,
                            'user_profile': user_profile,
                            'enhanced_context': enhanced_context
                        },
                        persona=conversation_ctx.persona
                    )
                    
                    # Update conversation context with flow metadata
                    conversation_ctx.context_data = conversation_ctx.context_data or {}
                    conversation_ctx.context_data.update({
                        'flow_metadata': flow_metadata,
                        'processing_method': 'langgraph_flow'
                    })
                    
                    self.logger.debug(f"🔄 Processed via LangGraph flow - Intent: {flow_metadata.get('intent', 'unknown')}")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ LangGraph flow failed, falling back to chat engine: {e}")
                    # Fallback to standard chat engine processing
                    response = await self._process_with_chat_engine(
                        user_id, message, conversation_ctx, enhanced_context
                    )
                    conversation_ctx.context_data = conversation_ctx.context_data or {}
                    conversation_ctx.context_data['processing_method'] = 'chat_engine_fallback'
            else:
                # Standard chat engine processing
                response = await self._process_with_chat_engine(
                    user_id, message, conversation_ctx, enhanced_context
                )
                conversation_ctx.context_data = conversation_ctx.context_data or {}
                conversation_ctx.context_data['processing_method'] = 'chat_engine_standard'
            
            # Save AI response to conversation history
            ai_provider = enhanced_context.get('ai_provider_used', 'unknown')
            task_type = enhanced_context.get('task_type_used', 'conversation')
            
            await self.user_profile_manager.process_conversation(
                user_id=user_id,
                message=response,
                message_type="ai_response",
                platform=platform,
                persona_used=conversation_ctx.persona,
                ai_provider=ai_provider,
                task_type=task_type,
                session_id=conversation_ctx.session_id
            )
            
            # Update conversation metrics
            conversation_ctx.message_count += 1
            conversation_ctx.last_activity = datetime.now()
            
            # Update performance metrics
            self.total_messages_processed += 1
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_response_time_metric(response_time)
            
            # Log with user insights
            user_insights = f" (Profile: {user_profile.name if user_profile and user_profile.name else 'Unknown'})"
            self.logger.debug(
                f"💬 Processed message for user {user_id}{user_insights} "
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
                    "name": persona.name,
                    "style": persona.style,
                    "purpose": persona.purpose,
                    "description": persona.description
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
    
    async def switch_ai_provider(self, task_type: TaskType, provider_name: str) -> bool:
        """
        Switch the primary AI provider for a specific task type
        
        Args:
            task_type: The task type to configure
            provider_name: Name of the provider to use
            
        Returns:
            True if switch was successful
        """
        try:
            if not self.ai_provider_manager:
                self.logger.error("AI Provider Manager not initialized")
                return False
                
            await self.ai_provider_manager.switch_primary_provider(task_type, provider_name)
            self.logger.info(f"Switched {task_type.value} provider to {provider_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch provider: {e}")
            return False
    
    async def get_ai_provider_status(self) -> Dict[str, Any]:
        """Get status of all AI providers"""
        if not self.ai_provider_manager:
            return {"error": "AI Provider Manager not initialized"}
            
        return await self.ai_provider_manager.get_provider_status()
    
    async def process_message_with_provider(
        self,
        user_id: str,
        message: str,
        task_type: TaskType = TaskType.CONVERSATION,
        preferred_provider: Optional[str] = None,
        platform: str = "telegram",
        persona: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a message with specific task type and optional provider preference
        
        Args:
            user_id: Unique user identifier
            message: User message text
            task_type: Type of task for AI provider selection
            preferred_provider: Force use of specific provider
            platform: Platform source
            persona: Requested persona
            context: Additional context data
            
        Returns:
            Generated AI response
        """
        # Use existing process_message but with enhanced context
        enhanced_context = context or {}
        enhanced_context.update({
            "task_type": task_type,
            "preferred_provider": preferred_provider
        })
        
        return await self.process_message(
            user_id=user_id,
            message=message,
            platform=platform,
            persona=persona,
            context=enhanced_context
        )

    async def _process_with_chat_engine(
        self,
        user_id: str,
        message: str,
        conversation_ctx: ConversationContext,
        enhanced_context: Dict[str, Any]
    ) -> str:
        """Process message using the standard chat engine"""
        return await self.chat_engine.process_message(
            user_id=user_id,
            message=message,
            conversation_context=conversation_ctx,
            additional_context=enhanced_context
        )

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

    async def get_user_profile(self, user_id: str) -> Optional[Any]:
        """Get comprehensive user profile"""
        if not self.user_profile_manager:
            return None
        return await self.user_profile_manager.get_user_profile(user_id)
    
    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user analytics and insights"""
        if not self.user_profile_manager:
            return {}
        return await self.user_profile_manager.get_user_analytics(user_id)
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 50,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get user conversation history"""
        if not self.user_profile_manager:
            return []
        return await self.user_profile_manager.get_conversation_history(
            user_id, limit, days_back
        )
    
    async def search_users_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: int = 100
    ) -> List[Any]:
        """Search users by profile criteria"""
        if not self.user_profile_manager:
            return []
        return await self.user_profile_manager.search_users(criteria, limit)


# Export the main class
__all__ = ["ChoyAIEngine", "ConversationContext"]
