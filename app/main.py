"""
Choy AI Brain - Main Application Entry Point

This is the central AI brain that serves as the hub for all Choy AI modules.
It provides intelligent conversation, long-term memory, and persona-based responses.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.ai_engine import ChoyAIEngine
from app.integrations.telegram.bot_handler import TelegramBotHandler
from app.config.settings import settings
from app.utils.logger import setup_logging


class ChoyAIBrain:
    """Main Choy AI Brain application"""
    
    def __init__(self):
        self.ai_engine = None
        self.telegram_bot = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize all components"""
        self.logger.info(" Initializing Choy AI Brain...")
        
        try:
            # Initialize AI Engine
            self.ai_engine = ChoyAIEngine()
            await self.ai_engine.initialize()
            
            # Initialize Telegram Bot
            self.telegram_bot = TelegramBotHandler(self.ai_engine)
            await self.telegram_bot.initialize()
            
            self.logger.info(" Choy AI Brain initialized successfully!")
            
        except Exception as e:
            self.logger.error(f" Failed to initialize Choy AI Brain: {e}")
            raise
    
    async def start(self):
        """Start the AI Brain"""
        await self.initialize()
        
        self.logger.info(" Starting Choy AI Brain...")
        
        # Start Telegram Bot
        await self.telegram_bot.start()
        
        self.logger.info(" Choy AI Brain is now running!")
        
        # Keep the application running
        try:
            # Wait for termination signal
            stop_event = asyncio.Event()
            
            def signal_handler(signum, frame):
                self.logger.info(" Received termination signal")
                stop_event.set()
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            await stop_event.wait()
            
        except KeyboardInterrupt:
            self.logger.info(" Keyboard interrupt received")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the AI Brain"""
        self.logger.info(" Shutting down Choy AI Brain...")
        
        try:
            if self.telegram_bot:
                await self.telegram_bot.stop()
            
            if self.ai_engine:
                await self.ai_engine.shutdown()
                
            self.logger.info(" Choy AI Brain shutdown complete")
            
        except Exception as e:
            self.logger.error(f" Error during shutdown: {e}")


async def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    # Create and start the AI Brain
    brain = ChoyAIBrain()
    await brain.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Goodbye!")
    except Exception as e:
        print(f" Fatal error: {e}")
        sys.exit(1)
