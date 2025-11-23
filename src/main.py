import os
import time
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GOOGLE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, POLLING_INTERVAL
from src.gmail_client import GmailHandler
from src.categorizer import EmailCategorizer
from src.agent import GmailLLMAgent

def main():
    print("Starting Email Agent...")
    print(f"Polling interval: {POLLING_INTERVAL} seconds")

    # Initialize Gmail handler
    try:
        gmail_handler = GmailHandler()
    except Exception as e:
        print(f"Failed to initialize Gmail handler: {e}")
        return

    # Initialize Gemini LLM
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return

    llm = ChatGoogleGenerativeAI(
        google_api_key=GOOGLE_API_KEY,
        model="gemini-2.5-flash"
    )

    categorizer = EmailCategorizer(llm)

    # Create LLM Agent
    agent = GmailLLMAgent(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, gmail_handler, categorizer)

    print("Agent initialized. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                # Process emails from last 24 hours (or shorter window if running frequently)
                # Using 24 hours to be safe, but could reduce to POLLING_INTERVAL + buffer
                agent.process_emails(hours=24, max_results=10, unread_only=True)
            except Exception as e:
                print(f"Error during processing cycle: {e}")
            
            print(f"Sleeping for {POLLING_INTERVAL} seconds...")
            time.sleep(POLLING_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping Email Agent...")
        sys.exit(0)

if __name__ == "__main__":
    main()
