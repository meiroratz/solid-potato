from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional
from googleapiclient.discovery import build
from auth.google_auth import get_credentials


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    start: datetime
    end: datetime
    location: Optional[str]
    description: Optional[str]
    all_day: bool
    calendar_name: str

    @property
    def time_range(self) -> str:
        if self.all_day:
            return "All day"
        fmt = "%-I:%M %p"
        return f"{self.start.strftime(fmt)} – {self.end.strftime(fmt)}"


def fetch(days_ahead: int = 1) -> list[CalendarEvent]:
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    end_of_range = now + timedelta(days=days_ahead)

    calendars = service.calendarList().list().execute().get("items", [])
    events: list[CalendarEvent] = []

    for cal in calendars:
        cal_id = cal["id"]
        cal_name = cal.get("summary", cal_id)

        result = service.events().list(
            calendarId=cal_id,
            timeMin=now.isoformat(),
            timeMax=end_of_range.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        for item in result.get("items", []):
            start_raw = item["start"]
            end_raw = item["end"]

            if "dateTime" in start_raw:
                all_day = False
                start = datetime.fromisoformat(start_raw["dateTime"])
                end = datetime.fromisoformat(end_raw["dateTime"])
            else:
                all_day = True
                start = datetime.fromisoformat(start_raw["date"]).replace(tzinfo=timezone.utc)
                end = datetime.fromisoformat(end_raw["date"]).replace(tzinfo=timezone.utc)

            events.append(CalendarEvent(
                event_id=item["id"],
                title=item.get("summary", "(No title)"),
                start=start,
                end=end,
                location=item.get("location"),
                description=item.get("description"),
                all_day=all_day,
                calendar_name=cal_name,
            ))

    events.sort(key=lambda e: e.start)
    return events


def fetch_upcoming(lookahead_minutes: int = 15) -> list[CalendarEvent]:
    """Return events starting within the next `lookahead_minutes` minutes."""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(minutes=lookahead_minutes)

    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    calendars = service.calendarList().list().execute().get("items", [])
    events: list[CalendarEvent] = []

    for cal in calendars:
        cal_id = cal["id"]
        cal_name = cal.get("summary", cal_id)

        result = service.events().list(
            calendarId=cal_id,
            timeMin=now.isoformat(),
            timeMax=window_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        for item in result.get("items", []):
            start_raw = item["start"]
            end_raw = item["end"]

            if "dateTime" in start_raw:
                all_day = False
                start = datetime.fromisoformat(start_raw["dateTime"])
                end = datetime.fromisoformat(end_raw["dateTime"])
            else:
                all_day = True
                start = datetime.fromisoformat(start_raw["date"]).replace(tzinfo=timezone.utc)
                end = datetime.fromisoformat(end_raw["date"]).replace(tzinfo=timezone.utc)

            events.append(CalendarEvent(
                event_id=item["id"],
                title=item.get("summary", "(No title)"),
                start=start,
                end=end,
                location=item.get("location"),
                description=item.get("description"),
                all_day=all_day,
                calendar_name=cal_name,
            ))

    events.sort(key=lambda e: e.start)
    return events
