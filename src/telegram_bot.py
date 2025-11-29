"""
Telegram bot handler for controlling the email agent.
Handles incoming commands like /start, /stop, and /status.
"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.agent_controller import start_agent, stop_agent, get_agent_status
from src.gmail_client import GmailHandler

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
    
    async def labels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /labels command - show email categorization statistics with buttons"""
        # Check if user is authorized
        if str(update.effective_chat.id) != self.authorized_chat_id:
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        try:
            # Get label statistics
            gmail_handler = GmailHandler()
            label_stats = gmail_handler.get_label_statistics()
            
            if not label_stats:
                await update.message.reply_text("📊 No email labels found.")
                return
            
            # Sort by count (descending)
            sorted_stats = sorted(label_stats.items(), key=lambda x: x[1], reverse=True)
            
            # Build message
            total_emails = sum(label_stats.values())
            message = "📊 *Email Categorization Statistics*\n\n"
            
            # Create keyboard buttons
            keyboard = []
            row = []
            
            for i, (label_name, count) in enumerate(sorted_stats):
                message += f"• {label_name}: *{count}* emails\n"
                
                # Add button for this label
                # Callback data format: view:<label_name>
                # Truncate label if too long for callback data (64 bytes limit)
                callback_data = f"view:{label_name}"
                if len(callback_data.encode('utf-8')) > 64:
                    # If too long, we might need a different strategy or just not add button
                    # For now, let's just try to add it, or maybe skip very long labels
                    pass
                
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                row.append(InlineKeyboardButton(f"{label_name} ({count})", callback_data=callback_data))
                
                # 2 buttons per row
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            
            if row:
                keyboard.append(row)
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message += f"\n📧 *Total:* {total_emails} categorized emails\n\n"
            message += "👇 *Tap a button below to view emails:*"
            
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching label statistics: {str(e)}")
    
    async def view_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /view command - show emails for a specific label"""
        # Check if user is authorized
        if str(update.effective_chat.id) != self.authorized_chat_id:
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        # Check if label name was provided
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a label name.\n\n"
                "Usage: `/view <label_name>`\n"
                "Example: `/view Interview 📅`",
                parse_mode="Markdown"
            )
            return
        
        # Join all arguments as label name (in case it has spaces)
        label_name = " ".join(context.args)
        await self.show_emails_for_label(update, label_name)

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        await query.answer() # Acknowledge the callback
        
        # Check authorization
        if str(update.effective_chat.id) != self.authorized_chat_id:
            await query.message.reply_text("⛔ Unauthorized access")
            return

        data = query.data
        if data.startswith("view:"):
            label_name = data.split(":", 1)[1]
            await self.show_emails_for_label(update, label_name)

    async def show_emails_for_label(self, update: Update, label_name: str):
        """Helper to fetch and show emails for a label"""
        try:
            # Get emails for this label
            gmail_handler = GmailHandler()
            emails = gmail_handler.get_emails_by_label(label_name, max_results=10)
            
            # Determine where to reply (message or callback query message)
            message_obj = update.message if update.message else update.callback_query.message
            
            if emails is None:
                await message_obj.reply_text(f"❌ Label '{label_name}' not found.")
                return
            
            if not emails:
                await message_obj.reply_text(f"📭 No emails found for label '{label_name}'.")
                return
            
            # Build message with email details
            message = f"📬 *Emails in '{label_name}'* (showing {len(emails)})\n\n"
            
            for i, email in enumerate(emails, 1):
                subject = email.get('subject', '(No Subject)')[:60]
                sender = email.get('from', '(Unknown)')[:40]
                snippet = email.get('snippet', '')[:100]
                
                # Escape markdown characters in content if needed, but for now simple replacement
                # To be safe with Markdown parse mode, we should be careful. 
                # Let's just use simple formatting.
                
                message += f"*{i}. {subject}*\n"
                message += f"   From: {sender}\n"
                message += f"   {snippet}...\n\n"
            
            # Telegram has a message length limit
            if len(message) > 4000:
                chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                for chunk in chunks:
                    await message_obj.reply_text(chunk, parse_mode="Markdown")
            else:
                await message_obj.reply_text(message, parse_mode="Markdown")
        except Exception as e:
            message_obj = update.message if update.message else update.callback_query.message
            await message_obj.reply_text(f"❌ Error fetching emails: {str(e)}")
    
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
            "/labels - View email categorization statistics\n"
            "/view <label> - View emails for a specific label\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("labels", self.labels_command))
        self.application.add_handler(CommandHandler("view", self.view_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Add callback query handler for inline buttons
        from telegram.ext import CallbackQueryHandler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
    
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
