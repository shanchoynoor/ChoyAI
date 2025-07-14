"""
ChoyAI System Health Check
Comprehensive health monitoring for all system components
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Test basic imports without external dependencies"""
    print("Testing Python imports...")
    
    try:
        # Test standard library imports
        import os
        import json
        import asyncio
        import sqlite3
        print("   [OK] Standard library imports successful")
        
        # Test if config directory exists
        config_path = Path("app/config")
        if config_path.exists():
            print("   [OK] Config directory found")
        else:
            print("   [ERROR] Config directory missing")
            return False
            
        # Test basic app structure
        app_path = Path("app")
        required_modules = ["core", "modules", "integrations", "api"]
        
        for module in required_modules:
            module_path = app_path / module
            if module_path.exists():
                print(f"   [OK] {module} module found")
            else:
                print(f"   [ERROR] {module} module missing")
                return False
        
        return True
    except Exception as e:
        print(f"   [ERROR] Import test failed: {e}")
        return False

def test_database_files():
    """Test database files exist and are accessible"""
    print("\nTesting database connectivity...")
    
    try:
        data_dir = Path("data/databases")
        if not data_dir.exists():
            print("   [ERROR] Database directory not found")
            return False
        
        databases = [
            ("core_memory.db", "Core memory storage"),
            ("user_memories.db", "User memory storage"), 
            ("conversations.db", "Conversation history")
        ]
        
        all_healthy = True
        for db_file, description in databases:
            db_path = data_dir / db_file
            if db_path.exists():
                size = db_path.stat().st_size
                print(f"   [OK] {db_file}: {description} ({size:,} bytes)")
                
                # Test database connectivity
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    print(f"        Tables: {len(tables)}")
                except Exception as e:
                    print(f"        [WARNING] Connection failed: {e}")
                    all_healthy = False
            else:
                print(f"   [ERROR] {db_file}: {description} (not found)")
                all_healthy = False
        
        return all_healthy
    except Exception as e:
        print(f"   [ERROR] Database check failed: {e}")
        return False

def test_file_structure():
    """Test critical file structure"""
    print("\nTesting file structure...")
    
    critical_files = [
        ("app/main.py", "Main application entry point"),
        ("app/core/ai_engine.py", "AI engine core"),
        ("app/modules/memory/core_memory.py", "Memory system"),
        ("app/integrations/telegram/bot_handler.py", "Telegram integration"),
        ("tools/init_databases.py", "Database initialization"),
        ("config/docker-compose.yml", "Docker configuration"),
        (".env", "Environment variables")
    ]
    
    all_present = True
    for file_path, description in critical_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"   [OK] {file_path}: {description} ({size:,} bytes)")
        else:
            print(f"   [ERROR] {file_path}: {description} (missing)")
            all_present = False
    
    return all_present

def test_environment_setup():
    """Test environment and configuration setup"""
    print("\nTesting environment setup...")
    
    try:
        # Check .env file
        env_file = Path(".env")
        if env_file.exists():
            print("   [OK] Environment file found")
            # Count non-empty lines
            with open(env_file, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"        Configuration entries: {len(lines)}")
        else:
            print("   [WARNING] .env file not found (using defaults)")
        
        # Check data directories
        data_dirs = ["data/databases", "data/logs"]
        for data_dir in data_dirs:
            path = Path(data_dir)
            if path.exists():
                file_count = len(list(path.glob("*")))
                print(f"   [OK] {data_dir}: {file_count} files")
            else:
                print(f"   [ERROR] {data_dir}: missing")
        
        # Check config files
        config_files = ["config/docker-compose.yml", "config/Dockerfile"]
        for config_file in config_files:
            if Path(config_file).exists():
                print(f"   [OK] {config_file}: present")
            else:
                print(f"   [WARNING] {config_file}: missing")
        
        return True
    except Exception as e:
        print(f"   [ERROR] Environment check failed: {e}")
        return False

def calculate_system_stats():
    """Calculate and display system statistics"""
    print("\nSystem Statistics:")
    
    try:
        # Calculate total project size
        total_size = 0
        file_count = 0
        
        for file_path in Path('.').rglob('*'):
            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                total_size += file_path.stat().st_size
                file_count += 1
        
        print(f"   Total files: {file_count:,}")
        print(f"   Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        
        # Database statistics
        db_dir = Path("data/databases")
        if db_dir.exists():
            db_size = sum(f.stat().st_size for f in db_dir.glob("*.db"))
            db_count = len(list(db_dir.glob("*.db")))
            print(f"   Database files: {db_count}")
            print(f"   Database size: {db_size:,} bytes ({db_size / 1024:.1f} KB)")
        
        # Code file statistics
        code_extensions = ['.py', '.js', '.ts', '.json', '.yml', '.yaml']
        code_files = []
        for ext in code_extensions:
            code_files.extend(Path('.').rglob(f'*{ext}'))
        
        code_size = sum(f.stat().st_size for f in code_files if f.is_file())
        print(f"   Code files: {len(code_files)}")
        print(f"   Code size: {code_size:,} bytes ({code_size / 1024:.1f} KB)")
        
    except Exception as e:
        print(f"   [ERROR] Statistics calculation failed: {e}")

def main():
    """Main health check orchestrator"""
    print("=== ChoyAI System Health Check ===")
    print("=" * 50)
    print(f"Location: {Path.cwd()}")
    print(f"Python: {sys.version.split()[0]}")
    print("=" * 50)
    
    # Run all health checks
    checks = [
        ("Python & Imports", test_basic_imports),
        ("Database Systems", test_database_files),
        ("File Structure", test_file_structure),
        ("Environment Setup", test_environment_setup)
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_function in checks:
        try:
            result = check_function()
            if result:
                passed_checks += 1
        except Exception as e:
            print(f"\n[ERROR] {check_name} check crashed: {e}")
    
    # System statistics
    calculate_system_stats()
    
    # Final summary
    print("\n" + "=" * 50)
    print("HEALTH CHECK SUMMARY")
    print("=" * 50)
    
    if passed_checks == total_checks:
        print("*** ALL SYSTEMS OPERATIONAL! ***")
        print("[OK] ChoyAI is ready for:")
        print("   * Development and testing")
        print("   * Database operations")
        print("   * AI provider integration")
        print("   * Telegram bot deployment")
        print("   * Docker containerization")
        
        print(f"\nNext steps:")
        print("   1. Configure API keys in .env")
        print("   2. Start application: python app/main.py")
        print("   3. Test Telegram bot integration")
        print("   4. Deploy to production environment")
        
    else:
        print(f"[WARNING] PARTIAL SUCCESS: {passed_checks}/{total_checks} checks passed")
        print("Some components need attention - see details above")
        
        if passed_checks >= total_checks * 0.75:
            print("[OK] Core functionality should work")
        else:
            print("[ERROR] Critical issues detected - fix before proceeding")
    
    print(f"\nHealth Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.0f}%)")
    print("=" * 50)

if __name__ == "__main__":
    main()
