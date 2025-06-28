# config.py
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class Config(BaseSettings):
    # Database Configuration
    DB_DIR: Path = Path(__file__).parent / "db"
    PROMPTS_DIR: Path = BASE_DIR / "prompts"  # Add this line
    CORE_MEMORY_DB: Path = DB_DIR / "core_memory.db"
    USER_MEMORY_DB: Path = DB_DIR / "user_memories.db"

    # Telegram Configuration
    telegram_bot_token: SecretStr = Field(
        ...,
        env="TELEGRAM_BOT_TOKEN",
        description="Telegram Bot API token"
    )
    
    # Logging Configuration
    log_level: LogLevel = Field(
        "INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL)"
    )
    
    # Database Paths
    base_dir: Path = Path(__file__).parent
    core_memory_db: Path = Field(
        default=base_dir / "db/core_memory.db",
        description="Core memory database path"
    )
    user_memory_db: Path = Field(
        default=base_dir / "db/user_memories.db",
        description="User memory database path"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

config = Config()
