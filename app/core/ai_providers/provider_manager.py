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
    cost_weight: float = 1.0  # Cost optimization factor
    performance_weight: float = 1.0  # Performance optimization factor


@dataclass
class CostMetrics:
    """Cost tracking for AI providers"""
    provider: str
    task_type: TaskType
    tokens_used: int
    estimated_cost: float
    response_time: float
    success_rate: float


class AIProviderManager:
    """Cost-optimized AI provider manager for ChoyAI productivity modules"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, BaseAIProvider] = {}
        self.provider_preferences: Dict[TaskType, ProviderPreference] = {}
        self.fallback_strategy = "cost_optimized"  # cost_optimized, performance, round_robin
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        self.cost_metrics: List[CostMetrics] = []
        
        # Cost-effective routing priorities (as per architecture doc)
        self.cost_priorities = {
            "orchestration": ["openai"],      # GPT-4o for primary orchestration
            "coding": ["anthropic", "deepseek", "openai"],  # Claude > DeepSeek > GPT-4o
            "documents": ["anthropic", "openai"],            # Claude > GPT-4o
            "analysis": ["anthropic", "openai", "deepseek"], # Claude > GPT-4o > DeepSeek
            "general": ["openai", "anthropic", "deepseek"]   # GPT-4o > Claude > DeepSeek
        }
        
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
        """Setup cost-optimized provider preferences for ChoyAI productivity modules"""
        # Cost-effective preferences based on architecture document
        preferences = [
            # Conversation - GPT-4o primary orchestrator
            ProviderPreference(
                TaskType.CONVERSATION,
                primary_provider="openai",  # GPT-4o for orchestration
                fallback_providers=["anthropic", "deepseek"],
                cost_weight=1.0,
                performance_weight=1.2
            ),
            
            # Analysis - Claude for documents and analysis
            ProviderPreference(
                TaskType.ANALYSIS,
                primary_provider="anthropic",  # Claude for long-form analysis
                fallback_providers=["openai", "deepseek"],
                cost_weight=1.1,  # Slightly higher cost but better quality
                performance_weight=1.3
            ),
            
            # Creative - GPT-4o for creative tasks
            ProviderPreference(
                TaskType.CREATIVE,
                primary_provider="openai",  # GPT-4o for creativity
                fallback_providers=["anthropic", "deepseek"],
                cost_weight=1.0,
                performance_weight=1.2
            ),
            
            # Technical/Coding - Claude > DeepSeek > GPT-4o (priority order)
            ProviderPreference(
                TaskType.TECHNICAL,
                primary_provider="anthropic",  # Claude first for coding
                fallback_providers=["deepseek", "openai"],  # DeepSeek second, GPT-4o third
                cost_weight=0.8,  # Lower cost for technical tasks
                performance_weight=1.4
            ),
            
            # Code Generation - Claude > DeepSeek > GPT-4o (cost-effective coding)
            ProviderPreference(
                TaskType.CODE_GENERATION,
                primary_provider="anthropic",  # Claude priority #1 for code
                fallback_providers=["deepseek", "openai"],  # DeepSeek fast secondary
                cost_weight=0.7,  # Lowest cost for coding
                performance_weight=1.5
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
    
    async def _track_cost_metrics(self, provider: str, task_type: TaskType, 
                                 tokens_used: int, response_time: float, success: bool):
        """Track cost metrics for optimization"""
        # Estimate cost based on provider and usage
        estimated_cost = self._estimate_cost(provider, tokens_used)
        
        # Calculate success rate
        success_rate = 1.0 if success else 0.0
        
        # Store metrics
        cost_metric = CostMetrics(
            provider=provider,
            task_type=task_type,
            tokens_used=tokens_used,
            estimated_cost=estimated_cost,
            response_time=response_time,
            success_rate=success_rate
        )
        
        self.cost_metrics.append(cost_metric)
        
        # Keep only last 1000 metrics to prevent memory issues
        if len(self.cost_metrics) > 1000:
            self.cost_metrics = self.cost_metrics[-1000:]
    
    def _estimate_cost(self, provider: str, tokens_used: int) -> float:
        """Estimate cost based on provider pricing"""
        # Approximate costs per 1K tokens (as of 2024/2025)
        cost_per_1k_tokens = {
            "openai": 0.03,      # GPT-4o pricing
            "anthropic": 0.025,  # Claude-3 pricing
            "deepseek": 0.002,   # DeepSeek very cost-effective
            "gemini": 0.015,     # Gemini Pro pricing
            "xai": 0.02          # Estimated xAI pricing
        }
        
        rate = cost_per_1k_tokens.get(provider, 0.02)  # Default rate
        return (tokens_used / 1000.0) * rate
    
    def _select_cost_optimized_provider(self, task_type: TaskType, 
                                      available_providers: List[str]) -> str:
        """Select provider based on cost optimization for productivity modules"""
        
        # Map task types to cost-effective provider priorities
        cost_routing = {
            TaskType.CONVERSATION: self.cost_priorities["orchestration"],
            TaskType.ANALYSIS: self.cost_priorities["documents"],
            TaskType.TECHNICAL: self.cost_priorities["coding"],
            TaskType.CODE_GENERATION: self.cost_priorities["coding"],
            TaskType.SUMMARIZATION: self.cost_priorities["documents"],
            TaskType.CREATIVE: self.cost_priorities["general"],
            TaskType.PROBLEM_SOLVING: self.cost_priorities["analysis"],
            TaskType.EMOTIONAL_SUPPORT: self.cost_priorities["general"],
            TaskType.TRANSLATION: self.cost_priorities["general"]
        }
        
        # Get priority list for this task type
        priority_list = cost_routing.get(task_type, self.cost_priorities["general"])
        
        # Find first available provider in priority order
        for preferred_provider in priority_list:
            if preferred_provider in available_providers:
                return preferred_provider
        
        # Fallback to first available provider
        return available_providers[0] if available_providers else "openai"
    
    async def get_cost_analytics(self) -> Dict[str, Any]:
        """Get cost analytics for productivity modules"""
        if not self.cost_metrics:
            return {"total_cost": 0, "provider_breakdown": {}, "task_breakdown": {}}
        
        total_cost = sum(metric.estimated_cost for metric in self.cost_metrics)
        
        # Provider breakdown
        provider_costs = {}
        for metric in self.cost_metrics:
            if metric.provider not in provider_costs:
                provider_costs[metric.provider] = {
                    "cost": 0, "tokens": 0, "requests": 0, "avg_response_time": 0
                }
            provider_costs[metric.provider]["cost"] += metric.estimated_cost
            provider_costs[metric.provider]["tokens"] += metric.tokens_used
            provider_costs[metric.provider]["requests"] += 1
            provider_costs[metric.provider]["avg_response_time"] += metric.response_time
        
        # Calculate averages
        for provider in provider_costs:
            requests = provider_costs[provider]["requests"]
            provider_costs[provider]["avg_response_time"] /= requests
        
        # Task type breakdown
        task_costs = {}
        for metric in self.cost_metrics:
            task_name = metric.task_type.value
            if task_name not in task_costs:
                task_costs[task_name] = {"cost": 0, "requests": 0}
            task_costs[task_name]["cost"] += metric.estimated_cost
            task_costs[task_name]["requests"] += 1
        
        return {
            "total_cost": total_cost,
            "provider_breakdown": provider_costs,
            "task_breakdown": task_costs,
            "metrics_count": len(self.cost_metrics),
            "cost_efficiency_tips": self._get_cost_optimization_tips()
        }
    
    def _get_cost_optimization_tips(self) -> List[str]:
        """Provide cost optimization recommendations"""
        tips = []
        
        if not self.cost_metrics:
            return ["No metrics available yet"]
        
        # Analyze provider usage patterns
        provider_usage = {}
        for metric in self.cost_metrics:
            if metric.provider not in provider_usage:
                provider_usage[metric.provider] = []
            provider_usage[metric.provider].append(metric.estimated_cost)
        
        # Find most expensive provider
        avg_costs = {}
        for provider, costs in provider_usage.items():
            avg_costs[provider] = sum(costs) / len(costs)
        
        if avg_costs:
            most_expensive = max(avg_costs, key=avg_costs.get)
            cheapest = min(avg_costs, key=avg_costs.get)
            
            if most_expensive != cheapest:
                tips.append(f"Consider using {cheapest} more often instead of {most_expensive} for cost savings")
        
        tips.extend([
            "Use DeepSeek for coding tasks to minimize costs",
            "Use Claude for document analysis and long-form content",
            "Use GPT-4o for orchestration and complex reasoning",
            "Implement local database storage to reduce API calls",
            "Cache frequently requested information locally"
        ])
        
        return tips
