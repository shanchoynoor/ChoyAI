"""
Tests for RAG Engine
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.rag_engine import RAGEngine


class TestRAGEngine:
    """Test RAG engine functionality"""
    
    @pytest.fixture
    async def rag_engine(self):
        """Create RAG engine for testing"""
        rag = RAGEngine()
        
        # Mock the memory managers to avoid database dependencies
        rag.vector_memory = AsyncMock()
        rag.core_memory = AsyncMock() 
        rag.user_memory = AsyncMock()
        
        # Mock initialization
        rag.vector_memory.initialize.return_value = True
        rag.core_memory.initialize.return_value = True
        rag.user_memory.initialize.return_value = True
        
        await rag.initialize()
        return rag
    
    @pytest.mark.asyncio
    async def test_initialization(self, rag_engine):
        """Test RAG engine initialization"""
        assert rag_engine.vector_memory is not None
        assert rag_engine.core_memory is not None
        assert rag_engine.user_memory is not None
    
    @pytest.mark.asyncio
    async def test_index_conversation(self, rag_engine):
        """Test indexing a conversation"""
        rag_engine.vector_memory.add_memory.return_value = "memory_id_123"
        
        success = await rag_engine.index_conversation(
            user_id="test_user",
            conversation_text="This is a test conversation about machine learning and AI",
            metadata={"session": "test"}
        )
        
        assert success == True
        rag_engine.vector_memory.add_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_index_knowledge_document(self, rag_engine):
        """Test indexing a knowledge document"""
        rag_engine.vector_memory.add_memory.return_value = "doc_memory_123"
        
        success = await rag_engine.index_knowledge_document(
            content="Python is a high-level programming language known for its simplicity",
            doc_id="python_intro",
            title="Introduction to Python",
            source="documentation"
        )
        
        assert success == True
        rag_engine.vector_memory.add_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_retrieve_context(self, rag_engine):
        """Test context retrieval"""
        # Mock vector memory responses
        rag_engine.vector_memory.search_memories.return_value = [
            {
                "content": "Previous conversation about Python",
                "similarity": 0.8,
                "metadata": {"type": "conversation"}
            }
        ]
        
        # Mock core memory response
        rag_engine.core_memory.get_core_facts.return_value = {
            "programming": [
                {"content": "Python is versatile", "confidence": 0.9}
            ]
        }
        
        # Mock user memory response
        rag_engine.user_memory.get_user_memories.return_value = [
            {"content": "User likes Python programming", "key": "preference"}
        ]
        
        context = await rag_engine.retrieve_context(
            query="Tell me about Python programming",
            user_id="test_user",
            max_context_length=1000
        )
        
        assert "query" in context
        assert "user_id" in context
        assert "contexts" in context
        assert context["user_id"] == "test_user"
    
    @pytest.mark.asyncio
    async def test_enhance_prompt_with_context(self, rag_engine):
        """Test prompt enhancement with RAG context"""
        # Mock retrieve_context
        mock_context = {
            "query": "test query",
            "user_id": "test_user",
            "contexts": {
                "core_facts": "Python is a programming language",
                "user_memory": "User prefers Python",
                "conversation": "Previous Python discussion",
                "knowledge": "Python documentation"
            }
        }
        
        rag_engine.retrieve_context = AsyncMock(return_value=mock_context)
        
        enhanced_prompt, metadata = await rag_engine.enhance_prompt_with_context(
            original_prompt="How do I learn Python?",
            user_id="test_user"
        )
        
        assert isinstance(enhanced_prompt, str)
        assert "How do I learn Python?" in enhanced_prompt
        assert isinstance(metadata, dict)
        assert len(enhanced_prompt) > len("How do I learn Python?")
    
    @pytest.mark.asyncio
    async def test_text_splitting(self, rag_engine):
        """Test text splitting functionality"""
        long_text = "This is a very long text. " * 100  # 500+ words
        chunks = rag_engine._split_text(long_text)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1  # Should be split into multiple chunks
        
        # Each chunk should be reasonable size
        for chunk in chunks:
            assert len(chunk) > 0
            assert len(chunk.split()) <= 250  # Reasonable chunk size
    
    @pytest.mark.asyncio
    async def test_context_formatting(self, rag_engine):
        """Test context formatting"""
        contexts = [
            {"content": "First context", "similarity": 0.9},
            {"content": "Second context", "similarity": 0.7},
            {"content": "Third context", "similarity": 0.5}
        ]
        
        formatted = rag_engine._format_contexts(contexts, max_length=100)
        
        assert isinstance(formatted, str)
        assert "Relevance:" in formatted
        assert len(formatted) <= 100
    
    @pytest.mark.asyncio
    async def test_rag_stats(self, rag_engine):
        """Test getting RAG statistics"""
        rag_engine.vector_memory.get_collection_stats.return_value = {
            "available": True,
            "total_memories": 42
        }
        
        stats = await rag_engine.get_rag_stats()
        
        assert "vector_memory" in stats
        assert "rag_available" in stats
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, rag_engine):
        """Test error handling in RAG operations"""
        # Make vector memory raise an exception
        rag_engine.vector_memory.add_memory.side_effect = Exception("Test error")
        
        success = await rag_engine.index_conversation(
            user_id="test_user",
            conversation_text="Test conversation",
            metadata={}
        )
        
        assert success == False
        
        # Test error in context retrieval
        rag_engine.vector_memory.search_memories.side_effect = Exception("Search error")
        
        context = await rag_engine.retrieve_context(
            query="test query",
            user_id="test_user"
        )
        
        assert "error" in context
    
    @pytest.mark.asyncio
    async def test_context_type_filtering(self, rag_engine):
        """Test filtering by context types"""
        rag_engine.vector_memory.search_memories.return_value = []
        rag_engine.core_memory.get_core_facts.return_value = {}
        rag_engine.user_memory.get_user_memories.return_value = []
        
        # Test with specific context types
        context = await rag_engine.retrieve_context(
            query="test query",
            user_id="test_user",
            context_types=["conversation_rag", "knowledge"]
        )
        
        assert isinstance(context, dict)
        assert "contexts" in context
        
        # Should only call vector memory search, not user/core memory
        rag_engine.vector_memory.search_memories.assert_called()
    
    @pytest.mark.asyncio
    async def test_context_length_limiting(self, rag_engine):
        """Test context length limiting"""
        # Mock large context responses
        large_content = "A" * 1000  # 1000 character content
        rag_engine.vector_memory.search_memories.return_value = [
            {"content": large_content, "similarity": 0.9},
            {"content": large_content, "similarity": 0.8}
        ]
        
        context = await rag_engine.retrieve_context(
            query="test query", 
            user_id="test_user",
            max_context_length=500  # Limit to 500 chars
        )
        
        # Total context should respect the limit
        total_context_length = sum(
            len(str(ctx)) for ctx in context.get("contexts", {}).values()
        )
        assert total_context_length <= 600  # Some overhead allowed
