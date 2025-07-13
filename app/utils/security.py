"""
Security utilities for Choy AI Brain

Provides rate limiting, user validation, and security decorators
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Dict, Optional, Set
from collections import defaultdict, deque

from app.config.settings import settings


class RateLimiter:
    """Rate limiting for user requests"""
    
    def __init__(self, max_requests: int = None, window_seconds: int = 60):
        self.max_requests = max_requests or settings.rate_limit_per_minute
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.logger = logging.getLogger(__name__)
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limit"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests outside the window
        while user_requests and user_requests[0] <= now - self.window_seconds:
            user_requests.popleft()
        
        # Check if under limit
        if len(user_requests) >= self.max_requests:
            self.logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Add current request
        user_requests.append(now)
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        """Get remaining requests for user"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        while user_requests and user_requests[0] <= now - self.window_seconds:
            user_requests.popleft()
        
        return max(0, self.max_requests - len(user_requests))


class UserValidator:
    """User validation and access control"""
    
    def __init__(self):
        self.allowed_users: Optional[Set[str]] = None
        self.blocked_users: Set[str] = set()
        self.logger = logging.getLogger(__name__)
        
        # Load allowed users from settings
        if settings.allowed_users:
            self.allowed_users = set(settings.allowed_users)
    
    def is_user_allowed(self, user_id: str) -> bool:
        """Check if user is allowed to use the bot"""
        # Check if user is blocked
        if user_id in self.blocked_users:
            self.logger.warning(f"Blocked user attempted access: {user_id}")
            return False
        
        # Check allowed users list (if configured)
        if self.allowed_users and user_id not in self.allowed_users:
            self.logger.warning(f"Unauthorized user attempted access: {user_id}")
            return False
        
        return True
    
    def block_user(self, user_id: str):
        """Block a user"""
        self.blocked_users.add(user_id)
        self.logger.info(f"User blocked: {user_id}")
    
    def unblock_user(self, user_id: str):
        """Unblock a user"""
        self.blocked_users.discard(user_id)
        self.logger.info(f"User unblocked: {user_id}")


# Global instances
rate_limiter_instance = RateLimiter()
user_validator_instance = UserValidator()


def rate_limiter(func):
    """Decorator for rate limiting"""
    @wraps(func)
    async def wrapper(self, update, context):
        user_id = str(update.effective_user.id)
        
        if not rate_limiter_instance.is_allowed(user_id):
            remaining = rate_limiter_instance.get_remaining_requests(user_id)
            await update.message.reply_text(
                f"⚠️ **Rate limit exceeded!**\n"
                f"Please wait before sending more messages.\n"
                f"Remaining requests: {remaining}"
            )
            return
        
        return await func(self, update, context)
    
    return wrapper


def user_validator(func):
    """Decorator for user validation"""
    @wraps(func)
    async def wrapper(self, update, context):
        user_id = str(update.effective_user.id)
        
        if not user_validator_instance.is_user_allowed(user_id):
            await update.message.reply_text(
                "⚠️ **Access Denied**\n"
                "You don't have permission to use this bot."
            )
            return
        
        return await func(self, update, context)
    
    return wrapper


def admin_required(func):
    """Decorator for admin-only commands"""
    @wraps(func)
    async def wrapper(self, update, context):
        user_id = str(update.effective_user.id)
        
        # Check if user is admin (you can customize this logic)
        admin_users = getattr(settings, 'admin_users', [])
        if user_id not in admin_users:
            await update.message.reply_text(
                "⚠️ **Admin Required**\n"
                "This command requires administrator privileges."
            )
            return
        
        return await func(self, update, context)
    
    return wrapper


def security_log(action: str, user_id: str, details: str = ""):
    """Log security-related events"""
    logger = logging.getLogger("security")
    logger.info(f"SECURITY: {action} | User: {user_id} | Details: {details}")


# Export utilities
__all__ = [
    "RateLimiter", 
    "UserValidator", 
    "rate_limiter", 
    "user_validator", 
    "admin_required",
    "security_log"
]
