from multiprocessing.pool import ThreadPool
import json
import feedparser
from typing import Dict, List

# Constants
RSS_FEEDS = ["http://www.memeorandum.com/feed.xml", "https://www.rnz.co.nz/rss/national.xml"]
MAX_WORKERS = 10  # Number of threads to use
#


def rss_single_feed(feed_url: str) -> List[Dict[str, str]]:
    """
    :param feed_url: Url of a rss feed
    :return: feed_news: list of dictionaries
    """
    feed_news = []
    rss_feed = feedparser.parse(feed_url)
    for entry in rss_feed.entries:
        feed_news.append({"title": entry.title, "description": entry.description, "link": entry.link, "source": rss_feed.feed.title})
    return feed_news


def rss_scraper(rss_feeds: list, max_workers: int) -> List[Dict[str, str]]:
    """
    :param max_workers: int - threads to run
    :param rss_feeds: list - rss urls
    :return: all_news: list - dictionaries
    """
    all_news = []
    pool = ThreadPool(max_workers)
    results = pool.map(rss_single_feed, rss_feeds)
    for r in results:
        all_news.extend(r)
    return all_news

db = open('db.json', 'w')

if __name__ == "__main__":
    news_list = rss_scraper(RSS_FEEDS, MAX_WORKERS)
    json = json.dumps(news_list)
    db.write(json)
    db.close
        
