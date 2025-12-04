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
    print(f"[DEBUG] run_polling_loop started with mode={initial_mode}")
    agent = initialize_agent()
    if not agent:
        print("[ERROR] Agent initialization failed.")
        return

    print(f"[OK] Agent started. Mode: {initial_mode}. Polling interval: {POLLING_INTERVAL} seconds")
    
    # Handle backfill if requested
    if initial_mode == "backfill":
        print("[INFO] Starting 24h Backfill (Read & Unread)...")
        try:
            agent.process_emails(hours=24, max_results=20, unread_only=False)
            print("[OK] Backfill complete. Switching to monitoring mode...")
        except Exception as e:
            print(f"[ERROR] Critical error during backfill!")
            print(f"[ERROR] Error type: {type(e).__name__}")
            print(f"[ERROR] Error message: {e}")
            import traceback
            print("[ERROR] Full traceback:")
            traceback.print_exc()
            print("[ERROR] Agent will stop due to backfill error.")
            return  # Exit the function, which will stop the agent
            
    # Main polling loop
    print("[INFO] Entering main polling loop...")
    cycle_count = 0
    while True:
        if stop_event and stop_event.is_set():
            print("[INFO] Stop event received. Stopping agent...")
            break

        cycle_count += 1
        print(f"[CYCLE {cycle_count}] Processing emails...")
        try:
            # Process emails (Monitor mode: unread only)
            agent.process_emails(hours=24, max_results=10, unread_only=True)
            print(f"[CYCLE {cycle_count}] Complete. Sleeping for {POLLING_INTERVAL} seconds...")
        except Exception as e:
            print(f"[ERROR] Error during processing cycle {cycle_count}: {e}")
            import traceback
            traceback.print_exc()
        
        # Sleep in short intervals to check for stop_event
        for i in range(POLLING_INTERVAL):
            if stop_event and stop_event.is_set():
                print("[INFO] Stop event detected during sleep.")
                break
            time.sleep(1)
    
    print("[INFO] run_polling_loop ended.")

def main():
    """Entry point for command line execution"""
    try:
        run_polling_loop()
    except KeyboardInterrupt:
        print("\nStopping Email Agent...")
        sys.exit(0)

if __name__ == "__main__":
    main()
