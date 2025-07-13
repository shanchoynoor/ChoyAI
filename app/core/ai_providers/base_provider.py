"""
Base AI Provider Interface

Defines the common interface that all AI providers must implement.
This ensures consistent behavior across different AI services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging


class TaskType(Enum):
    """Task types for AI provider selection"""
    CONVERSATION = "conversation"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    PROBLEM_SOLVING = "problem_solving"
    EMOTIONAL_SUPPORT = "emotional_support"
    RESEARCH = "research"


@dataclass
class AIMessage:
    """Standardized AI message format"""
    role: str  # system, user, assistant
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    provider: str
    model: str
    usage: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseAIProvider(ABC):
    """Base class for all AI providers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.is_available = False
        self.supported_tasks = []
        self.models = {}
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider and check availability"""
        pass
        
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[AIMessage],
        task_type: TaskType = TaskType.CONVERSATION,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion"""
        pass
        
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and available"""
        pass
        
    def supports_task(self, task_type: TaskType) -> bool:
        """Check if provider supports a specific task type"""
        return task_type in self.supported_tasks
        
    def get_best_model_for_task(self, task_type: TaskType) -> Optional[str]:
        """Get the best model for a specific task type"""
        task_models = self.models.get(task_type.value, {})
        if not task_models:
            # Return default model if no task-specific model
            return self.models.get('default')
        return task_models.get('primary') or task_models.get('fallback')
        
    async def close(self):
        """Cleanup resources"""
        pass
