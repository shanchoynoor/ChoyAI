#!/usr/bin/env python3
"""
ChoyAI Brain - Complete Setup Script

This script performs initial setup including:
- Database initialization
- Logging configuration
- Directory structure verification
- Environment validation
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_directories():
    """Ensure all required directories exist"""
    print("📁 Setting up directory structure...")
    
    base_dir = Path(__file__).parent.parent
    required_dirs = [
        "data",
        "data/databases", 
        "data/logs",
        "templates/personas",
        "tests",
        "docs"
    ]
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {dir_path}")
    
    print("✅ Directory structure complete!")

def validate_environment():
    """Validate environment configuration"""
    print("🔍 Validating environment...")
    
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print("   ❌ .env file not found")
        env_example = Path(__file__).parent.parent / "config" / ".env.example"
        if env_example.exists():
            print("   📝 Copying .env.example to .env...")
            import shutil
            shutil.copy2(env_example, env_file)
            print("   ✅ .env file created")
        else:
            print("   ❌ .env.example not found - manual setup required")
            return False
    
    # Check for required environment variables
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "DEEPSEEK_API_KEY"
    ]
    
    missing_vars = []
    
    try:
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        for var in required_vars:
            if f"{var}=your_" in env_content or f"{var}=" not in env_content:
                missing_vars.append(var)
    except Exception as e:
        print(f"   ❌ Error reading .env file: {e}")
        return False
    
    if missing_vars:
        print("   ⚠️  Missing required environment variables:")
        for var in missing_vars:
            print(f"      - {var}")
        print("   📝 Please edit .env file with your actual API keys")
        return False
    
    print("✅ Environment validation complete!")
    return True

def test_imports():
    """Test that all major components can be imported"""
    print("🧪 Testing component imports...")
    
    try:
        from app.config.settings import settings
        print("   ✅ Settings")
        
        from app.core.ai_engine import ChoyAIEngine
        print("   ✅ AI Engine")
        
        from app.modules.memory.core_memory import CoreMemoryManager
        print("   ✅ Core Memory")
        
        from app.modules.memory.user_memory import UserMemoryManager
        print("   ✅ User Memory")
        
        from app.modules.personas.persona_manager import PersonaManager
        print("   ✅ Persona Manager")
        
        from app.integrations.telegram.bot_handler import TelegramBotHandler
        print("   ✅ Telegram Bot")
        
        print("✅ All component imports successful!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def setup_logging_system():
    """Initialize the logging system"""
    print("📝 Setting up logging system...")
    
    try:
        from app.utils.logging_config import setup_logging
        
        setup_logging(
            log_level="INFO",
            log_to_file=True,
            enable_json=True
        )
        
        # Test logging
        logger = logging.getLogger("choyai.setup")
        logger.info("ChoyAI Brain setup initiated")
        
        print("✅ Logging system configured!")
        return True
        
    except Exception as e:
        print(f"   ❌ Logging setup failed: {e}")
        return False

def initialize_databases():
    """Initialize all databases"""
    print("🗄️  Initializing databases...")
    
    try:
        from tools.init_databases import initialize_databases
        initialize_databases()
        return True
    except Exception as e:
        print(f"   ❌ Database initialization failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 ChoyAI Brain - Complete Setup")
    print("=" * 50)
    
    success = True
    
    # Step 1: Setup directories
    try:
        setup_directories()
    except Exception as e:
        print(f"❌ Directory setup failed: {e}")
        success = False
    
    # Step 2: Setup logging
    try:
        setup_logging_system()
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
        success = False
    
    # Step 3: Initialize databases
    try:
        initialize_databases()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        success = False
    
    # Step 4: Validate environment
    try:
        env_valid = validate_environment()
        if not env_valid:
            success = False
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        success = False
    
    # Step 5: Test imports
    try:
        imports_ok = test_imports()
        if not imports_ok:
            success = False
    except Exception as e:
        print(f"❌ Import testing failed: {e}")
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 ChoyAI Brain setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Edit .env file with your API keys")
        print("   2. Run: python -m app.main")
        print("   3. Test your Telegram bot")
    else:
        print("❌ Setup completed with errors")
        print("   Please resolve the issues above and run setup again")
        sys.exit(1)

if __name__ == "__main__":
    main()
