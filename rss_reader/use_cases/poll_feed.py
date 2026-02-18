from datetime import datetime

from rss_reader.domain.entities import Article, Feed
from rss_reader.domain.ports.article_repository_port import ArticleRepositoryPort
from rss_reader.domain.ports.rss_reader_port import RssReaderPort
from rss_reader.use_cases.dto import FeedSource


class PollFeed:
    """Caso de uso: leer feeds RSS y persistir artículos."""

    def __init__(self, rss_reader: RssReaderPort, article_repo: ArticleRepositoryPort):
        self.rss_reader = rss_reader
        self.article_repo = article_repo

    def execute(self, feeds: list[FeedSource]) -> list[Article]:
        all_articles = []
        for f in feeds:
            feed = Feed(
                url=f.url,
                medio=f.medio,
            )
            articles = self.rss_reader.fetch(feed)
            if articles:
                self.article_repo.save_batch(articles)
                all_articles.extend(articles)
        return all_articles
