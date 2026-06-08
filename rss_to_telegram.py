import os
import json
import re
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://mt-news.ru/news/"
STATE_FILE = "state.json"


# Завантаження стану
try:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
except:
    state = {"last_url": ""}


# Отримання сторінки
r = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)

r.raise_for_status()

soup = BeautifulSoup(r.text, "html.parser")

# Перша новина
news = soup.select_one("div[id^='news_list-'] a[href]")

if not news:
    raise Exception("News not found")

link = news["href"]

# Перевірка на дубль
if link == state.get("last_url"):
    print("No new posts")
    raise SystemExit(0)

# Заголовок
title_tag = news.find("h3")

if not title_tag:
    raise Exception("Title not found")

title = title_tag.get_text(strip=True)

# Картинка
photo = None

style_tag = news.find("style")

if style_tag:

    match = re.search(
        r'url\((.*?)\)',
        style_tag.get_text()
    )

    if match:
        photo = match.group(1)

caption = (
    f"🏍 MotoGP News\n\n"
    f"<b>{title}</b>"
)

keyboard = {
    "inline_keyboard": [[
        {
            "text": "Читати",
            "url": link
        }
    ]]
}

# Відправка
if photo:

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        json={
            "chat_id": CHAT_ID,
            "photo": photo,
            "caption": caption,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        },
        timeout=30
    )

else:

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": title,
            "reply_markup": keyboard
        },
        timeout=30
    )

print(response.status_code)
print(response.text)

response.raise_for_status()

# Збереження останньої новини
state["last_url"] = link

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f)

print("Published:", link)
