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
                    # Fallback for Windows consoles that can't handle emojis
                    safe_name = label['name'].encode('ascii', 'replace').decode('ascii')
                    print(f" - {safe_name}")
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
                # Fallback for Windows consoles
                safe_sender = sender.encode('ascii', 'replace').decode('ascii')
                safe_subject = subject.encode('ascii', 'replace').decode('ascii')
                print(f"From: {safe_sender}")
                print(f"   Subject: {safe_subject}")


            return {
                "id": msg_id, 
                "threadId": msg.get('threadId'),
                "from": sender, 
                "subject": subject, 
                "labels": labels, 
                "snippet": snippet
            }

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
    
    def get_label_statistics(self):
        """Get email count statistics for all user-created labels"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Filter only user-created labels
            user_labels = [label for label in labels if label.get('type') == 'user']
            
            label_stats = {}
            for label in user_labels:
                label_name = label['name']
                label_id = label['id']
                
                # Get message count for this label
                try:
                    label_detail = self.service.users().labels().get(
                        userId='me', 
                        id=label_id
                    ).execute()
                    
                    # Get total messages with this label
                    message_count = label_detail.get('messagesTotal', 0)
                    label_stats[label_name] = message_count
                except Exception as e:
                    print(f"Error getting stats for label '{label_name}': {e}")
                    label_stats[label_name] = 0
            
            return label_stats
        except Exception as e:
            print(f"Error fetching label statistics: {e}")
            return {}
    
    def get_emails_by_label(self, label_name, max_results=10):
        """Fetch emails for a specific label"""
        try:
            # First, get the label ID
            labels = self.get_labels()
            label_id = None
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    label_id = label['id']
                    break
            
            if not label_id:
                print(f"Label '{label_name}' not found.")
                return None
            
            # Fetch messages with this label
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[label_id],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                return []
            
            # Get details for each message
            emails = []
            for msg in messages:
                details = self.get_email_details(msg['id'])
                if details:
                    emails.append(details)
            
            return emails
            return emails
        except Exception as e:
            # Safe print for error message which might contain the label name
            try:
                print(f"Error fetching emails for label '{label_name}': {e}")
            except UnicodeEncodeError:
                safe_label = label_name.encode('ascii', 'replace').decode('ascii')
                print(f"Error fetching emails for label '{safe_label}': {e}")
            return None

    def get_thread_details(self, thread_id):
        """Get details about a thread, specifically message count"""
        try:
            thread = self.service.users().threads().get(userId='me', id=thread_id).execute()
            messages = thread.get('messages', [])
            return {
                "id": thread_id,
                "messageCount": len(messages),
                "messages": messages
            }
        except Exception as e:
            print(f"Error fetching thread details: {e}")
            return None

    def send_reply(self, thread_id, to, subject, body):
        """Send a reply to a thread"""
        try:
            from email.mime.text import MIMEText
            import base64

            message = MIMEText(body)
            message['to'] = to
            # message['subject'] = subject # Omit subject for threading to work better naturally
            
            # If replying, we should ideally set References and In-Reply-To headers
            # But for simplicity, just setting the threadId in the API call usually groups it.
            # To be more correct, we'd fetch the last message in thread and set headers.
            # For now, let's rely on Gmail API's threadId grouping.
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            body = {'raw': raw_message, 'threadId': thread_id}
            
            sent_message = self.service.users().messages().send(
                userId='me', 
                body=body
            ).execute()
            
            print(f"Reply sent to {to} (Thread: {thread_id})")
            return sent_message
        except Exception as e:
            print(f"Error sending reply: {e}")
            return None
