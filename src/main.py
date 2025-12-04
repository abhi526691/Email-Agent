import os
import time
import sys
import threading
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GOOGLE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, POLLING_INTERVAL
from src.gmail_client import GmailHandler
from src.categorizer import EmailCategorizer
from src.agent import GmailLLMAgent

def initialize_agent():
    """Initialize and return the agent instance"""
    print("Initializing Email Agent...")
    
    # Initialize Gmail handler
    try:
        gmail_handler = GmailHandler()
    except Exception as e:
        print(f"Failed to initialize Gmail handler: {e}")
        return None

    # Initialize Gemini LLM
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return None

    llm = ChatGoogleGenerativeAI(
        google_api_key=GOOGLE_API_KEY,
        model="gemini-2.5-flash"
    )

    categorizer = EmailCategorizer(llm)

    # Create LLM Agent
    agent = GmailLLMAgent(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, gmail_handler, categorizer)
    return agent

def run_polling_loop(stop_event=None, initial_mode="monitor"):
    """
    Run the agent polling loop until stop_event is set
    
    Args:
        stop_event: Threading event to signal stop
        initial_mode: "monitor" (default) or "backfill"
    """
    agent = initialize_agent()
    if not agent:
        print("Agent initialization failed.")
        return

    print(f"Agent started. Mode: {initial_mode}. Polling interval: {POLLING_INTERVAL} seconds")
    
    # Handle backfill if requested
    if initial_mode == "backfill":
        print("🚀 Starting 24h Backfill (Read & Unread)...")
        try:
            agent.process_emails(hours=24, max_results=20, unread_only=False)
            print("✅ Backfill complete. Switching to monitoring mode...")
        except Exception as e:
            print(f"Error during backfill: {e}")
            
    # Main polling loop
    while True:
        if stop_event and stop_event.is_set():
            print("Stop event received. Stopping agent...")
            break

        try:
            # Process emails (Monitor mode: unread only)
            agent.process_emails(hours=24, max_results=10, unread_only=True)
        except Exception as e:
            print(f"Error during processing cycle: {e}")
        
        # Sleep in short intervals to check for stop_event
        for _ in range(POLLING_INTERVAL):
            if stop_event and stop_event.is_set():
                break
            time.sleep(1)

def main():
    """Entry point for command line execution"""
    try:
        run_polling_loop()
    except KeyboardInterrupt:
        print("\nStopping Email Agent...")
        sys.exit(0)

if __name__ == "__main__":
    main()
