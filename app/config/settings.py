"""
Choy AI Brain - Configuration Settings

Centralized configuration management using Pydantic Settings
"""

import os
from pathlib import Path
from typing import Literal, Optional, List
from pydantic import Field, SecretStr, validator
from pydantic_settings import BaseSettings

# Type definitions
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
Environment = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Main application settings"""
    
    # ===== ENVIRONMENT =====
    environment: Environment = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment"
    )
    
    debug: bool = Field(
        default=True,
        env="DEBUG", 
        description="Enable debug mode"
    )
    
    # ===== PATHS =====
    base_dir: Path = Field(
        default=Path(__file__).parent.parent.parent,
        description="Base project directory"
    )
    
    data_dir: Path = Field(
        default=None,
        description="Data storage directory"
    )
    
    logs_dir: Path = Field(
        default=None,
        description="Logs directory"
    )
    
    @validator('data_dir', pre=True, always=True)
    def set_data_dir(cls, v, values):
        if v is None:
            return values['base_dir'] / 'data'
        return v
    
    @validator('logs_dir', pre=True, always=True)
    def set_logs_dir(cls, v, values):
        if v is None:
            return values['data_dir'] / 'logs'
        return v
    
    # ===== LOGGING =====
    log_level: LogLevel = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    log_to_file: bool = Field(
        default=True,
        env="LOG_TO_FILE",
        description="Enable logging to file"
    )
    
    log_max_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        env="LOG_MAX_SIZE",
        description="Maximum log file size in bytes"
    )
    
    log_backup_count: int = Field(
        default=5,
        env="LOG_BACKUP_COUNT",
        description="Number of backup log files to keep"
    )
    
    # ===== DATABASE =====
    database_dir: Path = Field(
        default=None,
        description="Database directory"
    )
    
    core_memory_db: Path = Field(
        default=None,
        description="Core memory database path"
    )
    
    user_memory_db: Path = Field(
        default=None,
        description="User memory database path"
    )
    
    conversation_db: Path = Field(
        default=None,
        description="Conversation database path"
    )
    
    @validator('database_dir', pre=True, always=True)
    def set_database_dir(cls, v, values):
        if v is None:
            return values['data_dir'] / 'databases'
        return v
    
    @validator('core_memory_db', pre=True, always=True)
    def set_core_memory_db(cls, v, values):
        if v is None:
            return values['database_dir'] / 'core_memory.db'
        return v
    
    @validator('user_memory_db', pre=True, always=True)
    def set_user_memory_db(cls, v, values):
        if v is None:
            return values['database_dir'] / 'user_memories.db'
        return v
    
    @validator('conversation_db', pre=True, always=True)
    def set_conversation_db(cls, v, values):
        if v is None:
            return values['database_dir'] / 'conversations.db'
        return v
    
    # ===== TELEGRAM INTEGRATION =====
    telegram_bot_token: SecretStr = Field(
        ...,
        env="TELEGRAM_BOT_TOKEN",
        description="Telegram Bot API token"
    )
    
    telegram_webhook_url: Optional[str] = Field(
        default=None,
        env="TELEGRAM_WEBHOOK_URL",
        description="Telegram webhook URL for production"
    )
    
    telegram_use_polling: bool = Field(
        default=True,
        env="TELEGRAM_USE_POLLING",
        description="Use polling instead of webhooks"
    )
    
    # ===== AI CONFIGURATION =====
    default_persona: str = Field(
        default="choy",
        env="DEFAULT_PERSONA",
        description="Default AI persona"
    )
    
    max_conversation_history: int = Field(
        default=50,
        env="MAX_CONVERSATION_HISTORY",
        description="Maximum conversation history to keep in memory"
    )
    
    max_response_length: int = Field(
        default=2000,
        env="MAX_RESPONSE_LENGTH",
        description="Maximum AI response length"
    )
    
    response_timeout: float = Field(
        default=30.0,
        env="RESPONSE_TIMEOUT",
        description="AI response timeout in seconds"
    )
    
    # ===== DEEPSEEK API =====
    deepseek_api_key: SecretStr = Field(
        ...,
        env="DEEPSEEK_API_KEY",
        description="DeepSeek API key"
    )
    
    deepseek_model: str = Field(
        default="deepseek-chat",
        env="DEEPSEEK_MODEL",
        description="DeepSeek model to use"
    )
    
    deepseek_max_tokens: int = Field(
        default=1000,
        env="DEEPSEEK_MAX_TOKENS",
        description="Maximum tokens for DeepSeek responses"
    )
    
    deepseek_temperature: float = Field(
        default=0.7,
        env="DEEPSEEK_TEMPERATURE",
        description="Temperature for DeepSeek responses"
    )
    
    # ===== MEMORY CONFIGURATION =====
    memory_retention_days: int = Field(
        default=365,
        env="MEMORY_RETENTION_DAYS",
        description="Days to retain user memories"
    )
    
    max_memories_per_user: int = Field(
        default=1000,
        env="MAX_MEMORIES_PER_USER",
        description="Maximum memories per user"
    )
    
    enable_semantic_search: bool = Field(
        default=True,
        env="ENABLE_SEMANTIC_SEARCH",
        description="Enable semantic search for memories"
    )
    
    # ===== PERSONA CONFIGURATION =====
    personas_dir: Path = Field(
        default=None,
        description="Personas configuration directory"
    )
    
    @validator('personas_dir', pre=True, always=True)
    def set_personas_dir(cls, v, values):
        if v is None:
            return values['data_dir'] / 'personas'
        return v
    
    available_personas: List[str] = Field(
        default=[
            "choy", "stark", "rose", "sherlock", 
            "joker", "hermione", "harley"
        ],
        description="List of available personas"
    )
    
    @validator('available_personas', pre=True, always=True)
    def parse_available_personas(cls, v, values):
        # Check environment variable directly
        import os
        env_value = os.getenv('AVAILABLE_PERSONAS')
        if env_value:
            # Parse comma-separated string
            return [persona.strip() for persona in env_value.split(',') if persona.strip()]
        # Return default if not set
        if isinstance(v, str):
            return [persona.strip() for persona in v.split(',') if persona.strip()]
        return v or [
            "choy", "stark", "rose", "sherlock", 
            "joker", "hermione", "harley"
        ]
    
    # ===== SECURITY =====
    secret_key: SecretStr = Field(
        default="choy-ai-secret-key-change-in-production",
        env="SECRET_KEY",
        description="Secret key for encryption"
    )
    
    allowed_users: Optional[List[str]] = Field(
        default=None,
        description="List of allowed user IDs (if None, all users allowed)"
    )
    
    @validator('allowed_users', pre=True, always=True)
    def parse_allowed_users(cls, v, values):
        # Check environment variable directly
        import os
        env_value = os.getenv('ALLOWED_USERS')
        if env_value and env_value.strip():
            # Parse comma-separated string
            return [user_id.strip() for user_id in env_value.split(',') if user_id.strip()]
        # Return None if not set or empty
        if isinstance(v, str) and v.strip():
            return [user_id.strip() for user_id in v.split(',') if user_id.strip()]
        return None
    
    rate_limit_per_minute: int = Field(
        default=20,
        env="RATE_LIMIT_PER_MINUTE",
        description="Rate limit per user per minute"
    )
    
    # ===== PERFORMANCE =====
    max_concurrent_requests: int = Field(
        default=10,
        env="MAX_CONCURRENT_REQUESTS",
        description="Maximum concurrent requests"
    )
    
    cache_ttl: int = Field(
        default=300,  # 5 minutes
        env="CACHE_TTL",
        description="Cache TTL in seconds"
    )
    
    # ===== INTEGRATIONS (Future) =====
    # Google Workspace
    google_credentials_file: Optional[Path] = Field(
        default=None,
        env="GOOGLE_CREDENTIALS_FILE",
        description="Google service account credentials file"
    )
    
    # Meta/Facebook
    meta_app_id: Optional[str] = Field(
        default=None,
        env="META_APP_ID",
        description="Meta/Facebook App ID"
    )
    
    meta_app_secret: Optional[SecretStr] = Field(
        default=None,
        env="META_APP_SECRET",
        description="Meta/Facebook App Secret"
    )
    
    # Notion
    notion_token: Optional[SecretStr] = Field(
        default=None,
        env="NOTION_TOKEN",
        description="Notion integration token"
    )
    
    # ClickUp
    clickup_token: Optional[SecretStr] = Field(
        default=None,
        env="CLICKUP_TOKEN",
        description="ClickUp API token"
    )
    
    # ===== MONITORING =====
    enable_metrics: bool = Field(
        default=True,
        env="ENABLE_METRICS",
        description="Enable metrics collection"
    )
    
    metrics_port: int = Field(
        default=8080,
        env="METRICS_PORT",
        description="Metrics endpoint port"
    )
    
    health_check_interval: int = Field(
        default=60,
        env="HEALTH_CHECK_INTERVAL",
        description="Health check interval in seconds"
    )
    
    # ===== AI PROVIDER APIS =====
    
    # OpenAI/ChatGPT
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key for ChatGPT"
    )
    
    openai_model: str = Field(
        default="gpt-4",
        env="OPENAI_MODEL",
        description="OpenAI model to use"
    )
    
    openai_max_tokens: int = Field(
        default=4000,
        env="OPENAI_MAX_TOKENS",
        description="Maximum tokens for OpenAI responses"
    )
    
    openai_temperature: float = Field(
        default=0.7,
        env="OPENAI_TEMPERATURE",
        description="Temperature for OpenAI responses"
    )
    
    # Anthropic Claude
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None,
        env="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude"
    )
    
    anthropic_model: str = Field(
        default="claude-3-sonnet-20240229",
        env="ANTHROPIC_MODEL",
        description="Anthropic model to use"
    )
    
    anthropic_max_tokens: int = Field(
        default=4000,
        env="ANTHROPIC_MAX_TOKENS",
        description="Maximum tokens for Anthropic responses"
    )
    
    anthropic_temperature: float = Field(
        default=0.7,
        env="ANTHROPIC_TEMPERATURE",
        description="Temperature for Anthropic responses"
    )
    
    # xAI Grok
    xai_api_key: Optional[SecretStr] = Field(
        default=None,
        env="XAI_API_KEY",
        description="xAI API key for Grok"
    )
    
    xai_model: str = Field(
        default="grok-beta",
        env="XAI_MODEL",
        description="xAI model to use"
    )
    
    xai_max_tokens: int = Field(
        default=4000,
        env="XAI_MAX_TOKENS",
        description="Maximum tokens for xAI responses"
    )
    
    xai_temperature: float = Field(
        default=0.7,
        env="XAI_TEMPERATURE",
        description="Temperature for xAI responses"
    )
    
    # Google Gemini
    gemini_api_key: Optional[SecretStr] = Field(
        default=None,
        env="GEMINI_API_KEY",
        description="Google Gemini API key"
    )
    
    gemini_model: str = Field(
        default="gemini-pro",
        env="GEMINI_MODEL",
        description="Gemini model to use"
    )
    
    gemini_max_tokens: int = Field(
        default=4000,
        env="GEMINI_MAX_TOKENS",
        description="Maximum tokens for Gemini responses"
    )
    
    gemini_temperature: float = Field(
        default=0.7,
        env="GEMINI_TEMPERATURE",
        description="Temperature for Gemini responses"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.database_dir,
            self.personas_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


# Create global settings instance
settings = Settings()

# Ensure directories exist
settings.create_directories()

# Export settings
__all__ = ["settings", "Settings"]
