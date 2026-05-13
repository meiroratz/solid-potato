#!/usr/bin/env python3
"""Daily briefing — fetches calendar, email, weather, and Trello, then emails a digest."""

import argparse
import sys

import config
from sources import calendar, gmail, weather, trello
from compose import compose
from deliver import create_draft, send_now


def main():
    parser = argparse.ArgumentParser(description="Send your daily briefing digest.")
    parser.add_argument(
        "--send", action="store_true",
        help="Send immediately instead of creating a draft",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the HTML to stdout, do not touch Gmail",
    )
    args = parser.parse_args()

    print("Fetching weather...", flush=True)
    wx = weather.fetch()

    print("Fetching calendar events...", flush=True)
    events = calendar.fetch(days_ahead=1)

    print("Fetching email threads...", flush=True)
    threads = gmail.fetch()

    print("Fetching Trello activity...", flush=True)
    trello_actions = trello.fetch()

    print("Composing digest...", flush=True)
    subject, html = compose(
        weather=wx,
        events=events,
        threads=threads,
        trello_actions=trello_actions,
        trello_days=config.TRELLO_ACTIVITY_DAYS,
    )

    if args.dry_run:
        print(f"\nSubject: {subject}\n")
        print(html)
        return

    if args.send:
        msg_id = send_now(subject, html)
        print(f"Sent! Message ID: {msg_id}")
    else:
        draft_id = create_draft(subject, html)
        print(f"Draft created! Draft ID: {draft_id}")
        print("Open Gmail to review and send your briefing.")


if __name__ == "__main__":
    main()
