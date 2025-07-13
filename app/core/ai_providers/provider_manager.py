"""
AI Provider Manager

Manages multiple AI providers and routes requests to the appropriate provider
based on task type, provider availability, and configuration preferences.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import random

from .base_provider import BaseAIProvider, AIMessage, AIResponse, TaskType
from .deepseek_provider import DeepSeekProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .xai_provider import XAIProvider
from .gemini_provider import GeminiProvider
from app.config.settings import settings


@dataclass
class ProviderPreference:
    """Provider preference configuration"""
    task_type: TaskType
    primary_provider: str
    fallback_providers: List[str]
    model_preferences: Dict[str, str] = None


class AIProviderManager:
    """Manages multiple AI providers and routes requests"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, BaseAIProvider] = {}
        self.provider_preferences: Dict[TaskType, ProviderPreference] = {}
        self.fallback_strategy = "round_robin"  # round_robin, random, performance
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        
    async def initialize(self):
        """Initialize all configured AI providers"""
        self.logger.info("Initializing AI Provider Manager...")
        
        # Initialize providers based on available API keys
        await self._initialize_providers()
        
        # Setup default preferences
        await self._setup_default_preferences()
        
        self.logger.info(f"Initialized {len(self.providers)} AI providers")
        
    async def _initialize_providers(self):
        """Initialize available providers"""
        provider_configs = {
            'deepseek': {
                'api_key': settings.deepseek_api_key.get_secret_value() if settings.deepseek_api_key else None,
                'model': getattr(settings, 'deepseek_model', 'deepseek-chat'),
                'max_tokens': getattr(settings, 'deepseek_max_tokens', 4000),
                'temperature': getattr(settings, 'deepseek_temperature', 0.7),
            },
            'openai': {
                'api_key': getattr(settings, 'openai_api_key', None),
                'model': getattr(settings, 'openai_model', 'gpt-4'),
                'max_tokens': getattr(settings, 'openai_max_tokens', 4000),
                'temperature': getattr(settings, 'openai_temperature', 0.7),
            },
            'anthropic': {
                'api_key': getattr(settings, 'anthropic_api_key', None),
                'model': getattr(settings, 'anthropic_model', 'claude-3-sonnet-20240229'),
                'max_tokens': getattr(settings, 'anthropic_max_tokens', 4000),
                'temperature': getattr(settings, 'anthropic_temperature', 0.7),
            },
            'xai': {
                'api_key': getattr(settings, 'xai_api_key', None),
                'model': getattr(settings, 'xai_model', 'grok-beta'),
                'max_tokens': getattr(settings, 'xai_max_tokens', 4000),
                'temperature': getattr(settings, 'xai_temperature', 0.7),
            },
            'gemini': {
                'api_key': getattr(settings, 'gemini_api_key', None),
                'model': getattr(settings, 'gemini_model', 'gemini-pro'),
                'max_tokens': getattr(settings, 'gemini_max_tokens', 4000),
                'temperature': getattr(settings, 'gemini_temperature', 0.7),
            }
        }
        
        # Initialize each provider if API key is available
        for provider_name, config in provider_configs.items():
            if config.get('api_key'):
                try:
                    provider = await self._create_provider(provider_name, config)
                    if await provider.initialize():
                        self.providers[provider_name] = provider
                        self.logger.info(f"✅ {provider_name.title()} provider initialized")
                    else:
                        self.logger.warning(f"❌ {provider_name.title()} provider failed to initialize")
                except Exception as e:
                    self.logger.error(f"❌ Error initializing {provider_name}: {e}")
            else:
                self.logger.info(f"⏭️  Skipping {provider_name.title()} (no API key)")
                
    async def _create_provider(self, name: str, config: Dict[str, Any]) -> BaseAIProvider:
        """Create a provider instance"""
        provider_classes = {
            'deepseek': DeepSeekProvider,
            'openai': OpenAIProvider,
            'anthropic': AnthropicProvider,
            'xai': XAIProvider,
            'gemini': GeminiProvider
        }
        
        provider_class = provider_classes.get(name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {name}")
            
        return provider_class(name, config)
        
    async def _setup_default_preferences(self):
        """Setup default provider preferences for different task types"""
        # Define which providers are best for which tasks
        preferences = [
            # Conversation - General chat, good balance
            ProviderPreference(
                TaskType.CONVERSATION,
                primary_provider="deepseek",
                fallback_providers=["openai", "anthropic", "gemini", "xai"]
            ),
            
            # Analysis - Deep thinking, structured analysis
            ProviderPreference(
                TaskType.ANALYSIS,
                primary_provider="anthropic",
                fallback_providers=["openai", "deepseek", "gemini", "xai"]
            ),
            
            # Creative - Creative writing, storytelling
            ProviderPreference(
                TaskType.CREATIVE,
                primary_provider="openai",
                fallback_providers=["anthropic", "deepseek", "gemini", "xai"]
            ),
            
            # Technical - Programming, technical explanations
            ProviderPreference(
                TaskType.TECHNICAL,
                primary_provider="deepseek",
                fallback_providers=["openai", "anthropic", "xai", "gemini"]
            ),
            
            # Code Generation - Specifically for coding
            ProviderPreference(
                TaskType.CODE_GENERATION,
                primary_provider="deepseek",
                fallback_providers=["openai", "anthropic", "xai", "gemini"]
            ),
            
            # Research - Information gathering and synthesis
            ProviderPreference(
                TaskType.RESEARCH,
                primary_provider="gemini",
                fallback_providers=["anthropic", "openai", "deepseek", "xai"]
            ),
            
            # Emotional Support - Empathetic responses
            ProviderPreference(
                TaskType.EMOTIONAL_SUPPORT,
                primary_provider="anthropic",
                fallback_providers=["openai", "deepseek", "gemini", "xai"]
            ),
            
            # Problem Solving - Logical reasoning
            ProviderPreference(
                TaskType.PROBLEM_SOLVING,
                primary_provider="openai",
                fallback_providers=["anthropic", "deepseek", "xai", "gemini"]
            ),
            
            # Summarization - Text summarization
            ProviderPreference(
                TaskType.SUMMARIZATION,
                primary_provider="anthropic",
                fallback_providers=["openai", "deepseek", "gemini", "xai"]
            ),
            
            # Translation - Language translation
            ProviderPreference(
                TaskType.TRANSLATION,
                primary_provider="gemini",
                fallback_providers=["openai", "anthropic", "deepseek", "xai"]
            )
        ]
        
        for pref in preferences:
            # Only add preference if we have the primary provider available
            if pref.primary_provider in self.providers:
                self.provider_preferences[pref.task_type] = pref
                
    async def chat_completion(
        self,
        messages: List[AIMessage],
        task_type: TaskType = TaskType.CONVERSATION,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate chat completion using the best available provider
        
        Args:
            messages: List of messages for the conversation
            task_type: Type of task to optimize provider selection
            preferred_provider: Force use of specific provider
            **kwargs: Additional arguments for the provider
            
        Returns:
            AIResponse from the selected provider
        """
        if not self.providers:
            raise RuntimeError("No AI providers available")
            
        # Select the best provider for this task
        selected_provider = await self._select_provider(task_type, preferred_provider)
        
        if not selected_provider:
            raise RuntimeError(f"No available provider for task type: {task_type}")
            
        try:
            # Generate response using selected provider
            response = await selected_provider.chat_completion(messages, task_type, **kwargs)
            
            # Track performance metrics
            await self._update_performance_metrics(selected_provider.name, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error with {selected_provider.name}: {e}")
            
            # Try fallback providers
            fallback_response = await self._try_fallback_providers(
                messages, task_type, selected_provider.name, **kwargs
            )
            
            if fallback_response:
                return fallback_response
                
            # If all providers fail, re-raise the original error
            raise e
            
    async def _select_provider(
        self,
        task_type: TaskType,
        preferred_provider: Optional[str] = None
    ) -> Optional[BaseAIProvider]:
        """Select the best provider for a task"""
        
        # Use preferred provider if specified and available
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if await provider.health_check():
                return provider
                
        # Use task-based preference
        preference = self.provider_preferences.get(task_type)
        if preference:
            # Try primary provider
            if preference.primary_provider in self.providers:
                provider = self.providers[preference.primary_provider]
                if await provider.health_check():
                    return provider
                    
            # Try fallback providers
            for fallback_name in preference.fallback_providers:
                if fallback_name in self.providers:
                    provider = self.providers[fallback_name]
                    if await provider.health_check():
                        return provider
                        
        # Fallback to any available provider
        for provider in self.providers.values():
            if await provider.health_check():
                return provider
                
        return None
        
    async def _try_fallback_providers(
        self,
        messages: List[AIMessage],
        task_type: TaskType,
        failed_provider: str,
        **kwargs
    ) -> Optional[AIResponse]:
        """Try fallback providers when primary fails"""
        
        preference = self.provider_preferences.get(task_type)
        if not preference:
            return None
            
        # Try fallback providers
        for fallback_name in preference.fallback_providers:
            if fallback_name == failed_provider or fallback_name not in self.providers:
                continue
                
            try:
                provider = self.providers[fallback_name]
                if await provider.health_check():
                    self.logger.info(f"Trying fallback provider: {fallback_name}")
                    response = await provider.chat_completion(messages, task_type, **kwargs)
                    await self._update_performance_metrics(provider.name, response)
                    return response
            except Exception as e:
                self.logger.warning(f"Fallback provider {fallback_name} also failed: {e}")
                continue
                
        return None
        
    async def _update_performance_metrics(self, provider_name: str, response: AIResponse):
        """Update performance metrics for a provider"""
        if provider_name not in self.performance_metrics:
            self.performance_metrics[provider_name] = {
                'success_count': 0,
                'error_count': 0,
                'avg_response_time': 0.0,
                'total_tokens': 0
            }
            
        metrics = self.performance_metrics[provider_name]
        
        if response.error:
            metrics['error_count'] += 1
        else:
            metrics['success_count'] += 1
            
        # Update token usage
        if response.usage:
            metrics['total_tokens'] += response.usage.get('total_tokens', 0)
            
    async def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        
        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                models = await provider.get_available_models()
                
                status[name] = {
                    'healthy': is_healthy,
                    'models': models,
                    'metrics': self.performance_metrics.get(name, {}),
                    'supported_tasks': [task.value for task in provider.supported_tasks]
                }
            except Exception as e:
                status[name] = {
                    'healthy': False,
                    'error': str(e),
                    'metrics': self.performance_metrics.get(name, {})
                }
                
        return status
        
    async def switch_primary_provider(self, task_type: TaskType, provider_name: str):
        """Switch primary provider for a task type"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not available")
            
        if task_type in self.provider_preferences:
            self.provider_preferences[task_type].primary_provider = provider_name
        else:
            self.provider_preferences[task_type] = ProviderPreference(
                task_type=task_type,
                primary_provider=provider_name,
                fallback_providers=[name for name in self.providers.keys() if name != provider_name]
            )
            
        self.logger.info(f"Switched primary provider for {task_type.value} to {provider_name}")
        
    async def close(self):
        """Close all providers"""
        for provider in self.providers.values():
            await provider.close()
