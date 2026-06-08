import os
import json
import html
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://mt-news.ru/"
STATE_FILE = "state.json"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"last_url": ""}


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_latest_news_url():
    r = requests.get(BASE_URL, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    article = soup.select_one(
        "a.border.border-radius.padding"
    )

    if not article:
        raise Exception("News block not found")

    href = article.get("href")

    return urljoin(BASE_URL, href)


def get_article(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # ПІСЛЯ ТЕСТУ МОЖЕ ЗНАДОБИТИСЯ ЗМІНИТИ СЕЛЕКТОРИ
    title_tag = soup.find("h1")

    if not title_tag:
        raise Exception("Title not found")

    title = title_tag.get_text(" ", strip=True)

    text_parts = []

    article_container = soup.find("article")

    if article_container:
        paragraphs = article_container.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    for p in paragraphs:
        txt = p.get_text(" ", strip=True)

        if len(txt) > 20:
            text_parts.append(txt)

    article_text = "\n".join(text_parts)

    return title, article_text


def send_to_telegram(title, text, url):
    title = html.escape(title)
    text = html.escape(text[:3500])

    message = (
        f"<b>🏍 MotoGP News</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"<blockquote expandable>"
        f"{text}"
        f"</blockquote>"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Читати повністю",
                    "url": url
                }
            ]
        ]
    }

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
            "disable_web_page_preview": False
        },
        timeout=30
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()


def main():
    state = load_state()

    latest_url = get_latest_news_url()

    if latest_url == state.get("last_url"):
        print("No new news")
        return

    title, article_text = get_article(latest_url)

    send_to_telegram(
        title,
        article_text,
        latest_url
    )

    state["last_url"] = latest_url
    save_state(state)


if __name__ == "__main__":
    main()
