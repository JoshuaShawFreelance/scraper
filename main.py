from multiprocessing.pool import ThreadPool
import feedparser
import schedule
import time
import pickle
from typing import Dict, List

# Constants
RSS_FEEDS = ["http://feeds.bbci.co.uk/news/england/rss.xml", "http://feeds.skynews.com/feeds/rss/uk.xml", "https://www.rnz.co.nz/rss/national.xml", "http://www.memeorandum.com/feed.xml"]
MINUTES_BETWEEN_SCRAPES = 1
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
        feed_news.append({"title": entry.title, "description": entry.description, "link": entry.link, "published": entry.published, "source": rss_feed.feed.title})
        # use entry.published_parsed instead???
    return feed_news


def rss_scraper(rss_feeds: list, max_workers: int) -> None:
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
    pickle.dump(all_news, open("news_collated.data", "wb"))


if __name__ == "__main__":
    schedule.every(MINUTES_BETWEEN_SCRAPES).minutes.do(rss_scraper, rss_feeds=RSS_FEEDS, max_workers=MAX_WORKERS)
    # probably put this in the flask file and just import the scraper
    while True:
        schedule.run_pending()
        time.sleep(1)
