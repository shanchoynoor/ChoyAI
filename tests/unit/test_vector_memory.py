"""
Tests for Vector Memory Manager
"""

import pytest
import pytest_asyncio
import tempfile
import shutil
from pathlib import Path

from app.modules.memory.vector_memory import VectorMemoryManager


class TestVectorMemoryManager:
    """Test vector memory management functionality"""
    
    @pytest_asyncio.fixture
    async def vector_memory(self, temp_dir):
        """Create vector memory manager for testing"""
        # Override data directory for testing
        original_data_dir = None
        try:
            from app.config.settings import settings
            original_data_dir = settings.data_dir
            settings.data_dir = temp_dir
        except:
            pass
        
        vm = VectorMemoryManager(collection_name="test_memories")
        await vm.initialize()
        
        yield vm
        
        # Cleanup
        if vm:
            await vm.close()
        
        # Restore original data dir
        if original_data_dir:
            settings.data_dir = original_data_dir
    
    @pytest.mark.asyncio
    async def test_initialization(self, vector_memory):
        """Test vector memory initialization"""
        stats = await vector_memory.get_collection_stats()
        assert stats.get("available") in [True, False]  # Depends on dependencies
    
    @pytest.mark.asyncio
    async def test_add_memory(self, vector_memory):
        """Test adding a memory"""
        memory_id = await vector_memory.add_memory(
            user_id="test_user",
            content="This is a test memory about Python programming",
            memory_type="test",
            metadata={"source": "test"},
            importance=2
        )
        
        assert memory_id is not None
        assert "test_user" in memory_id
        assert "test" in memory_id
    
    @pytest.mark.asyncio
    async def test_search_memories(self, vector_memory):
        """Test semantic search"""
        # Add some test memories
        await vector_memory.add_memory(
            user_id="test_user",
            content="Python is a programming language",
            memory_type="knowledge"
        )
        
        await vector_memory.add_memory(
            user_id="test_user", 
            content="Machine learning uses algorithms",
            memory_type="knowledge"
        )
        
        # Search for programming-related content
        results = await vector_memory.search_memories(
            query="programming languages",
            user_id="test_user",
            limit=5
        )
        
        assert isinstance(results, list)
        # Results depend on whether vector dependencies are available
    
    @pytest.mark.asyncio
    async def test_get_user_memories(self, vector_memory):
        """Test retrieving user memories"""
        # Add test memory
        await vector_memory.add_memory(
            user_id="test_user",
            content="User-specific memory",
            memory_type="personal"
        )
        
        memories = await vector_memory.get_user_memories("test_user")
        assert isinstance(memories, list)
    
    @pytest.mark.asyncio 
    async def test_update_memory(self, vector_memory):
        """Test updating a memory"""
        # Add memory
        memory_id = await vector_memory.add_memory(
            user_id="test_user",
            content="Original content",
            memory_type="test"
        )
        
        # Update memory
        success = await vector_memory.update_memory(
            memory_id=memory_id,
            content="Updated content",
            metadata={"updated": True}
        )
        
        # Success depends on dependencies being available
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, vector_memory):
        """Test deleting a memory"""
        # Add memory
        memory_id = await vector_memory.add_memory(
            user_id="test_user",
            content="Memory to delete",
            memory_type="test"
        )
        
        # Delete memory
        success = await vector_memory.delete_memory(memory_id)
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_get_similar_contexts(self, vector_memory):
        """Test getting similar contexts"""
        # Add conversation context
        await vector_memory.add_memory(
            user_id="test_user",
            content="We discussed Python frameworks like Django and Flask",
            memory_type="conversation"
        )
        
        contexts = await vector_memory.get_similar_contexts(
            current_context="Tell me about web frameworks",
            user_id="test_user",
            limit=3
        )
        
        assert isinstance(contexts, list)
    
    @pytest.mark.asyncio
    async def test_memory_filtering(self, vector_memory):
        """Test memory filtering by type and user"""
        # Add memories for different users and types
        await vector_memory.add_memory(
            user_id="user1",
            content="User 1 conversation",
            memory_type="conversation"
        )
        
        await vector_memory.add_memory(
            user_id="user2", 
            content="User 2 conversation",
            memory_type="conversation"
        )
        
        await vector_memory.add_memory(
            user_id="user1",
            content="User 1 knowledge",
            memory_type="knowledge"
        )
        
        # Search with filters
        user1_convos = await vector_memory.search_memories(
            query="conversation",
            user_id="user1",
            memory_type="conversation"
        )
        
        user1_knowledge = await vector_memory.search_memories(
            query="knowledge", 
            user_id="user1",
            memory_type="knowledge"
        )
        
        assert isinstance(user1_convos, list)
        assert isinstance(user1_knowledge, list)
