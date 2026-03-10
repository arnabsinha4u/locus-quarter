from __future__ import annotations

import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from locus_quarter_app.interfaces import MailClient
from locus_quarter_app.models import EmailConfig


class GmailClient(MailClient):
    def __init__(self, config: EmailConfig):
        self.config = config

    def _credentials(self) -> Credentials:
        credential_dir = os.path.expanduser(self.config.secrets_path)
        os.makedirs(credential_dir, exist_ok=True)
        token_path = os.path.join(credential_dir, self.config.token_json)
        scopes = [scope.strip() for scope in self.config.action_scope.split(",") if scope.strip()]

        creds: Credentials | None = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.config.client_secret_file:
                    raise ValueError(
                        "Gmail client secret file is required when no valid token exists. "
                        "Set EMAIL:g_gmail_client_secret_file or LQ_GMAIL_CLIENT_SECRET_FILE."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.config.client_secret_file, scopes)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        if creds is None:
            raise RuntimeError("Unable to acquire Gmail credentials")
        return creds

    def send(self, sender: str, to: str, subject: str, body_text: str) -> None:
        credentials = self._credentials()
        service = build("gmail", "v1", credentials=credentials)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain"))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
