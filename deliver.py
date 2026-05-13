import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from auth.google_auth import get_credentials
import config


def create_draft(subject: str, html_body: str) -> str:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["To"] = config.BRIEFING_RECIPIENT or "me"
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}},
    ).execute()

    return draft["id"]


def send_now(subject: str, html_body: str, recipient: str = "") -> str:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["To"] = recipient or config.BRIEFING_RECIPIENT or "me"
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(
        userId="me",
        body={"raw": raw},
    ).execute()

    return sent["id"]
