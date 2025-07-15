"""
Unit tests for Core Memory Manager
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.modules.memory.core_memory import CoreMemoryManager


@pytest.mark.unit
@pytest.mark.memory
class TestCoreMemoryManager:
    """Test cases for CoreMemoryManager"""

    async def test_initialization(self, core_memory):
        """Test core memory manager initialization"""
        assert core_memory.connection is not None
        assert core_memory.db_path.exists()

    async def test_save_and_get_core_fact(self, core_memory):
        """Test saving and retrieving core facts"""
        # Save a core fact
        success = await core_memory.save_core_fact(
            category="test",
            key="test_key",
            value="test_value",
            description="Test description"
        )
        assert success is True

        # Retrieve the core fact
        fact = await core_memory.get_core_fact("test", "test_key")
        assert fact is not None
        assert fact["value"] == "test_value"
        assert fact["description"] == "Test description"

    async def test_add_knowledge(self, core_memory):
        """Test adding knowledge to the knowledge base"""
        success = await core_memory.add_knowledge(
            topic="test_topic",
            content="Test knowledge content",
            tags=["test", "knowledge"],
            importance=3
        )
        assert success is True

        # Verify knowledge was saved
        knowledge = await core_memory.search_knowledge("test_topic")
        assert len(knowledge) > 0
        assert knowledge[0]["content"] == "Test knowledge content"

    async def test_search_knowledge(self, core_memory):
        """Test knowledge search functionality"""
        # Add some test knowledge
        await core_memory.add_knowledge(
            topic="python_programming",
            content="Python is a high-level programming language",
            tags=["python", "programming"],
            importance=4
        )

        await core_memory.add_knowledge(
            topic="machine_learning",
            content="Machine learning is a subset of AI",
            tags=["ml", "ai"],
            importance=5
        )

        # Search for knowledge
        results = await core_memory.search_knowledge("programming")
        assert len(results) >= 1
        assert any("Python" in r["content"] for r in results)

    async def test_get_system_capabilities(self, core_memory):
        """Test retrieving system capabilities"""
        capabilities = await core_memory.get_system_capabilities()
        # Should have loaded initial capabilities
        assert len(capabilities) > 0
        assert any("memory" in cap.lower() for cap in capabilities)

    async def test_core_fact_confidence(self, core_memory):
        """Test core fact confidence levels"""
        # Save fact with custom confidence
        await core_memory.save_core_fact(
            category="test",
            key="confidence_test",
            value="high confidence fact",
            confidence=0.95
        )

        fact = await core_memory.get_core_fact("test", "confidence_test")
        assert fact["confidence"] == 0.95

    async def test_knowledge_importance_ordering(self, core_memory):
        """Test that knowledge is ordered by importance"""
        # Add knowledge with different importance levels
        await core_memory.add_knowledge(
            topic="low_importance",
            content="Low importance content",
            importance=1
        )

        await core_memory.add_knowledge(
            topic="high_importance",
            content="High importance content",
            importance=5
        )

        # Search should return higher importance first
        results = await core_memory.search_knowledge("importance")
        assert len(results) >= 2
        assert results[0]["importance"] >= results[1]["importance"]

    async def test_universal_ethics_framework(self, core_memory):
        """Test that universal ethics framework is loaded"""
        ethics = await core_memory.search_knowledge("ethics")
        assert len(ethics) > 0
        assert any("privacy" in e["content"].lower() for e in ethics)
        assert any("confidentiality" in e["content"].lower() for e in ethics)
