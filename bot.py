import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackContext
)
from db.core_memory import CoreMemory
from db.user_memory import UserMemory
from persona_manager import PersonaManager
from utils.logger import setup_logging
from utils.deepseek_api import DeepSeekAPI
from config import Config

# ===== [1] Add the switch_persona function here =====
async def switch_persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args or ['choy']
    
    persona_name = args[0].lower()
    persona = {
        'choy': {
            'name': 'choy',
            'style': 'Confident, strategic, no-fluff',
            'purpose': 'Primary assistant persona'
        },
        'stark': {
            'name': 'stark',
            'style': 'Tech genius, sarcastic',
            'purpose': 'Technical discussions'
        }
    }.get(persona_name)
    
    if not persona:
        await update.message.reply_text(f"Persona '{persona_name}' not found")
        return
    
    await update.message.reply_text(
        f"✅ Switched to persona: {persona['name']}\n"
 f"Style: {persona['style']}\n"
        f"Purpose: {persona['purpose']}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the bot!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"You said: {update.message.text}")



# Initialize components
setup_logging()
core_memory = CoreMemory()
user_memory = UserMemory()
persona_manager = PersonaManager()

# Active personas cache
active_personas = {}  # {user_id: persona_name}

# ──────────────────────────────────────────────────────────────
# 💬 Telegram Handlers
def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message with available commands"""
    user = update.effective_user
    welcome_msg = f"""
🤖 Welcome to Choy AI, {user.first_name}!

Available commands:
/persona - Switch between personalities
/remember - Save a memory
/recall - Retrieve a memory
/memories - List all your memories
/bio - Set your biography
/myid - Show your user info

Current personas:
- choy (default)
- stark
- rose
- sherlock
- joker
- hermione
- harley
"""
    update.message.reply_text(welcome_msg)

def handle_persona(update: Update, context: CallbackContext) -> None:
    """Handle persona switching"""
    user_id = update.effective_user.id
    args = context.args
    
    if not args:
        # List available personas
        personas = persona_manager.list_personas()
        response = "Available personas:\n" + "\n".join(
            f"- {p['name']}: {p['style']}" for p in personas
        )
        update.message.reply_text(response)
        return
    
    persona_name = args[0].lower()
    persona = persona_manager.get_persona(persona_name)
    
    if persona:
        active_personas[user_id] = persona_name
        update.message.reply_text(
            f"🎭 Switched to {persona_name} persona:\n"
            f"Style: {persona['style']}\n"
            f"Purpose: {persona['purpose']}"
        )
    else:
        update.message.reply_text(f"⚠️ Persona '{persona_name}' not found")

def handle_remember(update: Update, context: CallbackContext) -> None:
    """Handle memory saving"""
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 2:
        update.message.reply_text(
            "Usage: /remember <key> <value> [context]\n"
            "Example: /remember favorite_color blue seen in profile"
        )
        return
    
    key = args[0]
    value = args[1]
    context = ' '.join(args[2:]) if len(args) > 2 else None
    
    if user_memory.save_memory(user_id, key, value, context):
        update.message.reply_text(f"💾 Saved memory: {key} = {value}")
    else:
        update.message.reply_text("❌ Failed to save memory")

def handle_recall(update: Update, context: CallbackContext) -> None:
    """Handle memory recall"""
    user_id = update.effective_user.id
    args = context.args
    
    if not args:
        update.message.reply_text("Usage: /recall <key>")
        return
    
    key = args[0]
    value = user_memory.recall_memory(user_id, key)
    
    if value:
        update.message.reply_text(f"🔍 {key}: {value}")
    else:
        update.message.reply_text(f"ℹ️ No memory found for '{key}'")

def handle_memories(update: Update, context: CallbackContext) -> None:
    """List all user memories"""
    user_id = update.effective_user.id
    memories = user_memory.get_memories(user_id)
    
    if not memories:
        update.message.reply_text("You have no saved memories yet.")
        return
    
    response = "📝 Your memories:\n" + "\n".join(
        f"- {mem['key']}: {mem['value']}" + 
        (f" (Context: {mem['context']})" if mem.get('context') else "")
        for mem in memories
    )
    update.message.reply_text(response[:4000])  # Telegram message length limit

def handle_bio(update: Update, context: CallbackContext) -> None:
    """Set user biography"""
    user_id = update.effective_user.id
    bio = ' '.join(context.args) if context.args else None
    
    if not bio:
        current_bio = user_memory.get_user_bio(user_id)
        if current_bio:
            update.message.reply_text(f"📝 Current bio: {current_bio}")
        else:
            update.message.reply_text("Usage: /bio <your biography text>")
        return
    
    if user_memory.update_user_bio(user_id, bio):
        update.message.reply_text("✅ Biography updated successfully!")
    else:
        update.message.reply_text("❌ Failed to update biography")

def handle_myid(update: Update, context: CallbackContext) -> None:
    """Show user info"""
    user = update.effective_user
    update.message.reply_text(
        f"👤 Your ID: {user.id}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"Name: {user.full_name}"
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle regular messages with active persona"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Get active persona
    persona_name = active_personas.get(user_id, 'choy')
    persona = persona_manager.get_persona(persona_name)
    
    if not persona:
        update.message.reply_text("⚠️ Persona configuration error")
        return
    
    # Get user context
    user = user_memory.get_or_create_user(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )
    memories = user_memory.get_memories(user_id)
    
    # Generate response
    response = generate_response(
        persona_system_prompt=persona['system_prompt'],
        user_input=text,
        memories=memories,
        user=user
    )
    
    # Send response
    update.message.reply_text(response)
    
    # Log conversation
    user_memory.log_conversation(user_id, persona_name, text, response)

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        update.message.reply_text("⚠️ An error occurred. Please try again later.")

# ──────────────────────────────────────────────────────────────
# 🤖 AI Integration
def generate_response(persona_system_prompt: str, user_input: str, 
                     memories: list, user: dict) -> str:
    """Generate response using DeepSeek API"""
    # Implement your actual API call here
    try:
        # Build the full prompt with memories and user context
        prompt = f"""System: {persona_system_prompt}
        
User Context:
- Name: {user.get('first_name', '')} {user.get('last_name', '')}
- Username: @{user.get('username', '')}
- Bio: {user.get('bio', 'Not provided')}

Memories:
{format_memories(memories)}

User: {user_input}"""
        
        # This is where you'd call the actual API
        # response = requests.post(...)
        # return response.text
        
        # For now, return a placeholder
        return f"[Response as {user.get('active_persona', 'choy')}] {user_input}"
    
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return "⚠️ I encountered an error processing your message."

def format_memories(memories: list) -> str:
    """Format memories for prompt"""
    if not memories:
        return "No memories available"
    return "\n".join(
        f"- {mem['key']}: {mem['value']}" + 
        (f" (Context: {mem['context']})" if mem.get('context') else "")
        for mem in memories
    )

# ──────────────────────────────────────────────────────────────
# 🚀 Main Application
def main():
    """Start the bot"""
    updater = Updater(Config.TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("persona", handle_persona))
    dp.add_handler(CommandHandler("remember", handle_remember))
    dp.add_handler(CommandHandler("recall", handle_recall))
    dp.add_handler(CommandHandler("memories", handle_memories))
    dp.add_handler(CommandHandler("bio", handle_bio))
    dp.add_handler(CommandHandler("myid", handle_myid))
    application.add_handler(CommandHandler("persona", switch_persona))
    dp.add_handler(MessageHandler(Filters.text & ~filters.command, handle_message))
    dp.add_error_handler(error_handler)

    logger.info("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()