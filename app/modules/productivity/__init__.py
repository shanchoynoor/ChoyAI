"""
ChoyAI Productivity Modules Core System

Base architecture for 14 cost-effective productivity modules
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.core.ai_providers import AIProviderManager, TaskType


class ModuleType(Enum):
    """Types of productivity modules"""
    CHAT_VOICE = "chat_voice"           # Module 1: Chat/Voice
    CALENDAR = "calendar"               # Module 2: Reminders/Calendar  
    TASKS = "tasks"                     # Module 3: Tasks/To-Do
    NOTES = "notes"                     # Module 4: Notes
    DRIVE = "drive"                     # Module 5: Cloud Drive
    NEWS = "news"                       # Module 6: News
    MAIL = "mail"                       # Module 7: Mail
    MESSAGING = "messaging"             # Module 8: Messaging Hub
    VOICE = "voice"                     # Module 9: Call/Voice (STT/TTS)
    SOCIAL = "social"                   # Module 10: Social Media
    FINANCE = "finance"                 # Module 11: Accounts/Finance
    PROJECT = "project"                 # Module 12: Project Management
    TRADING = "trading"                 # Module 13: Trading Analysis
    ONLINE_AGENT = "online_agent"       # Module 14: Online Agent


@dataclass
class ModuleRequest:
    """Request structure for productivity modules"""
    user_id: str
    module_type: ModuleType
    action: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModuleResponse:
    """Response structure from productivity modules"""
    success: bool
    data: Any
    message: str
    cost_estimate: float = 0.0
    processing_time: float = 0.0
    ai_provider_used: Optional[str] = None
    external_apis_used: List[str] = None
    error: Optional[str] = None


@dataclass
class ModuleConfig:
    """Configuration for each productivity module"""
    module_type: ModuleType
    name: str
    description: str
    enabled: bool = True
    cost_limit_daily: float = 5.0  # Daily cost limit in USD
    preferred_ai_provider: Optional[str] = None
    external_apis: List[str] = None
    local_storage: bool = True
    requires_auth: bool = False


class BaseProductivityModule(ABC):
    """Base class for all productivity modules"""
    
    def __init__(self, config: ModuleConfig, ai_provider_manager: AIProviderManager):
        self.config = config
        self.ai_provider_manager = ai_provider_manager
        self.logger = logging.getLogger(f"module.{config.module_type.value}")
        self.daily_cost = 0.0
        self.request_count = 0
        self.last_reset = datetime.now().date()
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the module"""
        pass
    
    @abstractmethod
    async def process_request(self, request: ModuleRequest) -> ModuleResponse:
        """Process a module request"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get list of module capabilities"""
        pass
    
    async def health_check(self) -> bool:
        """Check if module is healthy"""
        try:
            return self.config.enabled and await self._module_health_check()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    @abstractmethod
    async def _module_health_check(self) -> bool:
        """Module-specific health check"""
        pass
    
    async def _use_ai_provider(self, messages: List[Any], task_type: TaskType = TaskType.CONVERSATION) -> ModuleResponse:
        """Use AI provider with cost tracking"""
        start_time = datetime.now()
        
        try:
            # Check daily cost limit
            if self.daily_cost >= self.config.cost_limit_daily:
                return ModuleResponse(
                    success=False,
                    data=None,
                    message="Daily cost limit reached",
                    error="COST_LIMIT_EXCEEDED"
                )
            
            # Reset daily counters if needed
            if datetime.now().date() > self.last_reset:
                self.daily_cost = 0.0
                self.request_count = 0
                self.last_reset = datetime.now().date()
            
            # Use AI provider
            response = await self.ai_provider_manager.chat_completion(
                messages=messages,
                task_type=task_type,
                preferred_provider=self.config.preferred_ai_provider
            )
            
            # Calculate cost and processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            estimated_cost = self._estimate_request_cost(response)
            
            # Update metrics
            self.daily_cost += estimated_cost
            self.request_count += 1
            
            return ModuleResponse(
                success=not response.error,
                data=response.content if not response.error else None,
                message="AI response generated successfully" if not response.error else f"AI error: {response.error}",
                cost_estimate=estimated_cost,
                processing_time=processing_time,
                ai_provider_used=response.provider_used,
                error=response.error
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"AI provider error: {e}")
            
            return ModuleResponse(
                success=False,
                data=None,
                message=f"AI provider failed: {str(e)}",
                processing_time=processing_time,
                error=str(e)
            )
    
    def _estimate_request_cost(self, ai_response) -> float:
        """Estimate cost of AI request"""
        if not ai_response.usage:
            return 0.01  # Default small cost
        
        tokens = ai_response.usage.get('total_tokens', 100)
        
        # Cost per 1K tokens by provider
        provider_costs = {
            'openai': 0.03,     # GPT-4o
            'anthropic': 0.025, # Claude
            'deepseek': 0.002,  # DeepSeek (very cheap)
            'gemini': 0.015,    # Gemini
            'xai': 0.02         # xAI
        }
        
        rate = provider_costs.get(ai_response.provider_used, 0.02)
        return (tokens / 1000.0) * rate
    
    async def get_module_stats(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            "module_type": self.config.module_type.value,
            "enabled": self.config.enabled,
            "daily_cost": self.daily_cost,
            "cost_limit": self.config.cost_limit_daily,
            "request_count": self.request_count,
            "last_reset": self.last_reset.isoformat(),
            "health": await self.health_check()
        }


