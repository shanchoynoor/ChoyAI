"""
Productivity API Endpoints - ChoyAI

REST API for 14 productivity modules with cost optimization
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from app.modules.productivity import (
    ProductivityModuleManager, ModuleRequest, ModuleResponse, ModuleType
)
from app.core.ai_providers import AIProviderManager

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/productivity", tags=["productivity"])

# Global productivity manager (will be initialized in main.py)
productivity_manager: Optional[ProductivityModuleManager] = None


# Pydantic models for API
class ProductivityRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    module_type: str = Field(..., description="Productivity module type")
    action: str = Field(..., description="Action to perform")
    data: Dict[str, Any] = Field(default_factory=dict, description="Request data")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ProductivityApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: str
    cost_estimate: float = 0.0
    processing_time: float = 0.0
    ai_provider_used: Optional[str] = None
    external_apis_used: Optional[List[str]] = None
    error: Optional[str] = None


class ModuleStatsResponse(BaseModel):
    total_daily_cost: float
    active_modules: int
    total_modules: int
    modules: Dict[str, Any]
    cost_optimization: bool


# Dependency to get productivity manager
async def get_productivity_manager() -> ProductivityModuleManager:
    if productivity_manager is None:
        raise HTTPException(status_code=503, detail="Productivity modules not initialized")
    return productivity_manager


@router.post("/request", response_model=ProductivityApiResponse)
async def process_productivity_request(
    request: ProductivityRequest,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Process a productivity module request"""
    try:
        # Validate module type
        try:
            module_type = ModuleType(request.module_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid module type: {request.module_type}"
            )
        
        # Create module request
        module_request = ModuleRequest(
            user_id=request.user_id,
            module_type=module_type,
            action=request.action,
            data=request.data,
            context=request.context
        )
        
        # Process request
        response = await manager.process_request(module_request)
        
        # Convert to API response
        return ProductivityApiResponse(
            success=response.success,
            data=response.data,
            message=response.message,
            cost_estimate=response.cost_estimate,
            processing_time=response.processing_time,
            ai_provider_used=response.ai_provider_used,
            external_apis_used=response.external_apis_used,
            error=response.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing productivity request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules", response_model=List[str])
async def get_available_modules(
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Get list of available productivity modules"""
    return [module_type.value for module_type in ModuleType]


@router.get("/modules/{module_type}/capabilities", response_model=List[str])
async def get_module_capabilities(
    module_type: str,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Get capabilities of a specific module"""
    try:
        module_enum = ModuleType(module_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid module type: {module_type}")
    
    if module_enum not in manager.modules:
        raise HTTPException(status_code=404, detail=f"Module {module_type} not available")
    
    module = manager.modules[module_enum]
    capabilities = await module.get_capabilities()
    return capabilities


@router.get("/stats", response_model=ModuleStatsResponse)
async def get_productivity_stats(
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Get statistics for all productivity modules"""
    stats = await manager.get_all_module_stats()
    return ModuleStatsResponse(**stats)


@router.get("/health")
async def health_check(
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Health check for productivity modules"""
    module_health = {}
    
    for module_type, module in manager.modules.items():
        module_health[module_type.value] = await module.health_check()
    
    all_healthy = all(module_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "modules": module_health,
        "timestamp": datetime.now().isoformat()
    }


# Specific module endpoints for common operations

@router.post("/tasks/create")
async def create_task(
    user_id: str,
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: Optional[str] = None,
    tags: List[str] = [],
    ai_enhance: bool = True,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Create a new task"""
    request = ModuleRequest(
        user_id=user_id,
        module_type=ModuleType.TASKS,
        action="create",
        data={
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "tags": tags,
            "ai_enhance": ai_enhance
        }
    )
    
    response = await manager.process_request(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error or response.message)
    
    return response.data


@router.get("/tasks/list")
async def list_tasks(
    user_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
    due_soon: bool = False,
    limit: int = 50,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """List user tasks with filters"""
    request = ModuleRequest(
        user_id=user_id,
        module_type=ModuleType.TASKS,
        action="list",
        data={
            "status": status,
            "priority": priority,
            "tag": tag,
            "due_soon": due_soon,
            "limit": limit
        }
    )
    
    response = await manager.process_request(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error or response.message)
    
    return response.data


@router.post("/notes/create")
async def create_note(
    user_id: str,
    title: str,
    content: str,
    note_type: str = "text",
    tags: List[str] = [],
    ai_enhance: bool = True,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Create a new note"""
    request = ModuleRequest(
        user_id=user_id,
        module_type=ModuleType.NOTES,
        action="create",
        data={
            "title": title,
            "content": content,
            "note_type": note_type,
            "tags": tags,
            "ai_enhance": ai_enhance
        }
    )
    
    response = await manager.process_request(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error or response.message)
    
    return response.data


@router.get("/notes/search")
async def search_notes(
    user_id: str,
    query: str,
    limit: int = 20,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Search notes by content"""
    request = ModuleRequest(
        user_id=user_id,
        module_type=ModuleType.NOTES,
        action="search",
        data={
            "query": query,
            "limit": limit
        }
    )
    
    response = await manager.process_request(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error or response.message)
    
    return response.data


@router.post("/calendar/create-event")
async def create_calendar_event(
    user_id: str,
    title: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: str = "",
    event_type: str = "personal",
    location: Optional[str] = None,
    attendees: List[str] = [],
    ai_enhance: bool = True,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Create a new calendar event"""
    request = ModuleRequest(
        user_id=user_id,
        module_type=ModuleType.CALENDAR,
        action="create_event",
        data={
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "event_type": event_type,
            "location": location,
            "attendees": attendees,
            "ai_enhance": ai_enhance
        }
    )
    
    response = await manager.process_request(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error or response.message)
    
    return response.data


@router.get("/calendar/free-time")
async def find_free_time(
    user_id: str,
    duration: int = 60,  # minutes
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    work_start_hour: int = 9,
    work_end_hour: int = 18,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Find available time slots"""
    request = ModuleRequest(
        user_id=user_id,
        module_type=ModuleType.CALENDAR,
        action="find_free_time",
        data={
            "duration": duration,
            "date_from": date_from,
            "date_to": date_to,
            "work_start_hour": work_start_hour,
            "work_end_hour": work_end_hour
        }
    )
    
    response = await manager.process_request(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error or response.message)
    
    return response.data


@router.post("/chat")
async def chat_message(
    user_id: str,
    message: str,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    use_rag: bool = True,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Send a chat message"""
    request = ModuleRequest(
        user_id=user_id,
        module_type=ModuleType.CHAT_VOICE,
        action="chat",
        data={
            "message": message,
            "session_id": session_id,
            "context": context or {},
            "use_rag": use_rag
        }
    )
    
    response = await manager.process_request(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error or response.message)
    
    return response.data


# Background task for daily cost reset
@router.post("/admin/reset-daily-costs")
async def reset_daily_costs(
    background_tasks: BackgroundTasks,
    manager: ProductivityModuleManager = Depends(get_productivity_manager)
):
    """Reset daily cost counters (admin endpoint)"""
    def reset_costs():
        for module in manager.modules.values():
            module.daily_cost = 0.0
            module.request_count = 0
            module.last_reset = datetime.now().date()
    
    background_tasks.add_task(reset_costs)
    
    return {"message": "Daily costs reset scheduled"}


# Module initialization function (called from main.py)
async def initialize_productivity_modules(ai_provider_manager: AIProviderManager):
    """Initialize productivity modules"""
    global productivity_manager
    
    try:
        productivity_manager = ProductivityModuleManager(ai_provider_manager)
        await productivity_manager.initialize()
        logger.info("🎯 Productivity modules initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize productivity modules: {e}")
        return False
