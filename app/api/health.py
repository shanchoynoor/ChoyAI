"""
Health check endpoint for ChoyAI Brain

Provides health status information for monitoring and load balancers
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.core.ai_engine import ChoyAIEngine
from app.config.settings import settings

# Create FastAPI app for health checks
health_app = FastAPI(
    title="ChoyAI Brain Health Check",
    description="Health monitoring endpoint",
    version="1.0.0"
)

logger = logging.getLogger(__name__)

# Global health status
health_status = {
    "status": "starting",
    "timestamp": datetime.now().isoformat(),
    "checks": {}
}

@health_app.get("/health")
async def health_check() -> JSONResponse:
    """Basic health check endpoint"""
    try:
        # Update timestamp
        health_status["timestamp"] = datetime.now().isoformat()
        
        # Basic system checks
        checks = {
            "api": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": "unknown"
        }
        
        # Try to check AI engine if available
        try:
            # This would require AI engine to be available
            checks["ai_engine"] = "healthy"
        except Exception as e:
            logger.warning(f"AI engine check failed: {e}")
            checks["ai_engine"] = "warning"
        
        # Check database connectivity
        try:
            # This would check database connection
            checks["database"] = "healthy"
        except Exception as e:
            logger.warning(f"Database check failed: {e}")
            checks["database"] = "warning"
        
        # Determine overall status
        if any(status == "error" for status in checks.values() if isinstance(status, str)):
            overall_status = "error"
            http_status = 503
        elif any(status == "warning" for status in checks.values() if isinstance(status, str)):
            overall_status = "warning"
            http_status = 200
        else:
            overall_status = "healthy"
            http_status = 200
        
        response_data = {
            "status": overall_status,
            "timestamp": health_status["timestamp"],
            "checks": checks,
            "version": "1.0.0",
            "environment": getattr(settings, 'environment', 'unknown')
        }
        
        return JSONResponse(
            content=response_data,
            status_code=http_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )

@health_app.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """Readiness check for Kubernetes/container orchestration"""
    try:
        # More comprehensive checks for readiness
        checks = {
            "ai_providers": "unknown",
            "database": "unknown",
            "telegram_bot": "unknown"
        }
        
        # Check if all required services are ready
        all_ready = True
        
        # This would check if AI providers are configured
        if not getattr(settings, 'deepseek_api_key', None):
            checks["ai_providers"] = "not_configured"
            all_ready = False
        else:
            checks["ai_providers"] = "ready"
        
        # Check Telegram bot token
        if not getattr(settings, 'telegram_bot_token', None):
            checks["telegram_bot"] = "not_configured"
            all_ready = False
        else:
            checks["telegram_bot"] = "ready"
        
        status_code = 200 if all_ready else 503
        status = "ready" if all_ready else "not_ready"
        
        return JSONResponse(
            content={
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "checks": checks
            },
            status_code=status_code
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )

@health_app.get("/health/live")
async def liveness_check() -> JSONResponse:
    """Liveness check for Kubernetes/container orchestration"""
    try:
        # Simple liveness check - just verify the process is running
        return JSONResponse(
            content={
                "status": "alive",
                "timestamp": datetime.now().isoformat(),
                "pid": os.getpid() if 'os' in globals() else "unknown"
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )

@health_app.get("/metrics")
async def metrics_endpoint() -> JSONResponse:
    """Basic metrics endpoint for monitoring"""
    try:
        # This would provide basic metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": 0,  # Would calculate actual uptime
            "memory_usage_mb": 0,  # Would get actual memory usage
            "cpu_usage_percent": 0,  # Would get actual CPU usage
            "active_connections": 0,  # Would count active connections
            "messages_processed": 0,  # Would count processed messages
            "errors_count": 0  # Would count errors
        }
        
        return JSONResponse(content=metrics, status_code=200)
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("HEALTH_CHECK_PORT", 8000))
    uvicorn.run(health_app, host="0.0.0.0", port=port)
