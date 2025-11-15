import feedparser




rss_business = ["https://timesofindia.indiatimes.com/rssfeeds/1898055.cms", 
                "https://www.thehindu.com/business/Economy/feeder/default.rss",
                "https://www.thehindu.com/business/Industry/feeder/default.rss", 
                "https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml", 
                "https://indianexpress.com/section/business/feed/", 
                "https://indianexpress.com/section/business/economy/feed/", 
                "https://feeds.feedburner.com/ndtvprofit-latest"]

rss_sports = ["https://timesofindia.indiatimes.com/rssfeeds/4719148.cms", 
              "https://www.hindustantimes.com/feeds/rss/sports/rssfeed.xml", 
              "https://indianexpress.com/section/sports/feed/", 
              "https://feeds.feedburner.com/ndtvsports-latest"]

rss_cricket = ["https://timesofindia.indiatimes.com/rssfeeds/54829575.cms",
               "https://www.thehindu.com/sport/cricket/feeder/default.rss", 
               "https://www.hindustantimes.com/feeds/rss/cricket/rssfeed.xml", 
               "https://indianexpress.com/section/sports/cricket/feed/", 
                "https://feeds.feedburner.com/ndtvsports-cricket" ]

rss_india = ["https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
              "https://www.thehindu.com/news/national/feeder/default.rss", 
              "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
                "https://indianexpress.com/section/india/feed/", 
                "https://feeds.feedburner.com/ndtvnews-india-news"]

rss_technology = ["https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",
                   "https://www.hindustantimes.com/feeds/rss/technology/rssfeed.xml", 
                   "https://indianexpress.com/section/technology/artificial-intelligence/feed/",
                     "https://indianexpress.com/section/technology/feed/",
                      "https://feeds.feedburner.com/gadgets360-latest", ]

rss_world = ["https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", 
             "https://www.thehindu.com/news/international/feeder/default.rss",
               "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml", 
               "https://indianexpress.com/section/world/feed/",
                "https://feeds.feedburner.com/ndtvnews-world-news" ]

rss_top = ["https://timesofindia.indiatimes.com/rssfeedstopstories.cms", 
           "https://www.hindustantimes.com/feeds/rss/trending/rssfeed.xml",
           "https://indianexpress.com/section/trending/feed/", 
            "https://feeds.feedburner.com/ndtvnews-top-stories" ]



def fetch_rss(url : str):
    feed = feedparser.parse(url)
    return [
        {
            "title": e.title,
            "url": e.link,
            "summary": e.summary if "summary" in e else None,
            "published": e.published if "published" in e else None,
        }
        for e in feed.entries
    ]


