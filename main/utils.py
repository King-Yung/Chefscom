# main/utils.py
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import UserOTP
import feedparser
from datetime import datetime
from django.utils.timezone import make_aware
from .models import CareerAdvice
from bs4 import BeautifulSoup
import html

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(user):
    otp = generate_otp()
    UserOTP.objects.update_or_create(user=user, defaults={"otp_code": otp})

    subject = "🔐 Your Login OTP - chefs.com.ng"
    message = f"Hello {user.first_name},\n\nYour one-time password (OTP) is: {otp}\n\nThis code expires in 5 minutes.\n\n- chefs.com.ng Team"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])



RSS_FEEDS = [
    "https://escoffieronline.com/feed/",
    # Add more culinary feeds here
]

def fetch_career_feeds():
    for feed_url in RSS_FEEDS:
        parsed = feedparser.parse(feed_url)

        for entry in parsed.entries:
            title = entry.title
            link = entry.link
            summary_html = getattr(entry, "summary", "")

            # Clean summary: remove all HTML tags and decode HTML entities
            summary_text = BeautifulSoup(html.unescape(summary_html), "html.parser").get_text()
            summary_text = summary_text.strip()[:200] + "..."  # limit to 200 chars

            # Published date
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = make_aware(datetime(*entry.published_parsed[:6]))
            else:
                published = make_aware(datetime.now())

            # Extract image
            image = None

            if hasattr(entry, "media_thumbnail"):
                image = entry.media_thumbnail[0]["url"]
            elif hasattr(entry, "media_content"):
                image = entry.media_content[0]["url"]
            elif hasattr(entry, "enclosures") and len(entry.enclosures) > 0:
                image = entry.enclosures[0].href

            if not image:
                soup = BeautifulSoup(summary_html, "html.parser")
                img_tag = soup.find("img")
                if img_tag and img_tag.get("src"):
                    image = img_tag["src"]

            # Fallback default image
            if not image:
                image = "/static/pictures/blog/default.jpg"

            # Avoid duplicates
            if not CareerAdvice.objects.filter(link=link).exists():
                CareerAdvice.objects.create(
                    title=title,
                    link=link,
                    summary=summary_text,
                    image=image,
                    published=published,
                )