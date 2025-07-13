"""
Telegram Bot Handler for Choy AI Brain

Handles all Telegram bot interactions and routes them to the AI engine
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError

from app.core.ai_engine import ChoyAIEngine
from app.config.settings import settings
from app.utils.security import rate_limiter, user_validator


class TelegramBotHandler:
    """Telegram bot integration handler"""
    
    def __init__(self, ai_engine: ChoyAIEngine):
        self.ai_engine = ai_engine
        self.logger = logging.getLogger(__name__)
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        
        # Performance tracking
        self.message_count = 0
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Initialize the Telegram bot"""
        self.logger.info("🤖 Initializing Telegram Bot...")
        
        try:
            # Create application
            self.application = (
                Application.builder()
                .token(settings.telegram_bot_token.get_secret_value())
                .build()
            )
            
            self.bot = self.application.bot
            
            # Add handlers
            await self._add_handlers()
            
            self.logger.info("✅ Telegram Bot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Telegram Bot: {e}")
            raise
    
    async def _add_handlers(self):
        """Add command and message handlers"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.handle_start))
        app.add_handler(CommandHandler("help", self.handle_help))
        app.add_handler(CommandHandler("persona", self.handle_persona))
        app.add_handler(CommandHandler("personas", self.handle_list_personas))
        app.add_handler(CommandHandler("remember", self.handle_remember))
        app.add_handler(CommandHandler("recall", self.handle_recall))
        app.add_handler(CommandHandler("memories", self.handle_memories))
        app.add_handler(CommandHandler("forget", self.handle_forget))
        app.add_handler(CommandHandler("bio", self.handle_bio))
        app.add_handler(CommandHandler("myid", self.handle_myid))
        app.add_handler(CommandHandler("stats", self.handle_stats))
        app.add_handler(CommandHandler("history", self.handle_history))
        
        # AI Provider commands
        app.add_handler(CommandHandler("providers", self.handle_providers))
        app.add_handler(CommandHandler("switchai", self.handle_switch_ai))
        app.add_handler(CommandHandler("aitask", self.handle_ai_task))
        
        # User Profile commands
        app.add_handler(CommandHandler("profile", self.handle_profile))
        app.add_handler(CommandHandler("analytics", self.handle_analytics))
        app.add_handler(CommandHandler("fullhistory", self.handle_full_history))
        
        # Message handler (for regular chat)
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )
        
        # Error handler
        app.add_error_handler(self.handle_error)
        
        self.logger.debug("📝 Added all Telegram handlers")
    
    async def start(self):
        """Start the Telegram bot"""
        self.logger.info("🚀 Starting Telegram Bot...")
        
        try:
            if settings.telegram_use_polling:
                # Use polling for development
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES
                )
                self.logger.info("📡 Telegram Bot started with polling")
            else:
                # Use webhooks for production
                webhook_url = settings.telegram_webhook_url
                if not webhook_url:
                    raise ValueError("Webhook URL required for production mode")
                
                await self.application.initialize()
                await self.application.start()
                await self.application.bot.set_webhook(webhook_url)
                self.logger.info(f"🌐 Telegram Bot started with webhook: {webhook_url}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start Telegram Bot: {e}")
            raise
    
    async def stop(self):
        """Stop the Telegram bot"""
        self.logger.info("🛑 Stopping Telegram Bot...")
        
        try:
            if self.application:
                if settings.telegram_use_polling:
                    await self.application.updater.stop()
                else:
                    await self.application.bot.delete_webhook()
                
                await self.application.stop()
                await self.application.shutdown()
                
            self.logger.info("✅ Telegram Bot stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping Telegram Bot: {e}")

    # ===== COMMAND HANDLERS =====
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_msg = f"""
🧠 **Welcome to Choy AI Brain, {user.first_name}!**

I'm your intelligent personal assistant with long-term memory and multiple personalities.

**Available Commands:**
• `/persona <n>` - Switch AI personality
• `/personas` - List available personalities  
• `/remember <key> <value>` - Save a memory
• `/recall <key>` - Retrieve a memory
• `/memories` - List all your memories
• `/forget <key>` - Delete a memory
• `/bio <text>` - Set your biography
• `/history` - View conversation history
• `/stats` - View AI statistics
• `/myid` - Show your user info
• `/help` - Show this help message

