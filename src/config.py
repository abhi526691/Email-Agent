import os
from dotenv import load_dotenv

load_dotenv()

# Gmail API Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials/credentials.json' # Adjusted path assuming running from root
TOKEN_FILE = 'token.json'

# Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Categories considered important for Telegram notification
IMPORTANT_CATEGORIES = ["interview_request", "interview_reminder", "follow_up"]

# Job Categories
JOB_CATEGORIES = {
    "application_confirmed": {"label": "Applied ✓"},
    "interview_request": {"label": "Interview 📅"},
    "interview_reminder": {"label": "Interview Reminder ⏰"},
    "offer": {"label": "Job Offer 🎉"},
    "rejected": {"label": "Rejected ❌"},
    "assessment": {"label": "Assessment 📝"},
    "follow_up": {"label": "Follow-up 💬"},
    "job_alert": {"label": "Job Alert 🔔"},
    "newsletter": {"label": "Newsletter 📰"},
    "spam": {"label": "Spam 🗑️"},
    "uncategorized": {"label": "Other 📧"}
}

# Email Classification Prompt
EMAIL_CLASSIFICATION_PROMPT = """
You are a precise email classifier for job-related emails.
Your task is to assign the email to EXACTLY ONE of the following category keys:

{categories}

=========================
CATEGORY DEFINITIONS
=========================

application_confirmed:
    Confirmation that an application was received.

interview_request:
    Recruiter requesting to schedule an interview or providing interview scheduling links.

interview_reminder:
    Reminders or confirmations for upcoming interviews.

offer:
    Job offer emails, offer letters, verbal offers, or negotiation instructions.

rejected:
    Rejection emails stating the applicant is not moving forward.

assessment:
    Coding tests, online assessments, take-home assignments.

follow_up:
    Recruiter checking in, following up, asking for updates, or next-steps clarification.

job_alert:
    Job recommendations, alerts about openings, job board notifications.

newsletter:
    Company newsletters, weekly digests, marketing content.

spam:
    Irrelevant, suspicious, non-job content.

uncategorized:
    Use ONLY if the email clearly does not fit any category above.

=========================
CATEGORY PRIORITY
=========================
interview_request > interview_reminder > offer > rejected > assessment >
follow_up > application_confirmed > job_alert > newsletter > spam > uncategorized

=========================
EMAIL TO CLASSIFY
=========================

Subject: {subject}
Snippet: {snippet}

=========================
RESPONSE RULES
=========================
- Respond with ONLY the category key.
- No explanation.
- No extra text.
- No formatting.
Category:
"""
