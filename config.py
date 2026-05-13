import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
BRIEFING_RECIPIENT = os.getenv("BRIEFING_RECIPIENT", "")
WEATHER_LOCATION = os.getenv("WEATHER_LOCATION", "New York")
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY", "")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")
TRELLO_BOARDS = [b.strip() for b in os.getenv("TRELLO_BOARDS", "").split(",") if b.strip()]
TRELLO_ACTIVITY_DAYS = int(os.getenv("TRELLO_ACTIVITY_DAYS", "1"))
EMAIL_THREAD_LIMIT = int(os.getenv("EMAIL_THREAD_LIMIT", "10"))

TRIGGER_LOOKAHEAD_MINUTES = int(os.getenv("TRIGGER_LOOKAHEAD_MINUTES", "15"))
TRIGGER_KEYWORD = os.getenv("TRIGGER_KEYWORD", "YSA BM")
TRIGGER_RECIPIENT = os.getenv("TRIGGER_RECIPIENT", "meiroratz@gmail.com")
TRIGGER_STATE_FILE = Path(os.getenv("TRIGGER_STATE_FILE", "trigger_state.json"))

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]
TOKEN_FILE = Path("token.json")
