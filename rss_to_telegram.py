import os
import json
import html
import requests
import feedparser

RSS_URL = "https://mt-news.ru/feed/"
##RSS_URL = "https://www.motogp.com/en/rss/news"
#RSS_URL = "https://feeds.bbci.co.uk/news/rss.xml"
STATE_FILE = "state.json"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Завантаження стану
try:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
except FileNotFoundError:
    state = {"last_link": ""}

feed = feedparser.parse(RSS_URL)

if not feed.entries:
    raise SystemExit("RSS feed is empty")

item = feed.entries[0]

title = html.escape(item.title)
link = item.link

if link == state.get("last_link"):
    print("No new posts")
    raise SystemExit(0)

description = getattr(item, "summary", "")
description = description[:700]
description = html.escape(description)

text = (
    f"<b>🏍 MotoGP News</b>\n\n"
    f"<b>{title}</b>\n\n"
    f"<blockquote>{description}</blockquote>"
)

keyboard = {
    "inline_keyboard": [
        [
            {
                "text": "Читати повністю",
                "url": link
            }
        ]
    ]
}

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": keyboard,
        "disable_web_page_preview": True,
    },
    timeout=30,
)

#print(response.status_code)
#print(response.text)

response.raise_for_status()

state["last_link"] = link

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f)
