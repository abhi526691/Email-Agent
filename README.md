# Email Agent

A smart email classifier and automation agent powered by Google's Gemini LLM. It fetches emails from Gmail, classifies them (e.g., Interview, Job Alert, Spam), labels them in Gmail, and sends Telegram notifications for important updates.

## Features
- **Gmail Integration**: Fetches unread emails and manages labels.
- **LLM Classification**: Uses Gemini 2.5 Flash to intelligently categorize emails.
- **Telegram Notifications**: Sends instant alerts for interviews, offers, and follow-ups.
- **Interactive Telegram Bot**: Control the agent and view email stats directly from Telegram.
- **REST API Control**: Start, stop, and monitor the agent via HTTP endpoints.
- **Automated Labeling**: Organizes your inbox by applying labels based on content.
- **Continuous Monitoring**: Runs in the background and checks for new emails periodically.

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

### Running the Agent (API + Bot)
Start the FastAPI server, which also launches the Telegram bot:
```bash
uvicorn src.api:app --reload
```
The API will be available at `http://localhost:8000`.

### Telegram Bot Commands
Interact with the bot using these commands:
- `/start`: Start the email monitoring agent.
- `/stop`: Stop the agent.
- `/status`: Check if the agent is running.
- `/labels`: View email categorization statistics and select labels to view.
- `/view <label>`: View recent emails for a specific label (e.g., `/view Interview`).
- `/help`: Show available commands.

### API Endpoints
Control the agent programmatically:
- `POST /agent/start`: Start the agent.
- `POST /agent/stop`: Stop the agent.
- `GET /agent/status`: Get current status.

### Running Standalone (Legacy)
To run the agent without the API/Bot interface:
```bash
python -m src.main
```

## Project Structure
- `src/`: Source code modules.
  - `api.py`: FastAPI application and entry point.
  - `telegram_bot.py`: Telegram bot implementation.
  - `agent_controller.py`: Shared state management.
  - `agent.py`: Main agent logic and orchestration.
  - `categorizer.py`: LLM classification logic.
  - `gmail_client.py`: Gmail API wrapper.
  - `config.py`: Configuration and prompts.
  - `main.py`: Legacy standalone entry point.
- `Notebooks/`: Original prototyping notebooks.