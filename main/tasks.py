import feedparser
from django.core.cache import cache
from datetime import datetime
import random
from bs4 import BeautifulSoup
import html

FEED_URLS = [
    "https://escoffieronline.com/feed",
    # add more feeds if needed
]

CACHE_KEY = "career_advice_feed"
CACHE_TIMEOUT = 60 * 60  # 1 hour

FALLBACK_IMAGES = [
    "/static/pictures/food/food1.jpg",
    "/static/pictures/food/food2.jpg",
    "/static/pictures/food/food3.jpg",
    "/static/pictures/food/food4.jpg",
]

def fetch_career_advice():
    """Fetch career advice posts from RSS feeds."""
    posts = []

    for url in FEED_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            # Handle image
            if hasattr(entry, "media_content"):
                image_url = entry.media_content[0]["url"]
            else:
                image_url = random.choice(FALLBACK_IMAGES)

            # Clean summary: remove HTML tags and decode entities
            raw_summary = getattr(entry, "summary", "")
            clean_summary = BeautifulSoup(html.unescape(raw_summary), "html.parser").get_text()
            clean_summary = clean_summary.strip()[:200] + "..."  # truncate to 200 chars

            post = {
                "title": entry.title,
                "link": entry.link,
                "summary": clean_summary,
                "published": getattr(entry, "published", ""),
                "image": image_url
            }
            posts.append(post)

    # Sort newest first
    posts.sort(key=lambda x: x.get("published", datetime.min), reverse=True)

    # Cache
    cache.set(CACHE_KEY, posts, CACHE_TIMEOUT)
    return posts
