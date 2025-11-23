import os
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GOOGLE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.gmail_client import GmailHandler
from src.categorizer import EmailCategorizer
from src.agent import GmailLLMAgent

def main():
    print("Starting Email Agent...")

    # Initialize Gmail handler
    gmail_handler = GmailHandler()

    # Initialize Gemini LLM
    if not GOOGLE_API_KEY:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        return

    llm = ChatGoogleGenerativeAI(
        google_api_key=GOOGLE_API_KEY,
        model="gemini-2.5-flash"
    )

    categorizer = EmailCategorizer(llm)

    # Create LLM Agent
    agent = GmailLLMAgent(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, gmail_handler, categorizer)

    # Process emails from last 24 hours
    # You can adjust hours and max_results as needed
    agent.process_emails(hours=24, max_results=10)

if __name__ == "__main__":
    main()
