from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta
import os
import sys
import subprocess
import mimetypes
import email
from base64 import urlsafe_b64decode
import logging
from Extensions import Extensions
from MagicalAuth import MagicalAuth
from Globals import getenv

try:
    from googleapiclient.discovery import build
except:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "google-api-python-client"]
    )
    from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class google(Extensions):
    """
    The Google extension provides functions to interact with Google services such as Gmail and Google Calendar. It uses logged in user's Google account to perform actions like sending emails, moving emails to folders, creating draft emails, deleting emails, searching emails, replying to emails, processing attachments, getting calendar items, adding calendar items, and removing calendar items if the user signed in with Google.
    """

    def __init__(
        self,
        **kwargs,
    ):
        self.api_key = kwargs.get("api_key")
        self.access_token = kwargs.get("GOOGLE_ACCESS_TOKEN", None)
        self.auth = None
        google_client_id = getenv("GOOGLE_CLIENT_ID")
        google_client_secret = getenv("GOOGLE_CLIENT_SECRET")
        self.timezone = getenv("TZ")
        if google_client_id and google_client_secret:
            self.commands = {
                "Google - Get Emails": self.get_emails,
                "Google - Send Email": self.send_email,
                "Google - Move Email to Folder": self.move_email_to_folder,
                "Google - Create Draft Email": self.create_draft_email,
                "Google - Delete Email": self.delete_email,
                "Google - Search Emails": self.search_emails,
                "Google - Reply to Email": self.reply_to_email,
                "Google - Process Attachments": self.process_attachments,
                "Google - Get Calendar Items": self.get_calendar_items,
                "Google - Add Calendar Item": self.add_calendar_item,
                "Google - Remove Calendar Item": self.remove_calendar_item,
                "Google - Get Keep Notes": self.get_keep_notes,
                "Google - Create Keep Note": self.create_keep_note,
                "Google - Delete Keep Note": self.delete_keep_note,
            }
            if self.api_key:
                try:
                    self.auth = MagicalAuth(token=self.api_key)
                    self.timezone = self.auth.get_timezone()
                except Exception as e:
                    logging.error(f"Error initializing Google extension: {str(e)}")
        self.attachments_dir = (
            kwargs["conversation_directory"]
            if "conversation_directory" in kwargs
            else "./WORKSPACE/attachments"
        )
        os.makedirs(self.attachments_dir, exist_ok=True)

    def authenticate(self):
        """
        Verifies that the current access token corresponds to a valid user.
        If the /me endpoint fails, refreshes the token using the OAuth refresh flow.
        """
        if self.auth:
            # Get both access and refresh tokens from MagicalAuth
            oauth_data = self.auth.get_oauth_functions("google")
            if oauth_data and hasattr(oauth_data, "refresh_token"):
                credentials = Credentials(
                    token=self.access_token,
                    refresh_token=oauth_data.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=getenv("GOOGLE_CLIENT_ID"),
                    client_secret=getenv("GOOGLE_CLIENT_SECRET"),
                    scopes=[
                        "https://www.googleapis.com/auth/gmail.modify",
                        "https://www.googleapis.com/auth/gmail.compose",
                        "https://www.googleapis.com/auth/gmail.send",
                        "https://www.googleapis.com/auth/calendar",
                        "https://www.googleapis.com/auth/calendar.events",
                    ],
                )
                return credentials
            else:
                # Fallback to just access token if refresh token isn't available
                self.access_token = self.auth.refresh_oauth_token(provider="google")

        credentials = Credentials(
            token=self.access_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=getenv("GOOGLE_CLIENT_ID"),
            client_secret=getenv("GOOGLE_CLIENT_SECRET"),
            scopes=[
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events",
            ],
        )
        return credentials

    async def get_emails(self, query=None, max_emails=10):
        """
        Get emails from the user's Gmail account

        Args:
        query (str): The search query to filter emails
        max_emails (int): The maximum number of emails to retrieve

        Returns:
        List[Dict]: A list of email data
        """
        try:
            access_token = self.authenticate()
            service = build(
                "gmail",
                "v1",
                credentials=access_token,
                always_use_jwt_access=True,
            )
            result = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_emails)
                .execute()
            )
            messages = result.get("messages", [])

            emails = []
            for message in messages:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"])
                    .execute()
                )
                email_data = {
                    "id": msg["id"],
                    "sender": msg["payload"]["headers"][0]["value"],
                    "subject": msg["payload"]["headers"][1]["value"],
                    "body": msg["snippet"],
                    "attachments": [
                        part["filename"]
                        for part in msg["payload"]["parts"]
                        if part.get("filename")
                    ],
                    "received_time": datetime.fromtimestamp(
                        int(msg["internalDate"]) / 1000
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                }
                emails.append(email_data)

            return emails
        except Exception as e:
            logging.info(f"Error retrieving emails: {str(e)}")
            return []

    async def send_email(self, to, subject, message_text):
        """
        Send an email from the user's Gmail account

        Args:
        to (str): The email address of the recipient
        subject (str): The subject of the email
        message_text (str): The body of the email

        Returns:
        str: The result of sending the email
        """
        try:
            access_token = self.authenticate()

            service = build("gmail", "v1", credentials=access_token)

            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = subject

            msg = MIMEText(message_text)
            message.attach(msg)

            raw = urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {"raw": raw}
            service.users().messages().send(userId="me", body=send_message).execute()

            return "Email sent successfully."
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            return "Failed to send email."

    async def move_email_to_folder(self, message_id, folder_name):
        """
        Move an email to a specific folder in the user's Gmail account

        Args:
        message_id (str): The ID of the email message
        folder_name (str): The name of the folder to move the email to

        Returns:
        str: The result of moving the email
        """
        try:
            access_token = self.authenticate()
            service = build(
                "gmail",
                "v1",
                credentials=access_token,
                always_use_jwt_access=True,
            )

            folders = service.users().labels().list(userId="me").execute()
            folder_id = next(
                (
                    folder["id"]
                    for folder in folders["labels"]
                    if folder["name"] == folder_name
                ),
                None,
            )

            if not folder_id:
                folder_data = {"name": folder_name}
                folder = (
                    service.users()
                    .labels()
                    .create(userId="me", body=folder_data)
                    .execute()
                )
                folder_id = folder["id"]

            service.users().messages().modify(
                userId="me", id=message_id, body={"addLabelIds": [folder_id]}
            ).execute()

            return f"Email moved to {folder_name} folder."
        except Exception as e:
            logging.info(f"Error moving email: {str(e)}")
            return "Failed to move email."

    async def create_draft_email(self, recipient, subject, body, attachments=None):
        """
        Create a draft email in the user's Gmail account

        Args:
        recipient (str): The email address of the recipient
        subject (str): The subject of the email
        body (str): The body of the email
        attachments (List[str]): A list of file paths to attach to the email

        Returns:
        str: The result of creating the draft email
        """
        try:
            access_token = self.authenticate()
            service = build(
                "gmail",
                "v1",
                credentials=access_token,
                always_use_jwt_access=True,
            )

            message = MIMEMultipart()
            message["to"] = recipient
            message["subject"] = subject

            msg = MIMEText(body)
            message.attach(msg)

            if attachments:
                for attachment in attachments:
                    content_type, encoding = mimetypes.guess_type(attachment)

                    if content_type is None or encoding is not None:
                        content_type = "application/octet-stream"

                    main_type, sub_type = content_type.split("/", 1)
                    with open(attachment, "rb") as fp:
                        msg = MIMEApplication(fp.read(), _subtype=sub_type)

                    msg.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(attachment),
                    )
                    message.attach(msg)

            raw = urlsafe_b64encode(message.as_bytes()).decode()
            draft = {"message": {"raw": raw}}
            service.users().drafts().create(userId="me", body=draft).execute()

            return "Draft email created successfully."
        except Exception as e:
            logging.info(f"Error creating draft email: {str(e)}")
            return "Failed to create draft email."

    async def delete_email(self, message_id):
        """
        Delete an email from the user's Gmail account

        Args:
        message_id (str): The ID of the email message

        Returns:
        str: The result of deleting the email
        """
        try:
            access_token = self.authenticate()
            service = build(
                "gmail",
                "v1",
                credentials=access_token,
                always_use_jwt_access=True,
            )
            service.users().messages().delete(userId="me", id=message_id).execute()
            return "Email deleted successfully."
        except Exception as e:
            logging.info(f"Error deleting email: {str(e)}")
            return "Failed to delete email."

    async def search_emails(self, query, max_emails=10):
        """
        Search emails in the user's Gmail account

        Args:
        query (str): The search query to filter emails
        max_emails (int): The maximum number of emails to retrieve

        Returns:
        List[Dict]: A list of email data
        """
        try:
            access_token = self.authenticate()
            service = build(
                "gmail",
                "v1",
                credentials=access_token,
                always_use_jwt_access=True,
            )
            result = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_emails)
                .execute()
            )
            messages = result.get("messages", [])

            emails = []
            for message in messages:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"])
                    .execute()
                )
                email_data = {
                    "id": msg["id"],
                    "sender": msg["payload"]["headers"][0]["value"],
                    "subject": msg["payload"]["headers"][1]["value"],
                    "body": msg["snippet"],
                    "attachments": [
                        part["filename"]
                        for part in msg["payload"]["parts"]
                        if part.get("filename")
                    ],
                    "received_time": datetime.fromtimestamp(
                        int(msg["internalDate"]) / 1000
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                }
                emails.append(email_data)

            return emails
        except Exception as e:
            logging.info(f"Error searching emails: {str(e)}")
            return []

    async def reply_to_email(self, message_id, body, attachments=None):
        """
        Reply to an email in the user's Gmail account

        Args:
        message_id (str): The ID of the email message
        body (str): The body of the reply email
        attachments (List[str]): A list of file paths to attach to the reply email

        Returns:
        str: The result of sending the reply
        """
        try:
            access_token = self.authenticate()
            service = build(
                "gmail",
                "v1",
                credentials=access_token,
                always_use_jwt_access=True,
            )
            message = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="raw")
                .execute()
            )
            msg_str = urlsafe_b64decode(message["raw"].encode("ASCII"))
            mime_msg = email.message_from_bytes(msg_str)

            reply_msg = MIMEMultipart()
            reply_msg["To"] = mime_msg["From"]
            reply_msg["Subject"] = f"Re: {mime_msg['Subject']}"
            reply_msg["In-Reply-To"] = mime_msg["Message-ID"]
            reply_msg["References"] = mime_msg["Message-ID"]

            reply_text = MIMEText(body)
            reply_msg.attach(reply_text)

            if attachments:
                for attachment in attachments:
                    content_type, encoding = mimetypes.guess_type(attachment)

                    if content_type is None or encoding is not None:
                        content_type = "application/octet-stream"

                    main_type, sub_type = content_type.split("/", 1)
                    with open(attachment, "rb") as fp:
                        attach_msg = MIMEApplication(fp.read(), _subtype=sub_type)

                    attach_msg.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(attachment),
                    )
                    reply_msg.attach(attach_msg)

            raw = urlsafe_b64encode(reply_msg.as_bytes()).decode()
            send_message = {"raw": raw}
            service.users().messages().send(userId="me", body=send_message).execute()

            return "Reply sent successfully."
        except Exception as e:
            logging.info(f"Error replying to email: {str(e)}")
            return "Failed to send reply."

    async def process_attachments(self, message_id):
        """
        Process attachments from an email in the user's Gmail account

        Args:
        message_id (str): The ID of the email message

        Returns:
        List[str]: A list of file paths to the saved attachments
        """
        try:
            access_token = self.authenticate()
            service = build(
                "gmail",
                "v1",
                credentials=access_token,
                always_use_jwt_access=True,
            )
            message = (
                service.users().messages().get(userId="me", id=message_id).execute()
            )
            saved_attachments = []

            for part in message["payload"]["parts"]:
                if part["filename"]:
                    attachment_id = part["body"]["attachmentId"]
                    attachment = (
                        service.users()
                        .messages()
                        .attachments()
                        .get(userId="me", messageId=message_id, id=attachment_id)
                        .execute()
                    )
                    data = urlsafe_b64decode(attachment["data"])

                    attachment_path = os.path.join(
                        self.attachments_dir, part["filename"]
                    )
                    with open(attachment_path, "wb") as file:
                        file.write(data)
                    saved_attachments.append(attachment_path)

            return saved_attachments
        except Exception as e:
            logging.info(f"Error processing attachments: {str(e)}")
            return []

    async def get_calendar_items(self, start_date=None, end_date=None, max_items=10):
        """
        Get calendar items from the user's Google Calendar

        Args:
        start_date (datetime): The start date to filter calendar items
        end_date (datetime): The end date to filter calendar items
        max_items (int): The maximum number of calendar items to retrieve

        Returns:
        List[Dict]: A list of calendar item data
        """
        try:
            access_token = self.authenticate()
            service = build(
                "calendar",
                "v3",
                credentials=access_token,
                always_use_jwt_access=True,
            )

            if start_date is None:
                start_date = datetime.utcnow().isoformat() + "Z"
            else:
                start_date = start_date.isoformat() + "Z"

            if end_date is None:
                end_date = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
            else:
                end_date = end_date.isoformat() + "Z"

            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_date,
                    timeMax=end_date,
                    maxResults=max_items,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            calendar_items = []
            for event in events:
                item_data = {
                    "id": event["id"],
                    "subject": event["summary"],
                    "start_time": event["start"]["dateTime"],
                    "end_time": event["end"]["dateTime"],
                    "location": event.get("location", ""),
                    "organizer": event["organizer"]["email"],
                }
                calendar_items.append(item_data)

            return calendar_items
        except Exception as e:
            logging.info(f"Error retrieving calendar items: {str(e)}")
            return []

    async def add_calendar_item(
        self, subject, start_time, end_time, location, attendees=None
    ):
        """
        Add a calendar item to the user's Google Calendar

        Args:
        subject (str): The subject of the calendar item
        start_time (str): The start time of the calendar item
        end_time (str): The end time of the calendar item
        location (str): The location of the calendar item
        attendees (List[str]): A list of email addresses of attendees

        Returns:
        str: The result of adding the calendar item
        """
        try:
            access_token = self.authenticate()
            service = build(
                "calendar",
                "v3",
                credentials=access_token,
                always_use_jwt_access=True,
            )

            event = {
                "summary": subject,
                "location": location,
                "start": {
                    "dateTime": start_time,
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "UTC",
                },
            }

            if attendees:
                event["attendees"] = [{"email": attendee} for attendee in attendees]

            service.events().insert(calendarId="primary", body=event).execute()

            return "Calendar item added successfully."
        except Exception as e:
            logging.info(f"Error adding calendar item: {str(e)}")
            return "Failed to add calendar item."

    async def remove_calendar_item(self, item_id):
        """
        Remove a calendar item from the user's Google Calendar

        Args:
        item_id (str): The ID of the calendar item to remove

        Returns:
        str: The result of removing the calendar item
        """
        try:
            access_token = self.authenticate()
            service = build(
                "calendar",
                "v3",
                credentials=access_token,
                always_use_jwt_access=True,
            )
            service.events().delete(calendarId="primary", eventId=item_id).execute()
            return "Calendar item removed successfully."
        except Exception as e:
            logging.info(f"Error removing calendar item: {str(e)}")
            return "Failed to remove calendar item."

    async def get_keep_notes(self):
        """
        Get all notes from Google Keep

        Returns:
        List[Dict]: A list of note data
        """
        try:
            access_token = self.authenticate()
            service = build("keep", "v1", credentials=access_token)
            notes = service.notes().list().execute()
            return notes.get("items", [])
        except Exception as e:
            logging.info(f"Error retrieving notes: {str(e)}")
            return []

    async def create_keep_note(self, title, content):
        """
        Create a new note in Google Keep

        Args:
        title (str): The title of the note
        content (str): The content of the note

        Returns:
        str: The result of creating the note
        """
        try:
            access_token = self.authenticate()
            service = build("keep", "v1", credentials=access_token)
            note = {"title": title, "content": content}
            service.notes().create(body=note).execute()
            return "Note created successfully."
        except Exception as e:
            logging.info(f"Error creating note: {str(e)}")
            return "Failed to create note."

    async def delete_keep_note(self, note_id):
        """
        Delete a note from Google Keep

        Args:
        note_id (str): The ID of the note to delete

        Returns:
        str: The result of deleting the note
        """
        try:
            access_token = self.authenticate()
            service = build("keep", "v1", credentials=access_token)
            service.notes().delete(noteId=note_id).execute()
            return "Note deleted successfully."
        except Exception as e:
            logging.info(f"Error deleting note: {str(e)}")
            return "Failed to delete note."
