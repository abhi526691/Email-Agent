"""
Telegram bot handler for controlling the email agent.
Handles incoming commands like /start, /stop, and /status.
"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.agent_controller import start_agent, stop_agent, get_agent_status

class TelegramBotHandler:
    """Handles Telegram bot commands for agent control"""
    
    def __init__(self, token: str, authorized_chat_id: str):
        self.token = token
        self.authorized_chat_id = authorized_chat_id
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        # Check if user is authorized
        if str(update.effective_chat.id) != self.authorized_chat_id:
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        result = start_agent()
        
        if result["success"]:
            await update.message.reply_text(
                "✅ Email Agent Started!\n\n"
                "The agent is now monitoring your emails and will send notifications for important messages."
            )
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        # Check if user is authorized
        if str(update.effective_chat.id) != self.authorized_chat_id:
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        result = stop_agent()
        
        if result["success"]:
            await update.message.reply_text(
                "🛑 Email Agent Stopping...\n\n"
                "The agent will stop after completing the current cycle."
            )
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        # Check if user is authorized
        if str(update.effective_chat.id) != self.authorized_chat_id:
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        status_info = get_agent_status()
        
        status_emoji = "🟢" if status_info["status"] == "Running" else "🔴"
        
        await update.message.reply_text(
            f"{status_emoji} *Agent Status*\n\n"
            f"Status: {status_info['status']}\n"
            f"Last Run: {status_info['last_run']}",
            parse_mode="Markdown"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        # Check if user is authorized
        if str(update.effective_chat.id) != self.authorized_chat_id:
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        help_text = (
            "🤖 *Email Agent Bot Commands*\n\n"
            "/start - Start the email agent\n"
            "/stop - Stop the email agent\n"
            "/status - Check agent status\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
    
    async def start_bot(self):
        """Start the Telegram bot"""
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        
        # Start polling in the background
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        print("[OK] Telegram bot started and listening for commands...")
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            print("[STOPPED] Telegram bot stopped")

# Global bot instance
bot_handler = None

def get_bot_handler():
    """Get or create the bot handler instance"""
    global bot_handler
    if bot_handler is None:
        bot_handler = TelegramBotHandler(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    return bot_handler