**Current Personalities:**
🎭 **choy** - Confident, strategic, direct
🤖 **stark** - Tech genius, sarcastic, innovative  
🌹 **rose** - Warm, empathetic, supportive

Just start chatting with me naturally! I'll remember our conversations and provide personalized assistance.
"""
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
        
        # Log new user
        self.logger.info(f"👋 New user started: {user.id} (@{user.username})")
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_msg = """
🧠 **Choy AI Brain - Help Guide**

**Basic Usage:**
Just chat with me naturally! I understand context and remember our conversations.

**Memory System:**
• I automatically remember important details from our chats
• Use `/remember` to explicitly save key information
• Use `/recall` to retrieve specific memories
• Use `/memories` to see all stored memories

**Personality System:**
• Switch between different AI personalities using `/persona`
• Each personality has unique traits and response styles
• Your personality preference is remembered

**Commands:**
• `/start` - Welcome message and overview
• `/help` - This help guide
• `/persona <n>` - Switch personality (choy, stark, rose)
• `/personas` - List all available personalities
• `/remember <key> <value> [context]` - Save memory
• `/recall <key>` - Get specific memory
• `/memories` - List all memories
• `/forget <key>` - Delete a memory
• `/bio <text>` - Set your biography
• `/history [limit]` - View conversation history
• `/stats` - View AI performance statistics
• `/myid` - Show your user information

**AI Provider Commands:**
• `/providers` - Show available AI providers and status
• `/switchai <task> <provider>` - Switch AI provider for tasks
• `/aitask <task> <message>` - Force specific task type

**User Profile Commands:**
• `/profile` - View your AI-generated profile
• `/analytics` - View conversation analytics and insights
• `/fullhistory [limit] [days]` - View detailed conversation history

**Available Task Types:**
• `conversation` - General chat
• `technical` - Programming and tech questions
• `creative` - Writing and creative tasks
• `analysis` - Deep analysis and research
• `research` - Information gathering
• `coding` - Code generation
• `problem` - Problem solving
• `emotional` - Emotional support
• `summary` - Summarization tasks
• `translate` - Translation tasks

**Tips:**
• Be specific when saving memories for better organization
• Try different personalities for different types of conversations
• I learn from our interactions to provide better responses over time
• Use different AI providers for specialized tasks

Need help with something specific? Just ask me!
"""
        
        await update.message.reply_text(help_msg, parse_mode='Markdown')
    
    @rate_limiter
    @user_validator
    async def handle_persona(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /persona command"""
        user_id = str(update.effective_user.id)
        args = context.args
        
        if not args:
            # List available personas
            personas = await self.ai_engine.persona_manager.get_all_personas_summary()
            
            response = "🎭 **Available Personas:**\n\n"
            for persona in personas:
                response += f"**{persona['name']}** - {persona['style']}\n"
                response += f"_{persona['purpose']}_\n\n"
            
            response += "Use `/persona <n>` to switch personalities."
            
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        
        persona_name = args[0].lower()
        result = await self.ai_engine.switch_persona(user_id, persona_name, "telegram")
        
        if result["success"]:
            persona = result["persona"]
            response = f"""
🎭 **Switched to {persona['name'].title()} persona!**

**Style:** {persona['style']}
**Purpose:** {persona['purpose']}

{persona.get('description', '')}
"""
        else:
            response = f"❌ {result['error']}"
            if 'available_personas' in result:
                response += f"\n\nAvailable: {', '.join(result['available_personas'])}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_list_personas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /personas command"""
        personas = await self.ai_engine.persona_manager.get_all_personas_summary()
        
        response = "🎭 **All Available Personas:**\n\n"
        for persona in personas:
            response += f"**{persona['display_name']}** (`{persona['name']}`)\n"
            response += f"Style: _{persona['style']}_\n"
            response += f"Purpose: {persona['purpose']}\n\n"
        
        response += "Use `/persona <n>` to switch to any personality."
        
        await update.message.reply_text(response, parse_mode='Markdown')

    # AI Provider commands
    async def handle_providers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /providers command"""
        providers_info = await self.ai_engine.get_providers_status()
        
        response = "🤖 **Available AI Providers:**\n\n"
        
        for provider_name, info in providers_info.items():
            status = "✅" if info["available"] else "❌"
            response += f"{status} **{provider_name.title()}**\n"
            response += f"   Status: {info['status']}\n"
            response += f"   Best for: {', '.join(info['strengths'])}\n\n"
        
        response += "\n**Current Provider Assignments:**\n"
        current_assignments = await self.ai_engine.get_current_provider_assignments()
        for task_type, provider in current_assignments.items():
            response += f"• {task_type}: {provider}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')

    # User Profile commands
    async def handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        user_id = str(update.effective_user.id)
        
        try:
            profile = await self.ai_engine.user_profile_manager.get_user_profile(user_id)
            
            if not profile:
                response = """
