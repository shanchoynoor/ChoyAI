"""
Enhanced logging configuration for Choy AI Brain

Provides structured logging with multiple handlers and formatters
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from pythonjsonlogger import jsonlogger

from app.config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        
        return super().format(record)


class ChoyLoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter with context"""
    
    def process(self, msg, kwargs):
        # Add context information
        context = self.extra.get('context', {})
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            msg = f"[{context_str}] {msg}"
        
        return msg, kwargs


def setup_logging():
    """Setup comprehensive logging for Choy AI Brain"""
    
    # Create logs directory
    logs_dir = settings.logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    if settings.log_to_file:
        # Main application log file (rotating)
        app_log_file = logs_dir / "app.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        app_formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(funcName)-15s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        app_handler.setLevel(getattr(logging, settings.log_level))
        root_logger.addHandler(app_handler)
        
        # Error log file (only errors and critical)
        error_log_file = logs_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        error_formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(pathname)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # JSON log file for structured logging
        json_log_file = logs_dir / "app.json"
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        json_formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(funcName)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        json_handler.setFormatter(json_formatter)
        json_handler.setLevel(getattr(logging, settings.log_level))
        root_logger.addHandler(json_handler)
        
        # Security log file
        security_log_file = logs_dir / "security.log"
        security_handler = logging.handlers.RotatingFileHandler(
            security_log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        security_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        security_handler.setFormatter(security_formatter)
        
        # Create security logger
        security_logger = logging.getLogger("security")
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False
        
        # Integration log file
        integration_log_file = logs_dir / "integration.log"
        integration_handler = logging.handlers.RotatingFileHandler(
            integration_log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        integration_formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        integration_handler.setFormatter(integration_formatter)
        
        # Create integration logger
        integration_logger = logging.getLogger("integration")
        integration_logger.addHandler(integration_handler)
        integration_logger.setLevel(logging.INFO)
        integration_logger.propagate = False
    
    # Configure specific loggers
    
    # Telegram bot logger
    telegram_logger = logging.getLogger("telegram")
    telegram_logger.setLevel(logging.INFO)
    
    # HTTP client loggers (reduce noise)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # AI/API loggers
    ai_logger = logging.getLogger("ai")
    ai_logger.setLevel(logging.INFO)
    
    # Memory system logger
    memory_logger = logging.getLogger("memory")
    memory_logger.setLevel(logging.INFO)
    
    # Performance logger
    perf_logger = logging.getLogger("performance")
    perf_logger.setLevel(logging.INFO)
    
    # Log startup message
    main_logger = logging.getLogger("choy.brain")
    main_logger.info("🚀 Choy AI Brain logging system initialized")
    main_logger.info(f"📝 Log level: {settings.log_level}")
    main_logger.info(f"📁 Logs directory: {logs_dir}")
    
    return main_logger


def get_logger(name: str, context: dict = None) -> logging.Logger:
    """Get a logger with optional context"""
    logger = logging.getLogger(name)
    
    if context:
        return ChoyLoggerAdapter(logger, {"context": context})
    
    return logger


def log_performance(func_name: str, duration: float, context: dict = None):
    """Log performance metrics"""
    perf_logger = logging.getLogger("performance")
    
    message = f"Function '{func_name}' executed in {duration:.3f}s"
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        message += f" | Context: {context_str}"
    
    if duration > 5.0:  # Log slow operations as warnings
        perf_logger.warning(f"SLOW: {message}")
    else:
        perf_logger.info(message)


def log_memory_usage(operation: str, before_mb: float, after_mb: float):
    """Log memory usage changes"""
    memory_logger = logging.getLogger("memory")
    diff_mb = after_mb - before_mb
    
    message = f"Memory usage | Operation: {operation} | Before: {before_mb:.1f}MB | After: {after_mb:.1f}MB | Change: {diff_mb:+.1f}MB"
    
    if diff_mb > 100:  # Log large memory increases as warnings
        memory_logger.warning(f"HIGH MEMORY: {message}")
    else:
        memory_logger.info(message)


def log_integration_activity(service: str, operation: str, status: str, details: str = ""):
    """Log integration service activity"""
    integration_logger = logging.getLogger("integration")
    
    message = f"{service.upper()}: {operation} | Status: {status}"
    if details:
        message += f" | Details: {details}"
    
    if status.lower() in ["error", "failed", "timeout"]:
        integration_logger.error(message)
    elif status.lower() in ["warning", "retry"]:
        integration_logger.warning(message)
    else:
        integration_logger.info(message)


def log_ai_interaction(persona: str, user_id: str, message_length: int, response_time: float):
    """Log AI interaction metrics"""
    ai_logger = logging.getLogger("ai")
    
    ai_logger.info(
        f"AI Interaction | Persona: {persona} | User: {user_id} | "
        f"Message length: {message_length} chars | Response time: {response_time:.3f}s"
    )


def log_system_activity(action: str, metadata: dict = None):
    """Log system activity - simplified version for testing"""
    logger = logging.getLogger("system_activity")
    metadata_str = f" | {metadata}" if metadata else ""
    logger.info(f"System Activity: {action}{metadata_str}")


# Performance decorator
def performance_monitor(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        import time
        from functools import wraps
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                name = operation_name or f"{func.__module__}.{func.__name__}"
                log_performance(name, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                name = operation_name or f"{func.__module__}.{func.__name__}"
                log_performance(name, duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Export utilities
__all__ = [
    "setup_logging",
    "get_logger", 
    "log_performance",
    "log_memory_usage",
    "log_integration_activity",
    "log_ai_interaction",
    "performance_monitor",
    "ChoyLoggerAdapter"
]
