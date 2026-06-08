import os
import json
import html
import requests

from bs4 import BeautifulSoup

BASE_URL = "https://mt-news.ru/news/"
STATE_FILE = "state.json"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_url": ""}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def get_latest_news():
    r = requests.get(
        BASE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    news_block = soup.select_one("div[id^='news_list-']")

    if not news_block:
        raise Exception("News list not found")

    first_link = news_block.find("a", href=True)

    if not first_link:
        raise Exception("News link not found")

    url = first_link["href"]

    title_tag = first_link.find("h3")

    title = (
        title_tag.get_text(" ", strip=True)
        if title_tag else ""
    )

    return url, title


def get_article(url):
    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    h1 = soup.select_one("#base-single-area h1")

    if not h1:
        raise Exception("Title not found")

    title = h1.get_text(" ", strip=True)

    content = soup.select_one(
        "#base-single-area .text.margin-top"
    )

    if not content:
        raise Exception("Article content not found")

    for tag in content.find_all(["script", "style"]):
        tag.decompose()

    for div in content.find_all("div"):
        div.decompose()

    image_url = None

    img = content.find("img")

    if img and img.get("src"):
        image_url = img["src"]

    text_parts = []

    for p in content.find_all("p"):

        txt = p.get_text(" ", strip=True)

        if not txt:
            continue

        text_parts.append(txt)

    article_text = "\n\n".join(text_parts)

    return title, article_text, image_url


def send_to_telegram(
    title,
    article_text,
    article_url,
    image_url
):
    title = html.escape(title)

    article_text = article_text[:3500]
    article_text = html.escape(article_text)

    message = (
        f"<b>🏍 MotoGP News</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"<blockquote expandable>"
        f"{article_text}"
        f"</blockquote>"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Читати повністю",
                    "url": article_url
                }
            ]
        ]
    }

    if image_url:

        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            json={
                "chat_id": CHAT_ID,
                "photo": image_url,
                "caption": message,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
            timeout=30,
        )

    else:

        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
            timeout=30,
        )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()


def main():

    state = load_state()

    latest_url, _ = get_latest_news()

    if latest_url == state.get("last_url"):
        print("No new posts")
        return

    title, article_text, image_url = get_article(
        latest_url
    )

    send_to_telegram(
        title,
        article_text,
        latest_url,
        image_url
    )

    state["last_url"] = latest_url

    save_state(state)

    print("Published:", latest_url)


if __name__ == "__main__":
    main()
