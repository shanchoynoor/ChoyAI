"""
Logging Configuration for ChoyAI Brain

This file sets up structured logging with proper formatting and file rotation.
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'persona'):
            log_entry['persona'] = record.persona
        if hasattr(record, 'provider'):
            log_entry['provider'] = record.provider
            
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Add color to level name
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: Path = None,
    max_bytes: int = 50 * 1024 * 1024,  # 50MB
    backup_count: int = 5,
    enable_json: bool = True
) -> None:
    """
    Setup comprehensive logging for ChoyAI Brain
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to files
        log_dir: Directory for log files
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep
        enable_json: Whether to use JSON formatting for files
    """
    
    # Set up log directory
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "data" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    console_formatter = ColoredConsoleFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    if log_to_file:
        # Main application log
        app_log_file = log_dir / "choyai.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(numeric_level)
        
        if enable_json:
            app_formatter = JSONFormatter()
        else:
            app_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
            )
        
        app_handler.setFormatter(app_formatter)
        root_logger.addHandler(app_handler)
        
        # Error-only log
        error_log_file = log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(app_formatter)
        root_logger.addHandler(error_handler)
        
        # AI provider specific log
        ai_log_file = log_dir / "ai_providers.log"
        ai_handler = logging.handlers.RotatingFileHandler(
            ai_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        ai_handler.setLevel(logging.DEBUG)
        ai_handler.setFormatter(app_formatter)
        
        # Only log AI provider messages to this file
        ai_logger = logging.getLogger('app.core.ai_providers')
        ai_logger.addHandler(ai_handler)
        ai_logger.propagate = True
        
        # Memory operations log
        memory_log_file = log_dir / "memory.log"
        memory_handler = logging.handlers.RotatingFileHandler(
            memory_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        memory_handler.setLevel(logging.DEBUG)
        memory_handler.setFormatter(app_formatter)
        
        # Only log memory operations to this file
        memory_logger = logging.getLogger('app.modules.memory')
        memory_logger.addHandler(memory_handler)
        memory_logger.propagate = True
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info(f"🔧 Logging configured - Level: {log_level}, File: {log_to_file}")
    if log_to_file:
        logger.info(f"📁 Log directory: {log_dir}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    user_id: str = None,
    session_id: str = None,
    persona: str = None,
    provider: str = None,
    **kwargs
) -> None:
    """
    Log a message with additional context
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        user_id: User ID for context
        session_id: Session ID for context
        persona: Active persona for context
        provider: AI provider for context
        **kwargs: Additional context fields
    """
    
    # Create a log record with extra context
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    if session_id:
        extra['session_id'] = session_id
    if persona:
        extra['persona'] = persona
    if provider:
        extra['provider'] = provider
    
    extra.update(kwargs)
    
    # Get the appropriate log method
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra)

# Example usage functions
def log_user_action(user_id: str, action: str, details: str = None):
    """Log a user action with context"""
    logger = get_logger('choyai.user_actions')
    log_with_context(
        logger, 'info', f"User action: {action}",
        user_id=user_id,
        action=action,
        details=details
    )

def log_ai_request(user_id: str, provider: str, persona: str, message: str):
    """Log an AI request"""
    logger = get_logger('choyai.ai_requests')
    log_with_context(
        logger, 'info', f"AI request to {provider}",
        user_id=user_id,
        provider=provider,
        persona=persona,
        request_preview=message[:100] + "..." if len(message) > 100 else message
    )

def log_memory_operation(user_id: str, operation: str, key: str = None, success: bool = True):
    """Log a memory operation"""
    logger = get_logger('choyai.memory')
    level = 'info' if success else 'error'
    log_with_context(
        logger, level, f"Memory {operation}",
        user_id=user_id,
        operation=operation,
        memory_key=key,
        success=success
    )

if __name__ == "__main__":
    # Test the logging setup
    setup_logging(log_level="DEBUG")
    
    logger = get_logger("test")
    logger.info("🧪 Testing ChoyAI logging system")
    log_user_action("test_user", "test_action", "Testing logging")
    log_ai_request("test_user", "deepseek", "choy", "Test message for AI")
    log_memory_operation("test_user", "save", "test_key", True)
    
    print("✅ Logging test complete - check data/logs/ directory")