class ProductivityModuleManager:
    """Manager for all productivity modules"""
    
    def __init__(self, ai_provider_manager: AIProviderManager):
        self.ai_provider_manager = ai_provider_manager
        self.modules: Dict[ModuleType, BaseProductivityModule] = {}
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize all enabled modules"""
        self.logger.info("🚀 Initializing ChoyAI Productivity Modules...")
        
        # Initialize modules in priority order (cost-effective first)
        module_configs = self._get_default_module_configs()
        
        for config in module_configs:
            if config.enabled:
                try:
                    module = await self._create_module(config)
                    if await module.initialize():
                        self.modules[config.module_type] = module
                        self.logger.info(f"✅ Initialized {config.name}")
                    else:
                        self.logger.warning(f"⚠️ Failed to initialize {config.name}")
                except Exception as e:
                    self.logger.error(f"❌ Error initializing {config.name}: {e}")
        
        self.logger.info(f"🎯 Initialized {len(self.modules)}/14 productivity modules")
    
    async def _create_module(self, config: ModuleConfig) -> BaseProductivityModule:
        """Create module instance based on type"""
        try:
            if config.module_type == ModuleType.TASKS:
                from app.modules.productivity.tasks_module import TasksModule
                return TasksModule(config, self.ai_provider_manager)
            
            elif config.module_type == ModuleType.NOTES:
                from app.modules.productivity.notes_module import NotesModule
                return NotesModule(config, self.ai_provider_manager)
            
            elif config.module_type == ModuleType.CALENDAR:
                from app.modules.productivity.calendar_module import CalendarModule
                return CalendarModule(config, self.ai_provider_manager)
            
            elif config.module_type == ModuleType.CHAT_VOICE:
                from app.modules.productivity.chat_voice_module import ChatVoiceModule
                return ChatVoiceModule(config, self.ai_provider_manager)
            
            elif config.module_type == ModuleType.MESSAGING:
                from app.modules.productivity.messaging_module import MessagingModule
                return MessagingModule(config, self.ai_provider_manager)
            
            elif config.module_type == ModuleType.ONLINE_AGENT:
                from app.modules.productivity.online_agent_module import OnlineAgentModule
                return OnlineAgentModule(config, self.ai_provider_manager)
            
            # Placeholder for unimplemented modules
            else:
                raise NotImplementedError(f"Module {config.module_type.value} not implemented yet")
                
        except ImportError as e:
            self.logger.warning(f"Failed to import {config.module_type.value} module: {e}")
            raise NotImplementedError(f"Module {config.module_type.value} implementation not available")
    
    def _get_default_module_configs(self) -> List[ModuleConfig]:
        """Get default configurations for all modules"""
        return [
            # Phase 1: Core modules (highest priority, lowest cost)
            ModuleConfig(
                module_type=ModuleType.TASKS,
                name="Tasks & To-Do",
                description="AI-powered task management with local storage",
                cost_limit_daily=1.0,  # Very low cost
                external_apis=[],
                local_storage=True
            ),
            ModuleConfig(
                module_type=ModuleType.NOTES,
                name="Smart Notes",
                description="AI-enhanced note taking and summarization",
                cost_limit_daily=1.0,
                external_apis=[],
                local_storage=True
            ),
            ModuleConfig(
                module_type=ModuleType.CALENDAR,
                name="Calendar & Reminders",
                description="Intelligent scheduling with Google Calendar",
                cost_limit_daily=0.5,  # Minimal AI usage
                external_apis=["google_calendar"],
                local_storage=True
            ),
            ModuleConfig(
                module_type=ModuleType.CHAT_VOICE,
                name="Chat & Voice",
                description="Core conversational AI with voice support",
                cost_limit_daily=5.0,  # Highest usage expected
                external_apis=["openai_whisper"],
                local_storage=False
            ),
            
            # Phase 2: Communication modules
            ModuleConfig(
                module_type=ModuleType.MESSAGING,
                name="Messaging Hub",
                description="Unified messaging across platforms",
                cost_limit_daily=2.0,
                external_apis=["telegram_bot"],
                local_storage=True
            ),
            ModuleConfig(
                module_type=ModuleType.MAIL,
                name="Email Assistant",
                description="AI-powered email drafting and management",
                cost_limit_daily=2.0,
                external_apis=["gmail_api"],
                local_storage=True
            ),
            
            # Phase 3: Information modules
            ModuleConfig(
                module_type=ModuleType.NEWS,
                name="News Aggregator",
                description="Personalized news summaries",
                cost_limit_daily=0.5,
                external_apis=["rss_feeds"],
                local_storage=True
            ),
            ModuleConfig(
                module_type=ModuleType.FINANCE,
                name="Finance Tracker",
                description="Personal finance management",
                cost_limit_daily=0.5,
                external_apis=["google_sheets"],
                local_storage=True
            ),
            ModuleConfig(
                module_type=ModuleType.TRADING,
                name="Trading Analysis",
                description="Cryptocurrency and market analysis",
                cost_limit_daily=1.0,
                external_apis=["coingecko_api"],
                local_storage=True
            ),
            
            # Phase 4: Advanced modules (implement later)
            ModuleConfig(
                module_type=ModuleType.DRIVE,
                name="Cloud Drive",
                description="Intelligent file management",
                cost_limit_daily=1.0,
                external_apis=["supabase"],
                local_storage=False,
                enabled=False  # Implement later
            ),
            ModuleConfig(
                module_type=ModuleType.SOCIAL,
                name="Social Media",
                description="Social media content and management",
                cost_limit_daily=2.0,
                external_apis=["twitter_api", "facebook_api"],
                local_storage=True,
                enabled=False  # Implement later
            ),
            ModuleConfig(
                module_type=ModuleType.PROJECT,
                name="Project Manager",
                description="AI-powered project management",
                cost_limit_daily=1.0,
                external_apis=[],
                local_storage=True,
                enabled=False  # Implement later
            ),
            ModuleConfig(
                module_type=ModuleType.VOICE,
                name="Voice Processing",
                description="Speech-to-text and text-to-speech",
                cost_limit_daily=3.0,
                external_apis=["openai_whisper", "elevenlabs_tts"],
                local_storage=False,
                enabled=False  # Implement later
            ),
            ModuleConfig(
                module_type=ModuleType.ONLINE_AGENT,
                name="Online Agent",
                description="Web search and live information access",
                cost_limit_daily=2.0,
                external_apis=["serper_api", "weather_api", "news_api", "perplexity_api"],
                local_storage=True,
                enabled=True  # Enable the online agent module
            )
        ]
    
    async def process_request(self, request: ModuleRequest) -> ModuleResponse:
        """Process a request through the appropriate module"""
        if request.module_type not in self.modules:
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Module {request.module_type.value} not available",
                error="MODULE_NOT_AVAILABLE"
            )
        
        module = self.modules[request.module_type]
        
        if not await module.health_check():
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Module {request.module_type.value} is unhealthy",
                error="MODULE_UNHEALTHY"
            )
        
        return await module.process_request(request)
    
    async def get_all_module_stats(self) -> Dict[str, Any]:
        """Get statistics for all modules"""
        stats = {}
        total_cost = 0.0
        
        for module_type, module in self.modules.items():
            module_stats = await module.get_module_stats()
            stats[module_type.value] = module_stats
            total_cost += module_stats["daily_cost"]
        
        return {
            "total_daily_cost": total_cost,
            "active_modules": len(self.modules),
            "total_modules": len(ModuleType),
            "modules": stats,
            "cost_optimization": total_cost < 20.0  # Target: under $20/day
        }


# Export main classes
__all__ = [
    "ModuleType", "ModuleRequest", "ModuleResponse", "ModuleConfig",
    "BaseProductivityModule", "ProductivityModuleManager"
]
