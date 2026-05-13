#!/usr/bin/env python3
"""Calendar event email trigger — run on a cron schedule (e.g. every 5 minutes).

Sends one notification email per upcoming event whose title contains
TRIGGER_KEYWORD (default "YSA BM"), skipping events already notified.
State is persisted in TRIGGER_STATE_FILE.
"""

import json
import sys
from datetime import datetime, timezone

import config
from sources.calendar import CalendarEvent, fetch_upcoming
from deliver import send_now


# ── State helpers ─────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if config.TRIGGER_STATE_FILE.exists():
        return json.loads(config.TRIGGER_STATE_FILE.read_text())
    return {}


def _save_state(state: dict) -> None:
    config.TRIGGER_STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Email composition ─────────────────────────────────────────────────────────

def _compose_notification(event: CalendarEvent) -> tuple[str, str]:
    subject = f"Starting soon: {event.title}"

    time_label = event.time_range
    location_row = (
        f'<p style="margin:4px 0;font-size:14px;color:#555;">📍 {event.location}</p>'
        if event.location else ""
    )
    description_row = (
        f'<p style="margin:8px 0 0;font-size:13px;color:#666;">{event.description}</p>'
        if event.description else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
             background:#f5f5f5;margin:0;padding:20px;color:#333;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;
              border:1px solid #e0e0e0;overflow:hidden;">
    <div style="background:#1a1a2e;color:#fff;padding:20px 24px;">
      <p style="margin:0;font-size:12px;opacity:.7;text-transform:uppercase;
                letter-spacing:.08em;">Starting soon</p>
      <h1 style="margin:6px 0 0;font-size:20px;font-weight:700;">{event.title}</h1>
    </div>
    <div style="padding:20px 24px;">
      <p style="margin:0 0 4px;font-size:13px;color:#999;">{event.calendar_name}</p>
      <p style="margin:0 0 8px;font-size:16px;font-weight:600;">🕐 {time_label}</p>
      {location_row}
      {description_row}
    </div>
  </div>
</body>
</html>"""

    return subject, html


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Checking for events starting within {config.TRIGGER_LOOKAHEAD_MINUTES} minutes…",
          flush=True)

    events = fetch_upcoming(config.TRIGGER_LOOKAHEAD_MINUTES)
    state = _load_state()
    notified = 0

    keyword = config.TRIGGER_KEYWORD.lower()

    for event in events:
        if keyword not in event.title.lower():
            continue

        if event.event_id in state:
            print(f"  skip (already sent): {event.title}")
            continue

        print(f"  sending notification: {event.title} @ {event.time_range}")
        subject, html = _compose_notification(event)
        try:
            msg_id = send_now(subject, html)
            state[event.event_id] = {
                "title": event.title,
                "start": event.start.isoformat(),
                "notified_at": datetime.now(timezone.utc).isoformat(),
                "message_id": msg_id,
            }
            notified += 1
        except Exception as exc:
            print(f"  ERROR sending for '{event.title}': {exc}", file=sys.stderr)

    _save_state(state)
    print(f"Done — {notified} notification(s) sent.")


if __name__ == "__main__":
    main()
