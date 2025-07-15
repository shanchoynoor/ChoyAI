"""
Unit tests for Persona Manager
"""

import pytest
from app.modules.personas.persona_manager import PersonaManager


@pytest.mark.unit
@pytest.mark.persona
class TestPersonaManager:
    """Test cases for PersonaManager"""

    async def test_initialization(self, persona_manager):
        """Test persona manager initialization"""
        assert len(persona_manager.personas) > 0
        assert persona_manager.default_persona in persona_manager.personas

    async def test_get_persona(self, persona_manager):
        """Test getting a specific persona"""
        choy = await persona_manager.get_persona("choy")
        assert choy is not None
        assert choy.name == "choy"
        assert choy.display_name == "Choy"

    async def test_list_persona_names(self, persona_manager):
        """Test listing all persona names"""
        names = await persona_manager.list_persona_names()
        assert "choy" in names
        assert len(names) >= 1

    async def test_get_persona_info(self, persona_manager):
        """Test getting persona information"""
        info = await persona_manager.get_persona_info("choy")
        assert info is not None
        assert "name" in info
        assert "display_name" in info
        assert "style" in info

    async def test_invalid_persona(self, persona_manager):
        """Test handling of invalid persona names"""
        invalid_persona = await persona_manager.get_persona("nonexistent")
        assert invalid_persona is None

    async def test_default_persona_fallback(self, persona_manager):
        """Test fallback to default persona"""
        # This should return the default persona when given invalid name
        default = await persona_manager.get_persona("invalid_name")
        assert default is None  # Should return None for invalid names

        # But we should always be able to get the default
        default = await persona_manager.get_persona(persona_manager.default_persona)
        assert default is not None

    async def test_persona_attributes(self, persona_manager):
        """Test that personas have required attributes"""
        choy = await persona_manager.get_persona("choy")
        assert hasattr(choy, 'name')
        assert hasattr(choy, 'display_name')
        assert hasattr(choy, 'style')
        assert hasattr(choy, 'personality')
        assert hasattr(choy, 'purpose')

    async def test_reload_personas(self, persona_manager):
        """Test persona reloading functionality"""
        initial_count = len(persona_manager.personas)
        success = await persona_manager.reload_personas()
        assert success is True
        # Count should be the same after reload
        assert len(persona_manager.personas) == initial_count
