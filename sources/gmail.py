import base64
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from googleapiclient.discovery import build
from auth.google_auth import get_credentials
import config


@dataclass
class EmailThread:
    subject: str
    sender: str
    snippet: str
    message_count: int
    date: datetime
    unread: bool


def _decode_header(raw: str) -> str:
    return raw.strip()


def _extract_name(from_header: str) -> str:
    match = re.match(r'^"?([^"<]+)"?\s*<', from_header)
    if match:
        return match.group(1).strip()
    return from_header.split("@")[0]


def fetch() -> list[EmailThread]:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    results = service.users().threads().list(
        userId="me",
        q="is:unread in:inbox",
        maxResults=config.EMAIL_THREAD_LIMIT,
    ).execute()

    thread_items = results.get("threads", [])
    threads: list[EmailThread] = []

    for item in thread_items:
        thread = service.users().threads().get(
            userId="me", id=item["id"], format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()

        messages = thread.get("messages", [])
        if not messages:
            continue

        first_msg = messages[0]
        headers = {h["name"]: h["value"] for h in first_msg.get("payload", {}).get("headers", [])}

        label_ids = first_msg.get("labelIds", [])
        unread = "UNREAD" in label_ids

        raw_date = headers.get("Date", "")
        try:
            from email.utils import parsedate_to_datetime
            date = parsedate_to_datetime(raw_date).astimezone(timezone.utc)
        except Exception:
            date = datetime.now(timezone.utc)

        threads.append(EmailThread(
            subject=headers.get("Subject", "(No subject)"),
            sender=_extract_name(headers.get("From", "Unknown")),
            snippet=thread.get("snippet", ""),
            message_count=len(messages),
            date=date,
            unread=unread,
        ))

    return threads
