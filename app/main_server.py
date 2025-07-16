"""
ChoyAI FastAPI Server - Cost-Effective Productivity Suite

Enhanced FastAPI server with 14 productivity modules
Cost-optimized 3-LLM orchestration (GPT-4o, Claude, DeepSeek)
"""

import asyncio
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.ai_engine import ChoyAIEngine
from app.core.ai_providers import AIProviderManager
from app.api.health import router as health_router
from app.api.productivity import router as productivity_router, initialize_productivity_modules
from app.config.settings import settings
from app.utils.logger import setup_logging

# Global instances
ai_engine: ChoyAIEngine = None
ai_provider_manager: AIProviderManager = None

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("🚀 Starting ChoyAI Productivity Server...")
    
    try:
        # Initialize AI Engine
        global ai_engine, ai_provider_manager
        ai_engine = ChoyAIEngine()
        await ai_engine.initialize()
        
        # Get AI provider manager from engine
        ai_provider_manager = ai_engine.ai_provider_manager
        
        # Initialize productivity modules
        await initialize_productivity_modules(ai_provider_manager)
        
        logger.info("✅ ChoyAI Productivity Server initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize server: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down ChoyAI Productivity Server...")
    
    try:
        if ai_engine:
            await ai_engine.shutdown()
        logger.info("✅ Server shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="ChoyAI Productivity Suite",
    description="Cost-effective AI productivity platform with 14 modules",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(productivity_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ChoyAI Productivity Suite",
        "version": "1.0.0",
        "description": "Cost-effective AI productivity platform with 14 modules",
        "features": [
            "Chat & Voice AI",
            "Smart Task Management", 
            "AI-Enhanced Notes",
            "Intelligent Calendar",
            "Cost-Optimized 3-LLM Routing",
            "Local Storage with Cloud Sync",
            "14 Productivity Modules"
        ],
        "cost_target": "$5-20/month operational costs",
        "providers": ["OpenAI GPT-4o", "Anthropic Claude", "DeepSeek"],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "productivity": "/api/v1/productivity",
            "modules": "/api/v1/productivity/modules"
        }
    }


@app.get("/api/v1/info")
async def api_info():
    """API information and capabilities"""
    if ai_provider_manager is None:
        raise HTTPException(status_code=503, detail="AI providers not initialized")
    
    # Get provider analytics
    analytics = await ai_provider_manager.get_cost_analytics()
    
    return {
        "ai_providers": {
            "available": list(ai_provider_manager.providers.keys()),
            "cost_optimization": analytics.get("cost_optimization_enabled", False),
            "daily_cost": analytics.get("daily_cost", 0.0),
            "cost_target": "Under $20/day"
        },
        "productivity_modules": {
            "total": 14,
            "implemented": ["tasks", "notes", "calendar", "chat_voice"],
            "categories": [
                "Core Communication (Chat, Voice, Messaging)",
                "Task Management (Tasks, Notes, Calendar)",
                "Information (News, Mail, Finance)",
                "Advanced (Trading, Project Management, Online Agent)"
            ]
        },
        "cost_strategy": {
            "orchestration": "OpenAI GPT-4o",
            "coding_priority": "Anthropic Claude > DeepSeek > OpenAI",
            "documents_priority": "Anthropic Claude > OpenAI",
            "backup_provider": "DeepSeek (ultra-low-cost)",
            "local_storage": "SQLite + Vector embeddings"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "message": str(exc) if settings.debug else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI server
    uvicorn.run(
        "app.main_server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
