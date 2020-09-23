from multiprocessing.pool import ThreadPool
from constants import RSS_FEEDS, MINUTES_BETWEEN_SCRAPES, MAX_WORKERS
import feedparser
import schedule
import time
import pickle
import traceback
from typing import Dict, List


def rss_single_feed(feed_url: str) -> List[Dict[str, str]]:
    """
    :param feed_url: Url of a rss feed
    :return: feed_news: list of dictionaries
    """
    feed_news = []
    rss_feed = feedparser.parse(feed_url)
    for entry in rss_feed.entries:
        feed_news.append({"title": entry.title, "link": entry.link, "published": entry.published, "source": rss_feed.feed.title})
    return feed_news


def rss_scraper(rss_feeds: list, max_workers: int) -> None:
    """
    :param max_workers: int - threads to run
    :param rss_feeds: list - rss urls
    :return: all_news: list - dictionaries
    """
    try:
        all_news = []
        pool = ThreadPool(max_workers)
        results = pool.map(rss_single_feed, rss_feeds)
        for r in results:
            all_news.extend(r)
        pickle.dump(all_news, open("news_collated.data", "wb"))
    except:
        traceback.print_exc()


def start_scraper():
    rss_scraper(rss_feeds=RSS_FEEDS, max_workers=MAX_WORKERS)
    schedule.every(MINUTES_BETWEEN_SCRAPES).minutes.do(rss_scraper, rss_feeds=RSS_FEEDS, max_workers=MAX_WORKERS)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    start_scraper()
