"""
Legacy bot.py - Backwards compatibility

This file maintains compatibility with the old structure while redirecting to the new system
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.main import main

if __name__ == "__main__":
    print("🔄 Starting Choy AI Brain via legacy entry point...")
    print("📝 For new deployments, use: python -m app.main")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
