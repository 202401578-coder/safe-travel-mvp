import feedparser
import requests
import streamlit as st
from urllib.parse import quote
from config import DANGER_KW, BLOCKED_SOURCES


@st.cache_data(ttl=86400)
def translate_to_korean(text: str) -> str:
    try:
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "ko", "dt": "t", "q": text},
            timeout=5,
        )
        return "".join(seg[0] for seg in resp.json()[0] if seg[0])
    except Exception:
        return text


@st.cache_data(ttl=600)
def fetch_safety_news(
    country_name: str, country_eng: str, city_name: str, city_eng: str
) -> list:
    try:
        query = f"{city_eng} OR {city_name} safety crime incident warning"
        url   = f"https://news.google.com/rss/search?q={quote(query)}&hl=en&gl=US&ceid=US:en"
        feed  = feedparser.parse(url)

        location_terms = {country_name.lower(), country_eng.lower(),
                          city_name.lower(), city_eng.lower()}
        articles = []

        for entry in feed.entries[:40]:
            title   = entry.get("title", "")
            source  = entry.get("source", {}).get("title", "")
            title_l = title.lower()

            if any(b.lower() in source.lower() for b in BLOCKED_SOURCES):
                continue
            if not any(t in title_l for t in location_terms):
                continue
            if not any(kw.lower() in title_l for kw in DANGER_KW):
                continue

            articles.append({
                "title":  title,
                "link":   entry.get("link", "#"),
                "pub":    entry.get("published", ""),
                "source": source or "뉴스",
            })

        return articles[:10]
    except Exception:
        return []
