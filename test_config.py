#!/usr/bin/env python3
"""
Test ChoyAI Configuration
Quick test to verify settings are working
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_config():
    """Test configuration loading"""
    print("🧪 Testing ChoyAI Configuration")
    print("=" * 35)
    
    try:
        from app.config.settings import settings
        print("✅ Settings imported successfully!")
        
        # Test key configuration values
        print(f"   Environment: {settings.environment}")
        print(f"   Log level: {settings.log_level}")
        print(f"   Data directory: {settings.data_dir}")
        print(f"   Database directory: {settings.database_dir}")
        
        # Test persona configuration
        print(f"   Available personas: {settings.available_personas}")
        print(f"   Default persona: {settings.default_persona}")
        
        # Test optional lists
        if settings.allowed_users:
            print(f"   Allowed users: {len(settings.allowed_users)} users")
        else:
            print("   Allowed users: All users allowed")
        
        # Test API keys (without revealing them)
        api_keys = []
        if settings.deepseek_api_key and str(settings.deepseek_api_key) != "your_deepseek_api_key_here":
            api_keys.append("DeepSeek")
        if settings.openai_api_key and str(settings.openai_api_key) != "your_openai_api_key_here":
            api_keys.append("OpenAI")
        if settings.anthropic_api_key and str(settings.anthropic_api_key) != "your_anthropic_api_key_here":
            api_keys.append("Anthropic")
        if settings.telegram_bot_token and str(settings.telegram_bot_token) != "your_telegram_bot_token_here":
            api_keys.append("Telegram")
        
        print(f"   Configured APIs: {', '.join(api_keys) if api_keys else 'None (using defaults)'}")
        
        print("\n✅ Configuration test passed!")
        print("🚀 ChoyAI is ready to start!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        print("\n🔧 To fix this issue:")
        print("1. Check your .env file for syntax errors")
        print("2. Ensure comma-separated lists don't have quotes")
        print("3. Example: AVAILABLE_PERSONAS=choy,stark,rose")
        print("4. Not: AVAILABLE_PERSONAS=\"choy,stark,rose\"")
        return False

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
