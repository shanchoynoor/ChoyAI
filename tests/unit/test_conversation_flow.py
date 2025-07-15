"""
Tests for Conversation Flow Manager
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.conversation_flow import ConversationFlowManager, ConversationState


class TestConversationFlowManager:
    """Test conversation flow management functionality"""
    
    @pytest.fixture
    async def flow_manager(self):
        """Create conversation flow manager for testing"""
        # Mock AI engine and RAG engine
        mock_ai_engine = AsyncMock()
        mock_rag_engine = AsyncMock()
        
        flow = ConversationFlowManager(
            ai_engine=mock_ai_engine,
            rag_engine=mock_rag_engine
        )
        
        await flow.initialize()
        return flow
    
    @pytest.mark.asyncio
    async def test_initialization(self, flow_manager):
        """Test flow manager initialization"""
        assert flow_manager.ai_engine is not None
        assert flow_manager.rag_engine is not None
        assert flow_manager.intent_patterns is not None
        assert len(flow_manager.intent_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_process_conversation_fallback(self, flow_manager):
        """Test conversation processing with fallback mode"""
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Hello there!",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert isinstance(response, str)
        assert isinstance(metadata, dict)
        assert "intent" in metadata
        assert "flow_state" in metadata
        assert metadata["intent"] == "greeting"
    
    def test_intent_classification(self, flow_manager):
        """Test intent classification patterns"""
        # Test greeting
        assert flow_manager._classify_intent_simple("hello there") == "greeting"
        assert flow_manager._classify_intent_simple("good morning") == "greeting"
        
        # Test task assistance
        assert flow_manager._classify_intent_simple("can you help me") == "task_assistance"
        assert flow_manager._classify_intent_simple("I need help with") == "task_assistance"
        
        # Test problem solving
        assert flow_manager._classify_intent_simple("I have a problem") == "problem_solving"
        assert flow_manager._classify_intent_simple("there's an error") == "problem_solving"
        
        # Test persona switching
        assert flow_manager._classify_intent_simple("switch to choy") == "persona_switching"
        assert flow_manager._classify_intent_simple("change persona") == "persona_switching"
        
        # Test memory recall
        assert flow_manager._classify_intent_simple("do you remember") == "memory_recall"
        assert flow_manager._classify_intent_simple("what did we talk about") == "memory_recall"
        
        # Test knowledge query
        assert flow_manager._classify_intent_simple("what is Python") == "knowledge_query"
        assert flow_manager._classify_intent_simple("explain machine learning") == "knowledge_query"
        
        # Test emotional support
        assert flow_manager._classify_intent_simple("I'm feeling sad") == "emotional_support"
        assert flow_manager._classify_intent_simple("need support") == "emotional_support"
        
        # Test general chat fallback
        assert flow_manager._classify_intent_simple("random text here") == "general_chat"
    
    @pytest.mark.asyncio
    async def test_greeting_handler(self, flow_manager):
        """Test greeting message handling"""
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Good morning!",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert "morning" in response.lower() or "hello" in response.lower()
        assert metadata["intent"] == "greeting"
    
    @pytest.mark.asyncio
    async def test_task_assistance_handler(self, flow_manager):
        """Test task assistance handling"""
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Can you help me with programming?",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert "help" in response.lower()
        assert metadata["intent"] == "task_assistance"
    
    @pytest.mark.asyncio
    async def test_knowledge_query_handler(self, flow_manager):
        """Test knowledge query handling"""
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="What is artificial intelligence?",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert len(response) > 0
        assert metadata["intent"] == "knowledge_query"
    
    @pytest.mark.asyncio
    async def test_persona_switching(self, flow_manager):
        """Test persona switching functionality"""
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Switch to rose persona",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert isinstance(response, str)
        assert metadata["intent"] == "persona_switching"
    
    @pytest.mark.asyncio
    async def test_memory_recall_with_rag(self, flow_manager):
        """Test memory recall with RAG engine"""
        # Mock RAG engine response
        flow_manager.rag_engine.retrieve_context.return_value = {
            "contexts": {
                "conversation_rag": "Previous conversation about Python",
                "user_memory": "User likes programming"
            }
        }
        
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Do you remember what we talked about?",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert isinstance(response, str)
        assert metadata["intent"] == "memory_recall"
    
    @pytest.mark.asyncio
    async def test_emotional_support_handler(self, flow_manager):
        """Test emotional support handling"""
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="I'm feeling really frustrated today",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert len(response) > 0
        assert metadata["intent"] == "emotional_support"
    
    @pytest.mark.asyncio
    async def test_general_chat_fallback(self, flow_manager):
        """Test general chat fallback"""
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Random conversation text",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert isinstance(response, str)
        assert metadata["intent"] == "general_chat"
    
    @pytest.mark.asyncio
    async def test_flow_stats(self, flow_manager):
        """Test getting flow statistics"""
        stats = await flow_manager.get_flow_stats()
        
        assert isinstance(stats, dict)
        assert "langgraph_available" in stats
        assert "supported_intents" in stats
        assert "ai_engine_connected" in stats
        assert "rag_engine_connected" in stats
        
        assert isinstance(stats["supported_intents"], list)
        assert len(stats["supported_intents"]) > 0
    
    @pytest.mark.asyncio
    async def test_context_enhancement(self, flow_manager):
        """Test conversation context enhancement"""
        enhanced_context = {
            "user_profile": {"name": "Test User"},
            "session_data": {"session_id": "test_123"}
        }
        
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Hello",
            conversation_context=enhanced_context,
            persona="choy"
        )
        
        assert isinstance(response, str)
        assert isinstance(metadata, dict)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, flow_manager):
        """Test error handling in conversation flow"""
        # Mock RAG engine to raise an exception
        flow_manager.rag_engine.retrieve_context.side_effect = Exception("RAG error")
        
        # Should still work with fallback
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Remember our conversation?",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        assert isinstance(response, str)
        assert metadata["intent"] == "memory_recall"
    
    @pytest.mark.asyncio
    async def test_multiple_intent_messages(self, flow_manager):
        """Test messages with multiple possible intents"""
        # Message that could be greeting + task assistance
        response, metadata = await flow_manager.process_conversation(
            user_id="test_user",
            message="Hello! Can you help me with something?",
            conversation_context={"platform": "test"},
            persona="choy"
        )
        
        # Should pick the first matching intent (greeting)
        assert metadata["intent"] in ["greeting", "task_assistance"]
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_conversation_state_transitions(self, flow_manager):
        """Test conversation state management"""
        # Simulate a conversation flow
        messages = [
            ("Hello there!", "greeting"),
            ("Can you help me learn Python?", "task_assistance"), 
            ("What is machine learning?", "knowledge_query"),
            ("Thanks for the help!", "general_chat")
        ]
        
        for message, expected_intent in messages:
            response, metadata = await flow_manager.process_conversation(
                user_id="test_user",
                message=message,
                conversation_context={"platform": "test"},
                persona="choy"
            )
            
            assert isinstance(response, str)
            assert metadata["intent"] == expected_intent
            assert metadata["flow_state"] == "completed"
    
    def test_fallback_response_generation(self, flow_manager):
        """Test fallback response generation"""
        from app.modules.conversation_flow import GraphState
        
        mock_state = {
            "user_intent": "greeting",
            "current_persona": "choy"
        }
        
        response = flow_manager._generate_fallback_response(mock_state)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "choy" in response.lower() or "hello" in response.lower()
