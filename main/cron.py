from .utils import fetch_career_feeds

def update_career_feeds():
    print("Updating career RSS feeds...")
    fetch_career_feeds()
    print("Career feeds updated.")
