# Email Agent

A smart email classifier and automation agent powered by Google's Gemini LLM. It fetches emails from Gmail, classifies them (e.g., Interview, Job Alert, Spam), labels them in Gmail, and sends Telegram notifications for important updates.

## Features
- **Gmail Integration**: Fetches unread emails and manages labels.
- **LLM Classification**: Uses Gemini 2.5 Flash to intelligently categorize emails.
- **Telegram Notifications**: Sends instant alerts for interviews, offers, and follow-ups.
- **Automated Labeling**: Organizes your inbox by applying labels based on content.

## Setup

### Prerequisites
1. **Python 3.10+**
2. **Gmail API Credentials**: `credentials/credentials.json` (OAuth 2.0 Client ID).
3. **Google Gemini API Key**: Set as `GOOGLE_API_KEY` environment variable.
4. **Telegram Bot**: Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables.

### Installation
1. Clone the repository.
2. Create/Activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the agent:
```bash
python -m src.main
```

## Project Structure
- `src/`: Source code modules.
  - `agent.py`: Main agent logic and orchestration.
  - `categorizer.py`: LLM classification logic.
  - `gmail_client.py`: Gmail API wrapper.
  - `config.py`: Configuration and prompts.
- `Notebooks/`: Original prototyping notebooks.