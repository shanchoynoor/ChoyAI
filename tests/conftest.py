"""
Test configuration and fixtures for ChoyAI
"""

import pytest
import asyncio
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from typing import AsyncGenerator, Generator

# Add the app directory to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from app.config.settings import Settings
from app.core.ai_engine import ChoyAIEngine
from app.modules.memory.core_memory import CoreMemoryManager
from app.modules.memory.user_memory import UserMemoryManager
from app.modules.memory.conversation_memory import ConversationMemoryManager
from app.modules.personas.persona_manager import PersonaManager
from app.core.ai_providers.provider_manager import AIProviderManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    return Settings(
        data_dir=temp_dir / "data",
        logs_dir=temp_dir / "logs",
        personas_dir=Path(__file__).parent.parent / "templates" / "personas",
        log_level="DEBUG",
        environment="test",
        debug=True
    )


@pytest.fixture
async def core_memory(test_settings: Settings) -> AsyncGenerator[CoreMemoryManager, None]:
    """Create a test core memory manager."""
    manager = CoreMemoryManager()
    # Override settings for test
    manager.db_path = test_settings.data_dir / "test_core_memory.db"
    await manager.initialize()
    yield manager
    # Cleanup
    if manager.connection:
        manager.connection.close()


@pytest.fixture
async def user_memory(test_settings: Settings) -> AsyncGenerator[UserMemoryManager, None]:
    """Create a test user memory manager."""
    manager = UserMemoryManager()
    # Override settings for test
    manager.db_path = test_settings.data_dir / "test_user_memory.db"
    await manager.initialize()
    yield manager
    # Cleanup
    if manager.connection:
        manager.connection.close()


@pytest.fixture
async def conversation_memory(test_settings: Settings) -> AsyncGenerator[ConversationMemoryManager, None]:
    """Create a test conversation memory manager."""
    manager = ConversationMemoryManager()
    # Override settings for test
    manager.db_path = test_settings.data_dir / "test_conversations.db"
    await manager.initialize()
    yield manager
    # Cleanup
    if manager.connection:
        manager.connection.close()


@pytest.fixture
async def persona_manager(test_settings: Settings) -> AsyncGenerator[PersonaManager, None]:
    """Create a test persona manager."""
    manager = PersonaManager()
    await manager.initialize()
    yield manager


@pytest.fixture
def mock_ai_provider():
    """Create a mock AI provider."""
    provider = Mock()
    provider.name = "test_provider"
    provider.is_available = True
    provider.supported_tasks = ["conversation", "technical"]
    
    async def mock_chat_completion(*args, **kwargs):
        from app.core.ai_providers.base_provider import AIResponse
        return AIResponse(
            content="Test response",
            provider="test_provider",
            model="test_model",
            usage={"total_tokens": 10}
        )
    
    provider.chat_completion = AsyncMock(side_effect=mock_chat_completion)
    provider.health_check = AsyncMock(return_value=True)
    provider.initialize = AsyncMock(return_value=True)
    provider.close = AsyncMock()
    
    return provider


@pytest.fixture
async def ai_provider_manager(mock_ai_provider) -> AsyncGenerator[AIProviderManager, None]:
    """Create a test AI provider manager."""
    manager = AIProviderManager()
    # Override with mock provider
    manager.providers = {"test_provider": mock_ai_provider}
    yield manager


@pytest.fixture
async def ai_engine(
    core_memory: CoreMemoryManager,
    user_memory: UserMemoryManager,
    conversation_memory: ConversationMemoryManager,
    persona_manager: PersonaManager,
    ai_provider_manager: AIProviderManager
) -> AsyncGenerator[ChoyAIEngine, None]:
    """Create a test AI engine with all dependencies."""
    engine = ChoyAIEngine()
    
    # Override with test components
    engine.core_memory = core_memory
    engine.user_memory = user_memory
    engine.conversation_memory = conversation_memory
    engine.persona_manager = persona_manager
    engine.ai_provider_manager = ai_provider_manager
    
    yield engine


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "test_user_123",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "bio": "Test user biography"
    }


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "user_id": "test_user_123",
        "platform": "telegram",
        "persona": "choy",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"}
        ]
    }


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing."""
    return [
        {
            "key": "favorite_color",
            "value": "blue",
            "context": "User mentioned they love blue",
            "category": "preferences",
            "importance": 3
        },
        {
            "key": "occupation",
            "value": "software engineer",
            "context": "Professional background",
            "category": "personal",
            "importance": 4
        }
    ]
