import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from .config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE

class GmailHandler:
    """Minimal Gmail fetcher
    Fetch the labels and unread emails from Gmail using Gmail API.
    """

    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None

        # Load existing token
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            print("creds loaded")

        # If no valid token, log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def get_labels(self):
        """Fetch and display only user-created Gmail labels"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            # Filter only user-created labels
            user_labels = [label for label in labels if label.get('type') == 'user']

            if not user_labels:
                print("No user-created labels found.")
                return []

            print("Your Gmail Labels (created by you):")
            for label in user_labels:
                try:
                    print(f" - {label['name']}")
                except UnicodeEncodeError:
                    print(f" - {label['name'].encode('ascii', 'replace').decode('ascii')}")
            print()
            return user_labels

        except Exception as e:
            print(f"Error fetching labels: {e}")
            return []
        
    def get_email_details(self, msg_id):
        """Get full email details + labels"""
        try:
            msg = self.service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()

            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
            snippet = msg.get('snippet', '')
            labels = msg.get('labelIds', [])

            try:
                print(f"From: {sender}")
                print(f"   Subject: {subject}")
                print(f"   Labels: {', '.join(labels) if labels else '(No Labels)'}")
                print(f"   Snippet: {snippet}...\n")
            except UnicodeEncodeError:
                print(f"From: {sender.encode('ascii', 'replace').decode('ascii')}")
                print(f"   Subject: {subject.encode('ascii', 'replace').decode('ascii')}")


            return {"id": msg_id, "from": sender, "subject": subject, "labels": labels, "snippet": snippet}

        except Exception as e:
            print(f"Error reading email: {e}")
            return None

    def get_emails_since(self, hours: int = 24, max_results: int = 50, unread_only: bool = False):
        """Fetch emails received in the last 'hours' hours"""
        try:
            if unread_only:
                query = f"newer_than:{hours}h is:unread"
            else:
                query = f"newer_than:{hours}h"
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            if not messages:
                print(f"No emails found in the last {hours} hours.")
                return []

            print(f"Found {len(messages)} emails from the last {hours} hours:\n")
            emails = []
            for msg in messages:
                details = self.get_email_details(msg['id'])
                if details:
                    emails.append(details)
            return emails

        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def check_label_exists(self, label_name):
        """Check if a label exists"""
        labels = self.get_labels()
        for label in labels:
            if label['name'].lower() == label_name.lower():
                return True
        return False
    
    def create_label(self, label_name):
        """Create a new label"""
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        try:
            label = self.service.users().labels().create(
                userId='me',
                body=label_body
            ).execute()
            print(f"Label '{label_name}' created.")
            return label
        except Exception as e:
            print(f"Error creating label: {e}")
            return None
