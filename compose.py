from datetime import datetime, timezone
from jinja2 import Environment, BaseLoader
from sources.calendar import CalendarEvent
from sources.gmail import EmailThread
from sources.weather import WeatherReport
from sources.trello import TrelloAction

_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f5f5; margin: 0; padding: 20px; color: #333; }
  .container { max-width: 640px; margin: 0 auto; }
  .header { background: #1a1a2e; color: #fff; border-radius: 12px 12px 0 0;
            padding: 24px 28px; }
  .header h1 { margin: 0 0 4px; font-size: 22px; font-weight: 700; }
  .header p  { margin: 0; opacity: 0.7; font-size: 14px; }
  .section   { background: #fff; padding: 20px 28px; border-left: 1px solid #e0e0e0;
               border-right: 1px solid #e0e0e0; }
  .section:last-of-type { border-radius: 0 0 12px 12px;
                           border-bottom: 1px solid #e0e0e0; }
  .section-title { font-size: 13px; font-weight: 700; text-transform: uppercase;
                   letter-spacing: 0.08em; color: #888; margin: 0 0 14px; }
  .divider { height: 1px; background: #eee; margin: 0; }

  /* Weather */
  .weather-main { display: flex; align-items: baseline; gap: 10px; }
  .temp { font-size: 42px; font-weight: 300; line-height: 1; }
  .weather-meta { font-size: 14px; color: #666; }
  .hourly { display: flex; gap: 12px; margin-top: 14px; overflow-x: auto; }
  .hour-cell { text-align: center; min-width: 54px; background: #f9f9f9;
               border-radius: 8px; padding: 8px 6px; }
  .hour-cell .h-time { font-size: 11px; color: #999; }
  .hour-cell .h-temp { font-size: 14px; font-weight: 600; margin-top: 4px; }

  /* Calendar */
  .event { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
  .event:last-child { border-bottom: none; }
  .event-time { font-size: 12px; color: #999; }
  .event-title { font-weight: 600; margin: 2px 0; }
  .event-meta { font-size: 12px; color: #888; }

  /* Email */
  .thread { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
  .thread:last-child { border-bottom: none; }
  .thread-subject { font-weight: 600; }
  .thread-from { font-size: 12px; color: #666; }
  .thread-snippet { font-size: 13px; color: #777; margin-top: 3px; }
  .badge { display: inline-block; background: #4f46e5; color: #fff;
           font-size: 10px; border-radius: 999px; padding: 1px 6px;
           vertical-align: middle; margin-left: 4px; }

  /* Trello */
  .trello-action { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
  .trello-action:last-child { border-bottom: none; }
  .trello-card { font-weight: 600; }
  .trello-who  { font-size: 12px; color: #666; }
  .trello-comment { font-size: 13px; color: #555; margin-top: 4px;
                    border-left: 3px solid #e0e0e0; padding-left: 8px; }

  .empty { color: #aaa; font-style: italic; font-size: 14px; }
  .footer { text-align: center; font-size: 12px; color: #bbb; padding: 16px; }
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Good morning ☀️</h1>
    <p>{{ date_str }} — Your daily briefing</p>
  </div>

  <!-- WEATHER -->
  <div class="section">
    <p class="section-title">🌤 Weather — {{ weather.location }}</p>
    {% if weather.error %}
      <p class="empty">Could not load weather: {{ weather.error }}</p>
    {% else %}
    <div class="weather-main">
      <span class="temp">{{ weather.temp_c | round(0) | int }}°C</span>
      <span class="weather-meta">
        {{ weather.description }}<br>
        Feels like {{ weather.feels_like_c | round(0) | int }}°C &nbsp;·&nbsp;
        Humidity {{ weather.humidity }}% &nbsp;·&nbsp;
        Wind {{ weather.wind_kph }} km/h
      </span>
    </div>
    {% if weather.hourly %}
    <div class="hourly">
      {% for h in weather.hourly %}
      <div class="hour-cell">
        <div class="h-time">{{ h.time }}</div>
        <div class="h-temp">{{ h.temp_c | round(0) | int }}°</div>
      </div>
      {% endfor %}
    </div>
    {% endif %}
    {% endif %}
  </div>
  <div class="divider"></div>

  <!-- CALENDAR -->
  <div class="section">
    <p class="section-title">📅 Today's Calendar</p>
    {% if not events %}
      <p class="empty">No events today.</p>
    {% else %}
      {% for e in events %}
      <div class="event">
        <div class="event-time">{{ e.time_range }}{% if not e.all_day %} · {{ e.calendar_name }}{% endif %}</div>
        <div class="event-title">{{ e.title }}</div>
        {% if e.location %}<div class="event-meta">📍 {{ e.location }}</div>{% endif %}
      </div>
      {% endfor %}
    {% endif %}
  </div>
  <div class="divider"></div>

  <!-- EMAIL -->
  <div class="section">
    <p class="section-title">📬 Inbox — Unread Threads</p>
    {% if not threads %}
      <p class="empty">Inbox zero! 🎉</p>
    {% else %}
      {% for t in threads %}
      <div class="thread">
        <div class="thread-subject">
          {{ t.subject }}
          {% if t.message_count > 1 %}<span class="badge">{{ t.message_count }}</span>{% endif %}
        </div>
        <div class="thread-from">From {{ t.sender }}</div>
        <div class="thread-snippet">{{ t.snippet | truncate(120) }}</div>
      </div>
      {% endfor %}
    {% endif %}
  </div>
  <div class="divider"></div>

  <!-- TRELLO -->
  <div class="section">
    <p class="section-title">📋 Trello Activity</p>
    {% if not trello_actions %}
      <p class="empty">No Trello activity in the past {{ trello_days }} day(s).</p>
    {% else %}
      {% for a in trello_actions %}
      <div class="trello-action">
        <div class="trello-card">{{ a.card_name }}</div>
        <div class="trello-who">
          {{ a.member }} {{ a.human_action }}
          {% if a.list_name %} in <em>{{ a.list_name }}</em>{% endif %}
          · {{ a.board_name }}
          · {{ a.date.strftime('%-I:%M %p') }}
        </div>
        {% if a.comment %}
        <div class="trello-comment">{{ a.comment | truncate(200) }}</div>
        {% endif %}
      </div>
      {% endfor %}
    {% endif %}
  </div>

  <div class="footer">Generated {{ now_str }}</div>
</div>
</body>
</html>
"""


def compose(
    weather: WeatherReport,
    events: list[CalendarEvent],
    threads: list[EmailThread],
    trello_actions: list[TrelloAction],
    trello_days: int,
) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %B %-d, %Y")
    now_str = now.strftime("%Y-%m-%d %H:%M UTC")
    subject = f"Daily Briefing — {date_str}"

    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(_TEMPLATE)
    html = tmpl.render(
        date_str=date_str,
        now_str=now_str,
        weather=weather,
        events=events,
        threads=threads,
        trello_actions=trello_actions,
        trello_days=trello_days,
    )
    return subject, html
