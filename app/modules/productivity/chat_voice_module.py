"""
Chat & Voice Module - ChoyAI Productivity Suite

Enhanced conversational AI with voice support
Integration with existing conversation flow
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

from app.modules.productivity import (
    BaseProductivityModule, ModuleRequest, ModuleResponse, ModuleConfig, ModuleType
)
from app.core.ai_providers import TaskType
from app.modules.conversation_flow import ConversationFlow


@dataclass
class ChatSession:
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    context_summary: Optional[str] = None


class ChatVoiceModule(BaseProductivityModule):
    """Enhanced chat and voice interaction module"""
    
    def __init__(self, config: ModuleConfig, ai_provider_manager):
        super().__init__(config, ai_provider_manager)
        self.conversation_flow = None
        self.active_sessions: Dict[str, ChatSession] = {}
        self.voice_enabled = False  # Will be enabled when voice APIs are configured
        
    async def initialize(self) -> bool:
        """Initialize chat and voice capabilities"""
        try:
            # Initialize conversation flow
            self.conversation_flow = ConversationFlow(self.ai_provider_manager)
            await self.conversation_flow.initialize()
            
            self.logger.info("✅ Chat & Voice module initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize chat module: {e}")
            return False
    
    async def process_request(self, request: ModuleRequest) -> ModuleResponse:
        """Process chat and voice requests"""
        action = request.action.lower()
        
        handlers = {
            # Chat functions
            "chat": self._handle_chat,
            "start_session": self._start_chat_session,
            "end_session": self._end_chat_session,
            "get_history": self._get_chat_history,
            "summarize_session": self._summarize_session,
            
            # Voice functions (placeholder for future)
            "voice_to_text": self._voice_to_text,
            "text_to_voice": self._text_to_voice,
            
            # AI assistance
            "get_suggestions": self._get_suggestions,
            "analyze_conversation": self._analyze_conversation,
            "set_context": self._set_context
        }
        
        if action not in handlers:
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Unknown action: {action}",
                error="INVALID_ACTION"
            )
        
        try:
            return await handlers[action](request)
        except Exception as e:
            self.logger.error(f"Error processing {action}: {e}")
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Error processing {action}: {str(e)}",
                error=str(e)
            )
    
    async def _handle_chat(self, request: ModuleRequest) -> ModuleResponse:
        """Handle chat conversation with cost optimization"""
        data = request.data
        message = data.get("message", "").strip()
        
        if not message:
            return ModuleResponse(
                success=False,
                data=None,
                message="Message content is required",
                error="MISSING_MESSAGE"
            )
        
        session_id = data.get("session_id")
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            # Create new session
            session = ChatSession(
                id=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id=request.user_id,
                title=f"Chat {datetime.now().strftime('%H:%M')}",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.active_sessions[session.id] = session
        
        # Prepare conversation context
        conversation_context = {
            "user_id": request.user_id,
            "session_id": session.id,
            "message": message,
            "context": data.get("context", {}),
            "use_rag": data.get("use_rag", True),
            "productivity_mode": True
        }
        
        # Use conversation flow for response
        try:
            start_time = datetime.now()
            
            # Process message through conversation flow
            ai_response = await self.conversation_flow.process_message(
                user_id=request.user_id,
                message=message,
                context=conversation_context
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update session metrics
            session.message_count += 1
            session.updated_at = datetime.now()
            if hasattr(ai_response, 'usage') and ai_response.usage:
                session.total_tokens += ai_response.usage.get('total_tokens', 0)
            
            # Estimate cost
            estimated_cost = self._estimate_conversation_cost(ai_response)
            session.total_cost += estimated_cost
            self.daily_cost += estimated_cost
            
            # Prepare response
            response_data = {
                "response": ai_response.content if hasattr(ai_response, 'content') else str(ai_response),
                "session_id": session.id,
                "session_stats": {
                    "messages": session.message_count,
                    "total_tokens": session.total_tokens,
                    "total_cost": session.total_cost
                },
                "suggestions": await self._get_response_suggestions(message, ai_response)
            }
            
            return ModuleResponse(
                success=True,
                data=response_data,
                message="Chat response generated",
                cost_estimate=estimated_cost,
                processing_time=processing_time,
                ai_provider_used=getattr(ai_response, 'provider_used', 'unknown')
            )
            
        except Exception as e:
            self.logger.error(f"Conversation flow error: {e}")
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Failed to process chat message: {str(e)}",
                error=str(e)
            )
    
    async def _start_chat_session(self, request: ModuleRequest) -> ModuleResponse:
        """Start a new chat session"""
        data = request.data
        
        session = ChatSession(
            id=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_sessions)}",
            user_id=request.user_id,
            title=data.get("title", f"Chat {datetime.now().strftime('%H:%M')}"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.active_sessions[session.id] = session
        
        return ModuleResponse(
            success=True,
            data=asdict(session),
            message="Chat session started"
        )
    
    async def _end_chat_session(self, request: ModuleRequest) -> ModuleResponse:
        """End and optionally summarize a chat session"""
        session_id = request.data.get("session_id")
        
        if not session_id or session_id not in self.active_sessions:
            return ModuleResponse(
                success=False,
                data=None,
                message="Session not found",
                error="SESSION_NOT_FOUND"
            )
        
        session = self.active_sessions[session_id]
        
        # Generate session summary if requested
        summary = None
        if request.data.get("generate_summary", False) and session.message_count > 3:
            summary_response = await self._generate_session_summary(session)
            if summary_response.success:
                summary = summary_response.data
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return ModuleResponse(
            success=True,
            data={
                "session": asdict(session),
                "summary": summary,
                "final_stats": {
                    "messages": session.message_count,
                    "duration": (session.updated_at - session.created_at).total_seconds(),
                    "total_cost": session.total_cost
                }
            },
            message="Chat session ended"
        )
    
    async def _generate_session_summary(self, session: ChatSession) -> ModuleResponse:
        """Generate AI summary of chat session"""
        messages = [
            {
                "role": "system",
                "content": """You are a conversation summarizer. Create a brief summary of the chat session including:
