#!/usr/bin/env python3
"""
Choy AI Brain Setup Script

This script helps set up the Choy AI Brain environment
"""

import os
import sys
import subprocess
from pathlib import Path


def print_banner():
    """Print setup banner"""
    print("""
🧠 Choy AI Brain Setup
=====================

Setting up your intelligent personal assistant with long-term memory
and multiple personalities.
""")


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Error: Python 3.11+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example_path.exists():
        print("❌ Error: .env.example file not found")
        return False
    
    # Copy .env.example to .env
    try:
        with open(env_example_path, 'r') as source:
            content = source.read()
        
        with open(env_path, 'w') as target:
            target.write(content)
        
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys before running the bot")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories"""
    directories = [
        "data/databases",
        "data/logs",
        "data/personas"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True


def check_required_files():
    """Check if required files exist"""
    required_files = [
        "requirements.txt",
        ".env.example",
        "app/main.py",
        "data/personas/choy.yaml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    return True


def print_next_steps():
    """Print next steps for the user"""
    print("""
🎉 Setup Complete!

Next Steps:
1. Edit the .env file with your API keys:
   - TELEGRAM_BOT_TOKEN (from @BotFather on Telegram)
   - DEEPSEEK_API_KEY (from DeepSeek platform)

2. Run the AI Brain:
   python main.py

3. Start chatting with your bot on Telegram!

📚 Documentation:
   - README.md for detailed usage instructions
   - .env.example for all configuration options
   - data/personas/ for personality customization

🆘 Need Help?
   - Check the logs in data/logs/ for debugging
   - Review the project structure in project_structure.md
   - Open an issue if you encounter problems

Happy chatting with your AI assistant! 🤖
""")


def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check required files
    if not check_required_files():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
