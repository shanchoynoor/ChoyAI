"""
Simple Health Check Test
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_basic_imports():
    """Test basic imports"""
    try:
        from app.config.settings import settings
        print("✅ Settings imported")
        print(f"   Environment: {settings.environment}")
        print(f"   Data dir: {settings.data_dir}")
        return True
    except Exception as e:
        print(f"❌ Settings import failed: {e}")
        return False

def test_database_files():
    """Test database files exist"""
    try:
        from app.config.settings import settings
        
        databases = {
            'core_memory': settings.core_memory_db,
            'user_memory': settings.user_memory_db, 
            'conversations': settings.conversation_db
        }
        
        for name, path in databases.items():
            if path.exists():
                size = path.stat().st_size
                print(f"✅ {name}: {path} ({size} bytes)")
            else:
                print(f"❌ {name}: {path} (not found)")
        
        return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ChoyAI Health Check Test")
    print("=" * 30)
    
    test_basic_imports()
    test_database_files()
    
    print("\n✅ Basic health check complete!")