👤 **User Profile**

No profile data available yet. Chat with me more and I'll automatically build your profile based on our conversations!

**What I track:**
• Personal information (name, age, location, profession)
• Interests and preferences
• Communication patterns
• Conversation topics and sentiment
"""
            else:
                response = f"""
👤 **Your AI-Generated Profile**

**Personal Information:**
• **Name:** {profile.name or 'Not detected'}
• **Age:** {profile.age or 'Not detected'}
• **Location:** {profile.location or 'Not detected'}
• **Profession:** {profile.profession or 'Not detected'}

**Interests:** {', '.join(profile.interests) if profile.interests else 'Learning from conversations...'}

**Communication Style:** {profile.communication_style or 'Analyzing...'}

**Profile Confidence:** {profile.confidence_score:.1%}
**Last Updated:** {profile.updated_at.strftime('%Y-%m-%d %H:%M')}

_This profile is automatically generated from our conversations._
"""
            
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            response = "❌ Error retrieving profile data."
        
        await update.message.reply_text(response, parse_mode='Markdown')

    # Add placeholder for other commands to be implemented
    async def handle_remember(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remember command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_recall(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recall command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_memories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /memories command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_forget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /forget command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_bio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bio command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_myid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myid command"""
        user = update.effective_user
        
        response = f"""
👤 **Your User Information:**

**Telegram ID:** `{user.id}`
**Username:** @{user.username or 'Not set'}
**Name:** {user.full_name}
**Language:** {user.language_code or 'Unknown'}

This ID is used to link your memories and conversations.
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_switch_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /switchai command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_ai_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /aitask command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analytics command"""
        await update.message.reply_text("Command under development...")
    
    async def handle_full_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /fullhistory command"""
        await update.message.reply_text("Command under development...")

    # Message handling
    @rate_limiter
    @user_validator
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular chat messages"""
        user_id = str(update.effective_user.id)
        message = update.message.text
        
        self.message_count += 1
        
        # Set typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        
        try:
            # Process message through AI engine
            result = await self.ai_engine.process_message(
                user_id=user_id,
                message=message,
                platform="telegram"
            )
            
            if result["success"]:
                response = result["response"]
                
                # Log successful interaction
                self.logger.debug(f"💬 Message processed for user {user_id}")
                
            else:
                response = "❌ Sorry, I encountered an issue processing your message. Please try again."
                self.logger.error(f"Failed to process message: {result.get('error')}")
            
        except Exception as e:
            self.logger.error(f"Error processing message from {user_id}: {e}")
            response = "❌ Sorry, I encountered an unexpected error. Please try again."
        
        # Send response
        try:
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            # Fallback without markdown if parsing fails
            await update.message.reply_text(response)
            self.logger.warning(f"Markdown parsing failed: {e}")
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot errors"""
        error = context.error
        
        self.logger.error(f"Telegram bot error: {error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Sorry, something went wrong. Please try again."
                )
            except Exception:
                pass  # Don't log errors for error messages
    
    # Utility methods
    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        uptime = datetime.now() - self.start_time
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "messages_processed": self.message_count,
            "messages_per_hour": self.message_count / max(uptime.total_seconds() / 3600, 1),
            "status": "running" if self.application else "stopped"
        }
