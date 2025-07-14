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
        
        # User onboarding state tracking
        self.user_onboarding_state = {}
        
    def get_time_based_greeting(self) -> str:
        """Get appropriate greeting based on current time"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "Good morning"
        elif 12 <= current_hour < 17:
            return "Good afternoon"
        elif 17 <= current_hour < 21:
            return "Good evening"
        else:
            return "Good night"
    
    async def check_user_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """Check if user has completed onboarding questions"""
        try:
            # Check if user profile manager is available
            if not self.ai_engine.user_profile_manager:
                return {
                    "completed": False,
                    "next_question": "city",
                    "questions_answered": 0
                }
                
            # Check if user profile exists and has basic info
            profile = await self.ai_engine.user_profile_manager.get_user_profile(user_id)
            
            if not profile:
                return {
                    "completed": False,
                    "next_question": "city",
                    "questions_answered": 0
                }
            
            # Check which questions have been answered
            questions_answered = 0
            next_question = None
            
            if not profile.location:
                next_question = "city"
            else:
                questions_answered += 1
                if not profile.age:
                    next_question = "age"
                else:
                    questions_answered += 1
                    if not profile.profession:
                        next_question = "profession"
                    else:
                        questions_answered += 1
            
            return {
                "completed": questions_answered == 3,
                "next_question": next_question,
                "questions_answered": questions_answered
            }
            
        except Exception as e:
            self.logger.error(f"Error checking onboarding status: {e}")
            return {
                "completed": False,
                "next_question": "city",
                "questions_answered": 0
            }
    
    async def get_onboarding_question(self, question_type: str) -> str:
        """Get the next onboarding question"""
        questions = {
            "city": "🏙️ Which city do you live in?",
            "age": "🎂 How old are you?",
            "profession": "💼 What do you do for work or study?"
        }
        return questions.get(question_type, "")
    
    async def process_onboarding_answer(self, user_id: str, message: str, question_type: str) -> bool:
        """Process user's answer to onboarding question"""
        try:
            message = message.strip()
            
            # Validate message is not empty
            if not message:
                return False
            
            # Extract information based on question type
            if question_type == "city":
                # Accept any non-empty string as city
                await self.ai_engine.user_profile_manager.update_user_info(
                    user_id=user_id,
                    city=message,
                    platform="telegram"
                )
                return True
                
            elif question_type == "age":
                # Extract age information - be more flexible
                age_str = ''.join(filter(str.isdigit, message))
                if age_str:
                    age = int(age_str)
                    if 1 <= age <= 150:  # Reasonable age range
                        await self.ai_engine.user_profile_manager.update_user_info(
                            user_id=user_id,
                            age=age,
                            platform="telegram"
                        )
                        return True
                # If no valid age found, still accept the raw message
                await self.ai_engine.user_profile_manager.update_user_info(
                    user_id=user_id,
                    age=None,  # Store as None, but mark as answered
                    platform="telegram"
                )
                return True
                
            elif question_type == "profession":
                # Accept any non-empty string as profession
                await self.ai_engine.user_profile_manager.update_user_info(
                    user_id=user_id,
                    profession=message,
                    platform="telegram"
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error processing onboarding answer: {e}")
            # Even if there's an error, we should try to continue the onboarding
            return True
    
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
        user_id = str(user.id)
        
        # Get time-based greeting
        time_greeting = self.get_time_based_greeting()
        
        # Check onboarding status
        onboarding_status = await self.check_user_onboarding_status(user_id)
        
        # Personalized greeting with time
        greeting_msg = f"Hi {user.first_name}! {time_greeting}! 👋"
        
        if not onboarding_status["completed"]:
            # User needs onboarding
            next_question = onboarding_status["next_question"]
            question_text = await self.get_onboarding_question(next_question)
            
            welcome_msg = f"""
{greeting_msg}

� **Welcome to Choy AI!**

I'm your intelligent personal assistant with long-term memory and multiple personalities. Before we start chatting, I'd love to get to know you better!

Let me ask you a few quick questions to personalize our conversations:

{question_text}
"""
            
            # Track onboarding state
            self.user_onboarding_state[user_id] = {
                "active": True,
                "next_question": next_question,
                "questions_answered": onboarding_status["questions_answered"]
            }
            
        else:
            # User has completed onboarding
            welcome_msg = f"""
{greeting_msg}

� **Welcome back to Choy AI!**

I'm your intelligent personal assistant with long-term memory and multiple personalities.

**Available Commands:**
• `/persona <name>` - Switch AI personality (choy, stark, rose)
• `/personas` - List available personalities  
• `/remember <key> <value>` - Save a memory
• `/recall <key>` - Retrieve a memory
• `/memories` - List all your memories
• `/profile` - View your AI-generated profile
• `/providers` - Show AI provider status
• `/help` - Show complete help guide

**Current Personalities:**
🎭 **choy** - Confident, strategic, direct (default)
🤖 **stark** - Tech genius, sarcastic, innovative  
🌹 **rose** - Warm, empathetic, supportive

Just start chatting with me naturally! I'll remember our conversations and provide personalized assistance.
"""
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
        
        # Log new user
        self.logger.info(f"👋 New user started: {user.id} (@{user.username}) - Onboarding: {onboarding_status['completed']}")
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = str(update.effective_user.id)
        
        # Check if user has completed onboarding
        onboarding_status = await self.check_user_onboarding_status(user_id)
        
        if not onboarding_status["completed"]:
            help_msg = """
� **Choy AI - Getting Started**

Hi! I noticed you haven't completed the initial setup yet. 

To get started, please use `/start` and I'll ask you a few quick questions:
• Which city do you live in?
• How old are you? 
• What do you do for work or study?

This helps me provide more personalized assistance! After that, you'll have access to all my features.
"""
        else:
            help_msg = """
� **Choy AI - Help Guide**

**Basic Usage:**
Just chat with me naturally! I understand context and remember our conversations.

**Personality System:**
• I start with the **Choy** persona by default (confident, strategic, direct)
• Switch personalities anytime with `/persona <name>`:
  - `/persona choy` - Confident, strategic, direct
  - `/persona stark` - Tech genius, sarcastic, innovative
  - `/persona rose` - Warm, empathetic, supportive

**Core Commands:**
• `/start` - Welcome message and setup
• `/help` - This help guide
• `/persona <name>` - Switch personality (choy, stark, rose)
• `/personas` - List all available personalities
• `/myid` - Show your user information

**Memory System:**
• I automatically remember important details from our chats
• `/remember <key> <value>` - Save specific information
• `/recall <key>` - Retrieve saved information
• `/memories` - List all your saved memories
• `/forget <key>` - Delete a memory

**AI Provider Commands:**
• `/providers` - Show available AI providers and status
• `/switchai <task> <provider>` - Switch AI provider for specific tasks
• `/aitask <task> <message>` - Force a specific task type

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

**Examples:**
• "Hi, how are you?" - Normal conversation
• `/persona stark` - Switch to tech genius personality
• `/remember birthday April 15` - Save important date
• `/aitask creative Write a poem about space` - Force creative task

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
            if not self.ai_engine.user_profile_manager:
                await update.message.reply_text("❌ User profile system not available")
                return
                
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
        user = update.effective_user
        message = update.message.text
        
        self.message_count += 1
        
        # Set typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        
        try:
            # Check if user is in onboarding process
            if user_id in self.user_onboarding_state and self.user_onboarding_state[user_id]["active"]:
                await self._handle_onboarding_response(update, user_id, message)
                return
            
            # Check if user needs onboarding
            onboarding_status = await self.check_user_onboarding_status(user_id)
            if not onboarding_status["completed"]:
                # Start onboarding process
                next_question = onboarding_status["next_question"]
                question_text = await self.get_onboarding_question(next_question)
                
                response = f"""
Before we continue chatting, I'd love to get to know you better! 

{question_text}
"""
                
                # Track onboarding state
                self.user_onboarding_state[user_id] = {
                    "active": True,
                    "next_question": next_question,
                    "questions_answered": onboarding_status["questions_answered"]
                }
                
                await update.message.reply_text(response, parse_mode='Markdown')
                return
            
            # Regular message processing for completed onboarding users
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
    
    async def _handle_onboarding_response(self, update: Update, user_id: str, message: str):
        """Handle user responses during onboarding"""
        try:
            user = update.effective_user
            onboarding_state = self.user_onboarding_state[user_id]
            current_question = onboarding_state["next_question"]
            
            # Process the answer - always try to accept it
            success = await self.process_onboarding_answer(user_id, message, current_question)
            
            # Always move forward unless there's a critical error
            if success or len(message.strip()) > 0:
                # Update questions answered count
                onboarding_state["questions_answered"] += 1
                
                # Determine next question
                next_question = None
                if current_question == "city":
                    next_question = "age"
                elif current_question == "age":
                    next_question = "profession"
                
                if next_question:
                    # Ask next question
                    question_text = await self.get_onboarding_question(next_question)
                    response = f"Great! Thanks for sharing. 😊\n\n{question_text}"
                    
                    # Update state
                    onboarding_state["next_question"] = next_question
                    
                else:
                    # Onboarding complete
                    response = f"""
Perfect! Thank you for sharing those details with me. 🎉

Now I can provide you with more personalized assistance! I'm Choy AI, and by default, I have a confident, strategic, and direct personality. 

You can switch to different personalities anytime:
• `/persona stark` - Tech genius, sarcastic, innovative
• `/persona rose` - Warm, empathetic, supportive  
• `/persona choy` - Back to confident, strategic, direct

What would you like to chat about, {user.first_name}? I'm here to help with anything you need! 💭
"""
                    
                    # Mark onboarding as complete
                    self.user_onboarding_state[user_id]["active"] = False
                
            else:
                # Only show error if message is completely empty
                response = "I didn't quite understand your answer. Could you please provide that information again?"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error handling onboarding response: {e}")
            await update.message.reply_text("Sorry, I encountered an error. Please try again.")
    
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
