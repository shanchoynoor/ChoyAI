"""
Integration tests for ChoyAI Engine
"""

import pytest
from app.core.ai_engine import ChoyAIEngine


@pytest.mark.integration
class TestChoyAIEngineIntegration:
    """Integration tests for the main AI engine"""

    async def test_process_message_flow(self, ai_engine, sample_user_data):
        """Test the complete message processing flow"""
        user_id = sample_user_data["user_id"]
        message = "Hello, my name is John and I'm a software engineer"
        
        # Process the message
        response = await ai_engine.process_message(
            user_id=user_id,
            message=message,
            platform="telegram",
            persona="choy"
        )
        
        assert response is not None
        assert len(response) > 0
        assert "Test response" in response  # From our mock

        # Verify user was created
        user = await ai_engine.user_memory.get_or_create_user(user_id=user_id)
        assert user["user_id"] == user_id

    async def test_memory_integration(self, ai_engine, sample_user_data):
        """Test memory integration across the system"""
        user_id = sample_user_data["user_id"]
        
        # Save a memory
        success = await ai_engine.save_user_memory(
            user_id=user_id,
            key="favorite_language",
            value="Python",
            context="User mentioned preference"
        )
        assert success is True

        # Retrieve memories
        memories = await ai_engine.get_user_memories(user_id)
        assert len(memories) >= 1
        assert any(m["key"] == "favorite_language" for m in memories)

    async def test_persona_switching(self, ai_engine, sample_user_data):
        """Test persona switching functionality"""
        user_id = sample_user_data["user_id"]
        
        # Switch to different persona
        result = await ai_engine.switch_persona(
            user_id=user_id,
            persona_name="choy",
            platform="telegram"
        )
        
        assert result["success"] is True
        assert result["persona"] == "choy"

    async def test_conversation_flow(self, ai_engine, sample_user_data):
        """Test conversation flow and memory"""
        user_id = sample_user_data["user_id"]
        
        # Send multiple messages
        messages = [
            "Hi, I'm new here",
            "I work as a data scientist",
            "My favorite color is green"
        ]
        
        responses = []
        for message in messages:
            response = await ai_engine.process_message(
                user_id=user_id,
                message=message,
                platform="telegram"
            )
            responses.append(response)
        
        assert len(responses) == len(messages)
        
        # Check that conversation was logged
        conversation_history = await ai_engine.conversation_memory.get_conversation_history(
            user_id=user_id,
            limit=10
        )
        
        # Should have both user messages and AI responses
        assert len(conversation_history) >= len(messages)

    async def test_error_handling(self, ai_engine):
        """Test error handling in the AI engine"""
        # Test with invalid user_id format
        response = await ai_engine.process_message(
            user_id="",  # Invalid empty user_id
            message="Test message",
            platform="telegram"
        )
        
        # Should handle gracefully
        assert response is not None

    async def test_multi_user_isolation(self, ai_engine):
        """Test that user data is properly isolated"""
        user1_id = "user1_test"
        user2_id = "user2_test"
        
        # Save different memories for each user
        await ai_engine.save_user_memory(
            user_id=user1_id,
            key="name",
            value="Alice"
        )
        
        await ai_engine.save_user_memory(
            user_id=user2_id,
            key="name",
            value="Bob"
        )
        
        # Verify isolation
        user1_memories = await ai_engine.get_user_memories(user1_id)
        user2_memories = await ai_engine.get_user_memories(user2_id)
        
        user1_names = [m["value"] for m in user1_memories if m["key"] == "name"]
        user2_names = [m["value"] for m in user2_memories if m["key"] == "name"]
        
        assert "Alice" in user1_names
        assert "Alice" not in user2_names
        assert "Bob" in user2_names
        assert "Bob" not in user1_names
