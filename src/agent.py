import requests
from .config import IMPORTANT_CATEGORIES

class GmailLLMAgent:
    """
    Fetch emails from Gmail Classifier, classify them using LLM Class, 
    and apply labels based on the predicted category and update it in Gmail.

    """

    def __init__(self, telegram_token: str, chat_id: str, gmail_handler, categorizer):
        self.gmail = gmail_handler
        self.categorizer = categorizer
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.IMPORTANT_CATEGORIES = IMPORTANT_CATEGORIES

    def process_emails(self, hours: int = 24, max_results: int = 5, unread_only: bool = False):
            """
            Fetch emails from the last 'hours' hours, classify, label them,
            and send Telegram notifications for important categories.
            """
            emails = self.gmail.get_emails_since(hours=hours, max_results=max_results, unread_only=unread_only)
            if not emails:
                print("No emails to process.")
                return

            print(f"Processing {len(emails)} emails...\n")

            # 1️⃣ Classify emails
            categorized_emails = self.categorizer.categorize(emails)

            # 2️⃣ Apply labels and check for important emails
            for email in categorized_emails:
                category_key = email.get("category", "uncategorized")
                label_name = email.get("category_label", "Other 📧")

                # create label if not exists
                if not self.gmail.check_label_exists(label_name):
                    self.gmail.create_label(label_name)

                # apply label
                try:
                    self.gmail.service.users().messages().modify(
                        userId='me',
                        id=email['id'],
                        body={'addLabelIds': [self._get_label_id(label_name)],
                            'removeLabelIds': []}  # optional: remove UNREAD
                    ).execute()
                    try:
                        print(f"Labeled: {email['subject'][:50]} -> {label_name}")
                    except UnicodeEncodeError:
                        print(f"Labeled: {email['subject'][:50].encode('ascii', 'replace').decode('ascii')} -> {label_name.encode('ascii', 'replace').decode('ascii')}")
                except Exception as e:
                    print(f"Error applying label to '{email['subject']}': {e}")

                # 3️⃣ Send Telegram notification if important
                if category_key in self.IMPORTANT_CATEGORIES and self.telegram_token and self.chat_id:
                    self.send_telegram_notification(email)


    def _get_label_id(self, label_name: str):
        """Return Gmail label ID, create if it doesn't exist"""
        labels = self.gmail.get_labels()
        for label in labels:
            if label['name'].lower() == label_name.lower():
                return label['id']
        # create if not found
        label = self.gmail.create_label(label_name)
        return label['id'] if label else None

    def send_telegram_notification(self, email):
        """Send a Telegram message with the email subject and snippet"""
        message = f"📧 *Important Email*\n\n*Subject:* {email.get('subject','')}\n*Snippet:* {email.get('snippet','')[:200]}..."
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "↩️ Reply", "callback_data": f"reply:{email['id']}"}
                ]]
            }
        }
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                try:
                    print(f"Telegram notification sent for '{email.get('subject','')[:50]}'")
                except UnicodeEncodeError:
                    print(f"Telegram notification sent for '{email.get('subject','').encode('ascii', 'replace').decode('ascii')[:50]}'")
            else:
                print(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
