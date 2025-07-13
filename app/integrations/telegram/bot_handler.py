"""
Telegram Bot Handler for Choy AI Brain

Handles all Telegram bot interactions and routes them to the AI engine
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
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
• `translate` - Translation tasksime

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
• `/persona <name>` - Switch AI personality
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
• `/persona <name>` - Switch personality (choy, stark, rose)
• `/personas` - List all available personalities
• `/remember <key> <value> [context]` - Save memory
• `/recall <key>` - Get specific memory
• `/memories` - List all memories
• `/forget <key>` - Delete a memory
• `/bio <text>` - Set your biography
• `/history [limit]` - View conversation history
• `/stats` - View AI performance statistics
• `/myid` - Show your user information

**Tips:**
• Be specific when saving memories for better organization
• Try different personalities for different types of conversations
• I learn from our interactions to provide better responses over time

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
            
            response += "Use `/persona <name>` to switch personalities."
            
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
        
        response += "Use `/persona <name>` to switch to any personality."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    @rate_limiter
    async def handle_remember(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remember command"""
        user_id = str(update.effective_user.id)
        args = context.args
        
        if len(args) < 2:
            await update.message.reply_text(
                "📝 **Usage:** `/remember <key> <value> [context]`\n\n"
                "**Example:** `/remember favorite_color blue from profile discussion`"
            )
            return
        
        key = args[0]
        value = args[1]
        context_info = ' '.join(args[2:]) if len(args) > 2 else None
        
        success = await self.ai_engine.save_user_memory(
            user_id=user_id,
            key=key,
            value=value,
            context=context_info
        )
        
        if success:
            response = f"💾 **Memory saved!**\n`{key}` = `{value}`"
            if context_info:
                response += f"\nContext: _{context_info}_"
        else:
            response = "❌ Failed to save memory. Please try again."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_recall(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recall command"""
        user_id = str(update.effective_user.id)
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "🔍 **Usage:** `/recall <key>`\n\n"
                "**Example:** `/recall favorite_color`"
            )
            return
        
        key = args[0]
        memories = await self.ai_engine.get_user_memories(user_id)
        
        # Find matching memory
        memory = next((m for m in memories if m['key'] == key), None)
        
        if memory:
            response = f"🔍 **Memory Found:**\n"
            response += f"`{memory['key']}` = `{memory['value']}`"
            if memory.get('context'):
                response += f"\nContext: _{memory['context']}_"
            if memory.get('created_at'):
                response += f"\nSaved: {memory['created_at']}"
        else:
            response = f"❌ No memory found for key: `{key}`"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_memories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /memories command"""
        user_id = str(update.effective_user.id)
        memories = await self.ai_engine.get_user_memories(user_id, limit=20)
        
        if not memories:
            await update.message.reply_text("📝 You don't have any saved memories yet.")
            return
        
        response = f"📝 **Your Memories ({len(memories)} total):**\n\n"
        
        for memory in memories[:20]:  # Limit to prevent long messages
            response += f"• `{memory['key']}` = `{memory['value']}`"
            if memory.get('context'):
                response += f" _(context: {memory['context']})_"
            response += "\n"
        
        if len(memories) > 20:
            response += f"\n... and {len(memories) - 20} more memories."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_forget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /forget command"""
        # This would be implemented with a delete_memory method in the AI engine
        await update.message.reply_text(
            "🗑️ Memory deletion feature coming soon!\n"
            "For now, you can overwrite memories by using `/remember` with the same key."
        )
    
    async def handle_bio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bio command"""
        user_id = str(update.effective_user.id)
        args = context.args
        
        if not args:
            # Show current bio
            memories = await self.ai_engine.get_user_memories(user_id)
            bio_memory = next((m for m in memories if m['key'] == 'user_bio'), None)
            
            if bio_memory:
                await update.message.reply_text(
                    f"📝 **Your current bio:**\n{bio_memory['value']}"
                )
            else:
                await update.message.reply_text(
                    "📝 **Usage:** `/bio <your biography>`\n\n"
                    "**Example:** `/bio Software engineer who loves AI and coffee`"
                )
            return
        
        bio = ' '.join(args)
        success = await self.ai_engine.save_user_memory(
            user_id=user_id,
            key="user_bio",
            value=bio,
            context="User biography"
        )
        
        if success:
            await update.message.reply_text("✅ **Biography updated successfully!**")
        else:
            await update.message.reply_text("❌ Failed to update biography.")
    
    async def handle_myid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myid command"""
        user = update.effective_user
        
        response = f"""
👤 **Your Information:**

**User ID:** `{user.id}`
**Username:** @{user.username or 'N/A'}
**Name:** {user.full_name}
**First Name:** {user.first_name}
**Last Name:** {user.last_name or 'N/A'}
**Language:** {user.language_code or 'N/A'}
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        stats = await self.ai_engine.get_ai_stats()
        uptime = datetime.now() - self.start_time
        
        response = f"""
📊 **Choy AI Brain Statistics**

**Performance:**
• Messages Processed: {stats['total_messages_processed']:,}
• Persona Switches: {stats['total_personas_switched']:,}
• Average Response Time: {stats['average_response_time']:.2f}s
• Active Conversations: {stats['active_conversations']}

**Memory System:**
• Total Users: {stats['memory_stats']['total_users']:,}
• Total Memories: {stats['memory_stats']['total_memories']:,}
• Total Conversations: {stats['memory_stats']['total_conversations']:,}

**Bot Statistics:**
• Bot Uptime: {str(uptime).split('.')[0]}
• Bot Messages: {self.message_count:,}

**Available Personas:** {', '.join(stats['available_personas'])}
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        user_id = str(update.effective_user.id)
        args = context.args
        limit = int(args[0]) if args and args[0].isdigit() else 10
        
        history = await self.ai_engine.get_conversation_history(user_id, limit)
        
        if not history:
            await update.message.reply_text("📜 No conversation history found.")
            return
        
        response = f"📜 **Recent Conversation History ({len(history)} messages):**\n\n"
        
        for entry in history[-limit:]:  # Show most recent
            timestamp = entry.get('timestamp', 'Unknown time')
            persona = entry.get('persona', 'unknown')
            user_msg = entry.get('user_message', '')[:100]  # Truncate long messages
            ai_msg = entry.get('ai_response', '')[:100]
            
            response += f"**{timestamp}** (as {persona})\n"
            response += f"You: _{user_msg}_\n"
            response += f"AI: _{ai_msg}_\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    @rate_limiter
    @user_validator
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular chat messages"""
        user_id = str(update.effective_user.id)
        message = update.message.text
        
        self.message_count += 1
        
        try:
            # Show typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
            
            # Process message through AI engine
            response = await self.ai_engine.process_message(
                user_id=user_id,
                message=message,
                platform="telegram",
                context={
                    'username': update.effective_user.username,
                    'first_name': update.effective_user.first_name,
                    'chat_id': update.effective_chat.id
                }
            )
            
            # Send response
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error processing message from user {user_id}: {e}")
            await update.message.reply_text(
                "⚠️ I encountered an error processing your message. Please try again."
            )
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot errors"""
        self.logger.error(f"Telegram bot error: {context.error}")
        
        if update and update.message:
            try:
                await update.message.reply_text(
                    "⚠️ An unexpected error occurred. The issue has been logged."
                )
            except TelegramError:
                pass  # Don't fail on error handling
    
    async def handle_providers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available AI providers and their status"""
        user_id = str(update.effective_user.id)
        
        # Validate user
        if not user_validator(user_id):
            await update.message.reply_text("❌ Access denied")
            return
            
        try:
            provider_status = await self.ai_engine.get_ai_provider_status()
            
            message = "🤖 *AI Provider Status*\n\n"
            
            for provider_name, status in provider_status.items():
                if status.get('healthy', False):
                    status_icon = "✅"
                    models = status.get('models', [])
                    supported_tasks = status.get('supported_tasks', [])
                    
                    message += f"{status_icon} *{provider_name.title()}*\n"
                    message += f"   Models: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}\n"
                    message += f"   Tasks: {len(supported_tasks)} supported\n"
                    
                    metrics = status.get('metrics', {})
                    if metrics:
                        success_count = metrics.get('success_count', 0)
                        error_count = metrics.get('error_count', 0)
                        total = success_count + error_count
                        if total > 0:
                            success_rate = (success_count / total) * 100
                            message += f"   Success Rate: {success_rate:.1f}%\n"
                else:
                    status_icon = "❌"
                    error = status.get('error', 'Unknown error')
                    message += f"{status_icon} *{provider_name.title()}*\n"
                    message += f"   Error: {error}\n"
                    
                message += "\n"
            
            message += "\n💡 Use `/switchai <task> <provider>` to change providers"
            message += "\n📝 Use `/aitask <task> <message>` to force a specific task type"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error getting provider status: {e}")
            await update.message.reply_text("❌ Error retrieving provider status")
    
    async def handle_switch_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Switch AI provider for a specific task type"""
        user_id = str(update.effective_user.id)
        
        # Validate user
        if not user_validator(user_id):
            await update.message.reply_text("❌ Access denied")
            return
        
        if len(context.args) != 2:
            await update.message.reply_text(
                "Usage: `/switchai <task_type> <provider>`\n\n"
                "Task types: conversation, technical, creative, analysis, research, etc.\n"
                "Providers: deepseek, openai, anthropic, xai, gemini"
            )
            return
            
        task_type_name = context.args[0].lower()
        provider_name = context.args[1].lower()
        
        try:
            from app.core.ai_providers import TaskType
            
            # Map string to TaskType enum
            task_type_map = {
                'conversation': TaskType.CONVERSATION,
                'technical': TaskType.TECHNICAL,
                'creative': TaskType.CREATIVE,
                'analysis': TaskType.ANALYSIS,
                'research': TaskType.RESEARCH,
                'coding': TaskType.CODE_GENERATION,
                'code': TaskType.CODE_GENERATION,
                'problem': TaskType.PROBLEM_SOLVING,
                'emotional': TaskType.EMOTIONAL_SUPPORT,
                'summary': TaskType.SUMMARIZATION,
                'translate': TaskType.TRANSLATION
            }
            
            task_type = task_type_map.get(task_type_name)
            if not task_type:
                await update.message.reply_text(
                    f"❌ Unknown task type: {task_type_name}\n"
                    f"Available: {', '.join(task_type_map.keys())}"
                )
                return
            
            success = await self.ai_engine.switch_ai_provider(task_type, provider_name)
            
            if success:
                await update.message.reply_text(
                    f"✅ Switched {task_type_name} tasks to {provider_name.title()}"
                )
            else:
                await update.message.reply_text(
                    f"❌ Failed to switch to {provider_name}. Provider may not be available."
                )
                
        except Exception as e:
            self.logger.error(f"Error switching provider: {e}")
            await update.message.reply_text("❌ Error switching AI provider")
    
    async def handle_ai_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process message with specific task type"""
        user_id = str(update.effective_user.id)
        
        # Apply rate limiting
        if not rate_limiter(user_id):
            await update.message.reply_text("⏰ Please wait before sending another message")
            return
            
        # Validate user
        if not user_validator(user_id):
            await update.message.reply_text("❌ Access denied")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: `/aitask <task_type> <your message>`\n\n"
                "Examples:\n"
                "• `/aitask creative Write me a short story`\n"
                "• `/aitask technical Explain how async works in Python`\n"
                "• `/aitask analysis Compare these two approaches`"
            )
            return
            
        task_type_name = context.args[0].lower()
        message = " ".join(context.args[1:])
        
        try:
            from app.core.ai_providers import TaskType
            
            # Map string to TaskType enum
            task_type_map = {
                'conversation': TaskType.CONVERSATION,
                'technical': TaskType.TECHNICAL,
                'creative': TaskType.CREATIVE,
                'analysis': TaskType.ANALYSIS,
                'research': TaskType.RESEARCH,
                'coding': TaskType.CODE_GENERATION,
                'code': TaskType.CODE_GENERATION,
                'problem': TaskType.PROBLEM_SOLVING,
                'emotional': TaskType.EMOTIONAL_SUPPORT,
                'summary': TaskType.SUMMARIZATION,
                'translate': TaskType.TRANSLATION
            }
            
            task_type = task_type_map.get(task_type_name)
            if not task_type:
                await update.message.reply_text(
                    f"❌ Unknown task type: {task_type_name}\n"
                    f"Available: {', '.join(task_type_map.keys())}"
                )
                return
            
            # Process message with specific task type
            response = await self.ai_engine.process_message_with_provider(
                user_id=user_id,
                message=message,
                task_type=task_type,
                platform="telegram",
                context={
                    'username': update.effective_user.username,
                    'first_name': update.effective_user.first_name,
                    'chat_id': update.effective_chat.id,
                    'forced_task_type': task_type_name
                }
            )
            
            # Send response with task type indicator
            response_with_header = f"🎯 *{task_type_name.title()} Task*\n\n{response}"
            await update.message.reply_text(response_with_header, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error processing AI task: {e}")
            await update.message.reply_text("❌ Error processing your task request")

# Export the main class
__all__ = ["TelegramBotHandler"]