1. Main topics discussed
2. Key decisions or outcomes
3. Action items (if any)
4. Overall sentiment

Keep it concise but informative."""
            },
            {
                "role": "user",
                "content": f"""Please summarize this chat session:
Session ID: {session.id}
Duration: {session.message_count} messages
Started: {session.created_at.strftime('%Y-%m-%d %H:%M')}

Create a brief summary of the conversation."""
            }
        ]
        
        return await self._use_ai_provider(messages, TaskType.ANALYSIS)
    
    async def _get_suggestions(self, request: ModuleRequest) -> ModuleResponse:
        """Get AI suggestions for conversation topics"""
        user_id = request.user_id
        context = request.data.get("context", {})
        
        messages = [
            {
                "role": "system",
                "content": """You are a productivity AI assistant. Based on the user's context and current time, suggest 5-7 helpful conversation topics or questions they might want to ask. Focus on:
1. Productivity and task management
2. Current date/time relevant topics
3. Work-related assistance
4. Personal development
5. Problem-solving

Respond in JSON format:
{
    "suggestions": [
        {"topic": "Topic name", "question": "Sample question", "category": "productivity/work/personal"}
    ]
}"""
            },
            {
                "role": "user",
                "content": f"""Current context:
Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
User ID: {user_id}
Context: {json.dumps(context, indent=2)}

Please suggest helpful conversation topics for this user."""
            }
        ]
        
        return await self._use_ai_provider(messages, TaskType.CONVERSATION)
    
    async def _get_response_suggestions(self, user_message: str, ai_response) -> List[str]:
        """Get follow-up suggestions based on the conversation"""
        # Simple follow-up suggestions based on message content
        suggestions = []
        
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['task', 'todo', 'remind']):
            suggestions.append("Create a task or reminder")
            
        if any(word in message_lower for word in ['note', 'write', 'remember']):
            suggestions.append("Save this as a note")
            
        if any(word in message_lower for word in ['schedule', 'meeting', 'calendar']):
            suggestions.append("Add to calendar")
            
        if any(word in message_lower for word in ['analyze', 'research', 'learn']):
            suggestions.append("Get more detailed analysis")
            
        # Always include these general options
        suggestions.extend([
            "Ask a follow-up question",
            "Get more details",
            "Start a new topic"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _estimate_conversation_cost(self, ai_response) -> float:
        """Estimate cost of conversation"""
        if not hasattr(ai_response, 'usage') or not ai_response.usage:
            return 0.01  # Default small cost
        
        tokens = ai_response.usage.get('total_tokens', 100)
        provider = getattr(ai_response, 'provider_used', 'unknown')
        
        # Cost per 1K tokens by provider (conversation rates)
        provider_costs = {
            'openai': 0.03,     # GPT-4o
            'anthropic': 0.025, # Claude
            'deepseek': 0.002,  # DeepSeek (very cheap)
            'gemini': 0.015,    # Gemini
            'xai': 0.02         # xAI
        }
        
        rate = provider_costs.get(provider, 0.02)
        return (tokens / 1000.0) * rate
    
    # Placeholder voice functions (for future implementation)
    async def _voice_to_text(self, request: ModuleRequest) -> ModuleResponse:
        """Convert voice to text (placeholder)"""
        return ModuleResponse(
            success=False,
            data=None,
            message="Voice-to-text not yet implemented",
            error="NOT_IMPLEMENTED"
        )
    
    async def _text_to_voice(self, request: ModuleRequest) -> ModuleResponse:
        """Convert text to voice (placeholder)"""
        return ModuleResponse(
            success=False,
            data=None,
            message="Text-to-voice not yet implemented", 
            error="NOT_IMPLEMENTED"
        )
    
    async def get_capabilities(self) -> List[str]:
        """Get module capabilities"""
        return [
            "chat", "start_session", "end_session", "get_history", 
            "summarize_session", "get_suggestions", "analyze_conversation",
            "set_context"
            # Voice capabilities will be added later
            # "voice_to_text", "text_to_voice"
        ]
    
    async def _module_health_check(self) -> bool:
        """Check if chat module is healthy"""
        try:
            # Check if conversation flow is available
            return (self.conversation_flow is not None and 
                    hasattr(self.conversation_flow, 'process_message'))
        except Exception:
            return False
