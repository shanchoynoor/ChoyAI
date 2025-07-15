"""
Unit tests for User Memory Manager
"""

import pytest
from app.modules.memory.user_memory import UserMemoryManager


@pytest.mark.unit
@pytest.mark.memory
class TestUserMemoryManager:
    """Test cases for UserMemoryManager"""

    async def test_create_user(self, user_memory, sample_user_data):
        """Test user creation"""
        user = await user_memory.get_or_create_user(
            user_id=sample_user_data["user_id"],
            username=sample_user_data["username"],
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"]
        )
        
        assert user["user_id"] == sample_user_data["user_id"]
        assert user["username"] == sample_user_data["username"]
        assert user["first_name"] == sample_user_data["first_name"]

    async def test_save_and_get_memory(self, user_memory, sample_user_data):
        """Test saving and retrieving user memories"""
        user_id = sample_user_data["user_id"]
        
        # Save a memory
        success = await user_memory.save_memory(
            user_id=user_id,
            key="favorite_color",
            value="blue",
            context="User mentioned preference",
            category="preferences",
            importance=3
        )
        assert success is True

        # Retrieve the memory
        memory = await user_memory.get_memory(user_id, "favorite_color")
        assert memory is not None
        assert memory["value"] == "blue"
        assert memory["category"] == "preferences"
        assert memory["importance"] == 3

    async def test_get_memories_with_filters(self, user_memory, sample_user_data, sample_memory_data):
        """Test retrieving memories with filters"""
        user_id = sample_user_data["user_id"]
        
        # Save multiple memories
        for memory_data in sample_memory_data:
            await user_memory.save_memory(
                user_id=user_id,
                **memory_data
            )

        # Get all memories
        all_memories = await user_memory.get_memories(user_id)
        assert len(all_memories) == len(sample_memory_data)

        # Get memories by category
        preference_memories = await user_memory.get_memories(
            user_id, category="preferences"
        )
        assert len(preference_memories) == 1
        assert preference_memories[0]["key"] == "favorite_color"

        # Get limited memories
        limited_memories = await user_memory.get_memories(user_id, limit=1)
        assert len(limited_memories) == 1
        # Should be ordered by importance (highest first)
        assert limited_memories[0]["importance"] == 4

    async def test_search_memories(self, user_memory, sample_user_data, sample_memory_data):
        """Test memory search functionality"""
        user_id = sample_user_data["user_id"]
        
        # Save memories
        for memory_data in sample_memory_data:
            await user_memory.save_memory(user_id=user_id, **memory_data)

        # Search for memories
        results = await user_memory.search_memories(user_id, "engineer")
        assert len(results) == 1
        assert results[0]["key"] == "occupation"

        # Search by context
        results = await user_memory.search_memories(user_id, "love")
        assert len(results) == 1
        assert results[0]["key"] == "favorite_color"

    async def test_delete_memory(self, user_memory, sample_user_data):
        """Test memory deletion"""
        user_id = sample_user_data["user_id"]
        
        # Save a memory
        await user_memory.save_memory(
            user_id=user_id,
            key="temp_memory",
            value="temporary value"
        )

        # Verify it exists
        memory = await user_memory.get_memory(user_id, "temp_memory")
        assert memory is not None

        # Delete it
        success = await user_memory.delete_memory(user_id, "temp_memory")
        assert success is True

        # Verify it's gone
        memory = await user_memory.get_memory(user_id, "temp_memory")
        assert memory is None

    async def test_user_preferences(self, user_memory, sample_user_data):
        """Test user preferences functionality"""
        user_id = sample_user_data["user_id"]
        
        # Set a preference
        success = await user_memory.update_user_preference(
            user_id, "theme", "dark"
        )
        assert success is True

        # Get the preference
        theme = await user_memory.get_user_preference(user_id, "theme")
        assert theme == "dark"

        # Update the preference
        await user_memory.update_user_preference(user_id, "theme", "light")
        theme = await user_memory.get_user_preference(user_id, "theme")
        assert theme == "light"

    async def test_user_stats(self, user_memory, sample_user_data, sample_memory_data):
        """Test user statistics functionality"""
        user_id = sample_user_data["user_id"]
        
        # Create user
        await user_memory.get_or_create_user(user_id=user_id)
        
        # Add memories and preferences
        for memory_data in sample_memory_data:
            await user_memory.save_memory(user_id=user_id, **memory_data)
        
        await user_memory.update_user_preference(user_id, "language", "en")
        
        # Get stats
        stats = await user_memory.get_user_stats(user_id)
        
        assert stats["memory_count"] == len(sample_memory_data)
        assert stats["preferences_count"] == 1
        assert "category_counts" in stats
        assert stats["category_counts"]["preferences"] == 1
        assert stats["category_counts"]["personal"] == 1
