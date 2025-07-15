"""
Integration tests for enhanced AI engine with RAG and conversation flow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.ai_engine import ChoyAIEngine
from app.modules.memory.vector_memory import VectorMemoryManager
from app.modules.rag_engine import RAGEngine
from app.modules.conversation_flow import ConversationFlowManager


class TestEnhancedAIEngine:
    """Test the enhanced AI engine with all new features"""
    
    @pytest.fixture
    async def enhanced_ai_engine(self, sample_user_data, mock_ai_provider):
        """Create enhanced AI engine with mocked dependencies"""
        engine = ChoyAIEngine()
        
        # Mock all the components to avoid real database/API calls
        engine.core_memory = AsyncMock()
        engine.user_memory = AsyncMock()
        engine.conversation_memory = AsyncMock()
        engine.vector_memory = AsyncMock()
        engine.rag_engine = AsyncMock()
        engine.conversation_flow = AsyncMock()
        engine.persona_manager = AsyncMock()
        engine.ai_provider_manager = AsyncMock()
        engine.user_profile_manager = AsyncMock()
        engine.chat_engine = AsyncMock()
        
        # Mock initialization methods
        for component in [engine.core_memory, engine.user_memory, engine.conversation_memory,
                         engine.vector_memory, engine.rag_engine, engine.conversation_flow,
                         engine.persona_manager, engine.ai_provider_manager]:
            component.initialize.return_value = True
        
        # Mock user profile manager methods
        engine.user_profile_manager.process_conversation.return_value = ({}, {})
        engine.user_profile_manager.get_user_profile.return_value = sample_user_data
        
        # Mock conversation flow response
        engine.conversation_flow.process_conversation.return_value = (
            "Enhanced response from conversation flow", 
            {"intent": "general_chat", "flow_state": "completed"}
        )
        
        # Mock chat engine fallback
        engine.chat_engine.process_message.return_value = "Fallback response from chat engine"
        
        await engine.initialize()
        return engine
    
    @pytest.mark.asyncio
    async def test_enhanced_initialization(self, enhanced_ai_engine):
        """Test that all enhanced components are initialized"""
        assert enhanced_ai_engine.vector_memory is not None
        assert enhanced_ai_engine.rag_engine is not None
        assert enhanced_ai_engine.conversation_flow is not None
        
        # Verify initialization was called
        enhanced_ai_engine.vector_memory.initialize.assert_called_once()
        enhanced_ai_engine.rag_engine.initialize.assert_called_once()
        enhanced_ai_engine.conversation_flow.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_message_processing_with_conversation_flow(self, enhanced_ai_engine):
        """Test message processing using the conversation flow"""
        response = await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="Hello, how are you today?",
            platform="telegram",
            persona="choy"
        )
        
        assert response == "Enhanced response from conversation flow"
        
        # Verify conversation flow was called
        enhanced_ai_engine.conversation_flow.process_conversation.assert_called_once()
        
        # Verify user profile processing
        enhanced_ai_engine.user_profile_manager.process_conversation.assert_called()
    
    @pytest.mark.asyncio
    async def test_conversation_flow_fallback(self, enhanced_ai_engine):
        """Test fallback to chat engine when conversation flow fails"""
        # Make conversation flow raise an exception
        enhanced_ai_engine.conversation_flow.process_conversation.side_effect = Exception("Flow error")
        
        response = await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="Test message",
            platform="telegram"
        )
        
        assert response == "Fallback response from chat engine"
        
        # Verify chat engine was called as fallback
        enhanced_ai_engine.chat_engine.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_no_conversation_flow_fallback(self, enhanced_ai_engine):
        """Test behavior when conversation flow is not available"""
        # Disable conversation flow
        enhanced_ai_engine.conversation_flow = None
        
        response = await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="Test message",
            platform="telegram"
        )
        
        assert response == "Fallback response from chat engine"
        
        # Verify chat engine was called directly
        enhanced_ai_engine.chat_engine.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_conversation_context_enhancement(self, enhanced_ai_engine):
        """Test that conversation context includes enhanced metadata"""
        await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="Test message",
            platform="telegram",
            context={"additional": "data"}
        )
        
        # Check that conversation flow was called with enhanced context
        call_args = enhanced_ai_engine.conversation_flow.process_conversation.call_args
        assert call_args is not None
        
        conversation_context = call_args[1]["conversation_context"]
        assert "platform" in conversation_context
        assert "user_profile" in conversation_context
        assert "enhanced_context" in conversation_context
    
    @pytest.mark.asyncio
    async def test_conversation_context_management(self, enhanced_ai_engine):
        """Test conversation context tracking and updates"""
        user_id = "test_user"
        platform = "telegram"
        
        # Process multiple messages
        for i in range(3):
            await enhanced_ai_engine.process_message(
                user_id=user_id,
                message=f"Message {i}",
                platform=platform
            )
        
        # Verify conversation context exists and is tracked
        conversation_id = f"{platform}_{user_id}"
        assert conversation_id in enhanced_ai_engine.active_conversations
        
        ctx = enhanced_ai_engine.active_conversations[conversation_id]
        assert ctx.user_id == user_id
        assert ctx.platform == platform
        assert ctx.message_count == 3
    
    @pytest.mark.asyncio
    async def test_persona_handling(self, enhanced_ai_engine):
        """Test persona handling in enhanced flow"""
        await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="Switch to rose persona",
            platform="telegram",
            persona="rose"
        )
        
        # Verify persona was passed to conversation flow
        call_args = enhanced_ai_engine.conversation_flow.process_conversation.call_args
        assert call_args[1]["persona"] == "rose"
    
    @pytest.mark.asyncio
    async def test_enhanced_error_handling(self, enhanced_ai_engine):
        """Test comprehensive error handling"""
        # Make multiple components fail
        enhanced_ai_engine.user_profile_manager.process_conversation.side_effect = Exception("Profile error")
        enhanced_ai_engine.conversation_flow.process_conversation.side_effect = Exception("Flow error")
        enhanced_ai_engine.chat_engine.process_message.side_effect = Exception("Chat error")
        
        response = await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="Test message",
            platform="telegram"
        )
        
        # Should return error message instead of crashing
        assert "error" in response.lower() or "apologize" in response.lower()
    
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, enhanced_ai_engine):
        """Test that performance metrics are tracked"""
        initial_count = enhanced_ai_engine.total_messages_processed
        
        await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="Test message",
            platform="telegram"
        )
        
        assert enhanced_ai_engine.total_messages_processed == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_context_data_persistence(self, enhanced_ai_engine):
        """Test that context data is properly stored and updated"""
        user_id = "test_user"
        platform = "telegram"
        
        await enhanced_ai_engine.process_message(
            user_id=user_id,
            message="Test message",
            platform=platform
        )
        
        conversation_id = f"{platform}_{user_id}"
        ctx = enhanced_ai_engine.active_conversations[conversation_id]
        
        # Check that processing metadata was stored
        assert ctx.context_data is not None
        assert "processing_method" in ctx.context_data
        assert ctx.context_data["processing_method"] in [
            "langgraph_flow", "chat_engine_fallback", "chat_engine_standard"
        ]
    
    @pytest.mark.asyncio
    async def test_multiple_user_isolation(self, enhanced_ai_engine):
        """Test that different users have isolated contexts"""
        users = ["user1", "user2", "user3"]
        
        # Process messages for multiple users
        for user_id in users:
            await enhanced_ai_engine.process_message(
                user_id=user_id,
                message=f"Hello from {user_id}",
                platform="telegram"
            )
        
        # Verify separate conversation contexts
        for user_id in users:
            conversation_id = f"telegram_{user_id}"
            assert conversation_id in enhanced_ai_engine.active_conversations
            ctx = enhanced_ai_engine.active_conversations[conversation_id]
            assert ctx.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_integration_flow_metadata(self, enhanced_ai_engine):
        """Test that flow metadata is properly integrated"""
        # Mock conversation flow to return specific metadata
        flow_metadata = {
            "intent": "knowledge_query",
            "flow_state": "completed",
            "entities": {"topic": "AI"},
            "persona_used": "choy"
        }
        
        enhanced_ai_engine.conversation_flow.process_conversation.return_value = (
            "Knowledge response", flow_metadata
        )
        
        await enhanced_ai_engine.process_message(
            user_id="test_user",
            message="What is AI?",
            platform="telegram"
        )
        
        # Verify metadata was stored in conversation context
        conversation_id = "telegram_test_user"
        ctx = enhanced_ai_engine.active_conversations[conversation_id]
        
        assert "flow_metadata" in ctx.context_data
        assert ctx.context_data["flow_metadata"]["intent"] == "knowledge_query"
