"""
Simple System Check
"""

import os
import sqlite3
from pathlib import Path

def check_directories():
    """Check if required directories exist"""
    print("📁 Checking directories...")
    
    required_dirs = [
        "app",
        "app/core", 
        "app/modules",
        "app/integrations",
        "data",
        "data/databases",
        "data/logs",
        "config",
        "templates",
        "tools"
    ]
    
    missing = []
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"   ✅ {directory}")
        else:
            print(f"   ❌ {directory}")
            missing.append(directory)
    
    return len(missing) == 0

def check_databases():
    """Check database files"""
    print("\n🗄️  Checking databases...")
    
    db_dir = Path("data/databases")
    if not db_dir.exists():
        print(f"   ❌ Database directory not found: {db_dir}")
        return False
    
    databases = [
        "core_memory.db",
        "user_memories.db", 
        "conversations.db"
    ]
    
    all_exist = True
    for db_name in databases:
        db_path = db_dir / db_name
        if db_path.exists():
            size = db_path.stat().st_size
            print(f"   ✅ {db_name} ({size} bytes)")
            
            # Test database connectivity
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                print(f"      Tables: {len(tables)}")
            except Exception as e:
                print(f"      ⚠️  Connection test failed: {e}")
        else:
            print(f"   ❌ {db_name} (not found)")
            all_exist = False
    
    return all_exist

def check_config_files():
    """Check configuration files"""
    print("\n⚙️  Checking configuration...")
    
    config_files = [
        ".env",
        "config/.env.example",
        "config/Dockerfile",
        "config/docker-compose.yml"
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"   ✅ {config_file}")
        else:
            print(f"   ❌ {config_file}")
            all_exist = False
    
    return all_exist

def check_code_files():
    """Check key code files"""
    print("\n🐍 Checking code files...")
    
    key_files = [
        "app/main.py",
        "app/core/ai_engine.py",
        "app/modules/memory/core_memory.py",
        "app/integrations/telegram/bot_handler.py",
        "tools/init_databases.py",
        "tools/setup.py"
    ]
    
    all_exist = True
    for code_file in key_files:
        if Path(code_file).exists():
            print(f"   ✅ {code_file}")
        else:
            print(f"   ❌ {code_file}")
            all_exist = False
    
    return all_exist

def main():
    """Main system check"""
    print("🔍 ChoyAI System Check")
    print("=" * 30)
    
    checks = [
        ("Directory Structure", check_directories),
        ("Database Files", check_databases), 
        ("Configuration Files", check_config_files),
        ("Code Files", check_code_files)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"   ❌ {check_name} check failed: {e}")
            all_passed = False
    
    print("\n" + "=" * 30)
    if all_passed:
        print("🎉 All system checks passed!")
        print("\n📋 System is ready for:")
        print("   • Database operations")
        print("   • Logging functionality") 
        print("   • Configuration management")
        print("   • Application startup")
    else:
        print("⚠️  Some checks failed - see details above")
    
    print(f"\n📁 Current working directory: {Path.cwd()}")
    print(f"🗂️  Data directory size: {sum(f.stat().st_size for f in Path('data').rglob('*') if f.is_file())} bytes")

if __name__ == "__main__":
    main()
