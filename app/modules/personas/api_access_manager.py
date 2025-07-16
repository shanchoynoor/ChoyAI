"""
API Access Manager for Personas

Manages API access for personas, ensuring they can access live information
through the productivity modules system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass

from app.modules.productivity import (
    ProductivityModuleManager, ModuleRequest, ModuleResponse, ModuleType
)
from app.config.settings import get_settings


@dataclass
class APICapability:
    """API capability definition"""
    name: str
    description: str
    module_type: ModuleType
    actions: List[str]
    cost_estimate: float
    requires_auth: bool = False


class APIAccessManager:
    """
    Manages API access for personas to ensure they can access live information
    """
    
    def __init__(self, productivity_manager: ProductivityModuleManager):
        self.productivity_manager = productivity_manager
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # API capabilities available to personas
        self.api_capabilities = self._initialize_api_capabilities()
        
    def _initialize_api_capabilities(self) -> Dict[str, APICapability]:
        """Initialize available API capabilities"""
        capabilities = {
            "weather": APICapability(
                name="Weather Information",
                description="Get current weather conditions and forecasts",
                module_type=ModuleType.ONLINE_AGENT,
                actions=["get_weather", "weather", "forecast"],
                cost_estimate=0.0,  # Free API
                requires_auth=False
            ),
            "news": APICapability(
                name="News & Current Events",
                description="Access latest news and trending topics",
                module_type=ModuleType.ONLINE_AGENT,
                actions=["get_news", "news", "current_events"],
                cost_estimate=0.0,  # Free API
                requires_auth=False
            ),
            "web_search": APICapability(
                name="Web Search",
                description="Search the internet for current information",
                module_type=ModuleType.ONLINE_AGENT,
                actions=["web_search", "search", "search_web"],
                cost_estimate=0.0,  # Free tier
                requires_auth=False
            ),
            "finance": APICapability(
                name="Financial Data",
                description="Stock prices, cryptocurrency, and market information",
                module_type=ModuleType.ONLINE_AGENT,
                actions=["get_finance", "stock_price", "crypto_price"],
                cost_estimate=0.0,  # Free API
                requires_auth=False
            ),
            "maps": APICapability(
                name="Maps & Location",
                description="Find locations, addresses, and directions",
                module_type=ModuleType.ONLINE_AGENT,
                actions=["get_maps", "find_location", "directions"],
                cost_estimate=0.0,  # Free tier
                requires_auth=False
            ),
            "calendar": APICapability(
                name="Calendar Events",
                description="Manage calendar events and scheduling",
                module_type=ModuleType.CALENDAR,
                actions=["list_events", "create_event", "find_free_time"],
                cost_estimate=0.0,  # Local + Google API (free)
                requires_auth=True
            ),
            "tasks": APICapability(
                name="Task Management",
                description="Create and manage tasks and to-dos",
                module_type=ModuleType.TASKS,
                actions=["create_task", "list_tasks", "analyze_tasks"],
                cost_estimate=0.01,  # Minimal AI usage
                requires_auth=False
            ),
            "notes": APICapability(
                name="Smart Notes",
                description="Create, search, and summarize notes",
                module_type=ModuleType.NOTES,
                actions=["create_note", "search_notes", "summarize_notes"],
                cost_estimate=0.02,  # AI summarization
                requires_auth=False
            ),
            "translation": APICapability(
                name="Translation Services",
                description="Translate text between languages",
                module_type=ModuleType.ONLINE_AGENT,
                actions=["translate", "translate_text"],
                cost_estimate=0.0,  # Free API
                requires_auth=False
            ),
            "social_trends": APICapability(
                name="Social Media Trends",
                description="Current trending topics and social information",
                module_type=ModuleType.ONLINE_AGENT,
                actions=["get_trends", "social_trends"],
                cost_estimate=0.0,  # Free API
                requires_auth=False
            )
        }
        
        return capabilities
    
    async def execute_api_request(
        self,
        user_id: str,
        capability_name: str,
        action: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResponse:
        """
        Execute an API request through the appropriate productivity module
        """
        try:
            # Validate capability
            if capability_name not in self.api_capabilities:
                return ModuleResponse(
                    success=False,
                    data=None,
                    message=f"Unknown API capability: {capability_name}",
                    error="INVALID_CAPABILITY"
                )
            
            capability = self.api_capabilities[capability_name]
            
            # Validate action
            if action not in capability.actions:
                return ModuleResponse(
                    success=False,
                    data=None,
                    message=f"Action '{action}' not supported for {capability_name}",
                    error="INVALID_ACTION"
                )
            
            # Create module request
            module_request = ModuleRequest(
                user_id=user_id,
                module_type=capability.module_type,
                action=action,
                data=data,
                context=context,
                metadata={
                    "persona_api_request": True,
                    "capability": capability_name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Execute request through productivity manager
            response = await self.productivity_manager.process_request(module_request)
            
            # Log API usage
            self.logger.info(
                f"API request executed - User: {user_id}, Capability: {capability_name}, "
                f"Action: {action}, Success: {response.success}, Cost: ${response.cost_estimate:.4f}"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error executing API request: {e}")
            return ModuleResponse(
                success=False,
                data=None,
                message=f"Failed to execute API request: {str(e)}",
                error=str(e)
            )
    
    async def get_weather_info(self, user_id: str, location: Optional[str] = None) -> ModuleResponse:
        """Get weather information for a location"""
        data = {}
        if location:
            data["location"] = location
        
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="weather",
            action="get_weather",
            data=data
        )
    
    async def search_web(self, user_id: str, query: str, num_results: int = 5) -> ModuleResponse:
        """Search the web for information"""
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="web_search",
            action="web_search",
            data={"query": query, "num_results": num_results}
        )
    
    async def get_news(self, user_id: str, query: Optional[str] = None, category: Optional[str] = None) -> ModuleResponse:
        """Get latest news"""
        data = {}
        if query:
            data["query"] = query
        if category:
            data["category"] = category
        
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="news",
            action="get_news",
            data=data
        )
    
    async def get_financial_info(self, user_id: str, symbol: str) -> ModuleResponse:
        """Get financial information for a symbol"""
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="finance",
            action="get_finance",
            data={"symbol": symbol}
        )
    
    async def find_location(self, user_id: str, location: str) -> ModuleResponse:
        """Find location information"""
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="maps",
            action="find_location",
            data={"location": location}
        )
    
    async def translate_text(self, user_id: str, text: str, target_language: str, source_language: Optional[str] = None) -> ModuleResponse:
        """Translate text to target language"""
        data = {"text": text, "target_language": target_language}
        if source_language:
            data["source_language"] = source_language
        
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="translation",
            action="translate",
            data=data
        )
    
    async def get_social_trends(self, user_id: str, platform: Optional[str] = None) -> ModuleResponse:
        """Get social media trends"""
        data = {}
        if platform:
            data["platform"] = platform
        
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="social_trends",
            action="get_trends",
            data=data
        )
    
    async def create_calendar_event(
        self,
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> ModuleResponse:
        """Create a calendar event"""
        data = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time
        }
        if description:
            data["description"] = description
        if location:
            data["location"] = location
        
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="calendar",
            action="create_event",
            data=data
        )
    
    async def create_task(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> ModuleResponse:
        """Create a new task"""
        data = {"title": title}
        if description:
            data["description"] = description
        if priority:
            data["priority"] = priority
        if due_date:
            data["due_date"] = due_date
        
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="tasks",
            action="create_task",
            data=data
        )
    
    async def create_note(
        self,
        user_id: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> ModuleResponse:
        """Create a new note"""
        data = {"title": title, "content": content}
        if tags:
            data["tags"] = tags
        
        return await self.execute_api_request(
            user_id=user_id,
            capability_name="notes",
            action="create_note",
            data=data
        )
    
    def get_available_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all available API capabilities"""
        return {
            name: {
                "name": cap.name,
                "description": cap.description,
                "actions": cap.actions,
                "cost_estimate": cap.cost_estimate,
                "requires_auth": cap.requires_auth
            }
            for name, cap in self.api_capabilities.items()
        }
    
    async def get_capability_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all API capabilities"""
        status = {}
        
        for name, capability in self.api_capabilities.items():
            # Check if the required module is available
            module_available = capability.module_type in self.productivity_manager.modules
            
            if module_available:
                module = self.productivity_manager.modules[capability.module_type]
                module_healthy = await module.health_check()
            else:
                module_healthy = False
            
            status[name] = {
                "name": capability.name,
                "description": capability.description,
                "module_available": module_available,
                "module_healthy": module_healthy,
                "status": "available" if module_available and module_healthy else "unavailable",
                "cost_estimate": capability.cost_estimate,
                "requires_auth": capability.requires_auth
            }
        
        return status
    
    async def test_api_capability(self, capability_name: str, user_id: str = "test_user") -> Dict[str, Any]:
        """Test an API capability with a simple request"""
        try:
            if capability_name not in self.api_capabilities:
                return {"success": False, "error": f"Unknown capability: {capability_name}"}
            
            capability = self.api_capabilities[capability_name]
            test_action = capability.actions[0]  # Use first action as test
            
            # Define test data for each capability
            test_data = {
                "weather": {"location": "New York"},
                "news": {"query": "technology"},
                "web_search": {"query": "test search", "num_results": 1},
                "finance": {"symbol": "AAPL"},
                "maps": {"location": "New York"},
                "translation": {"text": "Hello", "target_language": "es"},
                "social_trends": {},
                "calendar": {"title": "Test Event", "start_time": "2024-01-01T10:00:00", "end_time": "2024-01-01T11:00:00"},
                "tasks": {"title": "Test Task"},
                "notes": {"title": "Test Note", "content": "Test content"}
            }
            
            data = test_data.get(capability_name, {})
            
            response = await self.execute_api_request(
                user_id=user_id,
                capability_name=capability_name,
                action=test_action,
                data=data
            )
            
            return {
                "success": response.success,
                "message": response.message,
                "cost_estimate": response.cost_estimate,
                "processing_time": response.processing_time,
                "error": response.error
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
