import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from requests import RequestException

from rss_reader.domain.entities import Article, Feed
from rss_reader.domain.ports.article_read_port import GetArticle


def clean_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(" ", strip=True)


def _get_pub_date(entry) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None)
    if parsed:
        try:
            return datetime(*parsed[:6])
        except (TypeError, ValueError):
            pass
    return None


class GetArticleRss(GetArticle):
    """Adapter: toma la URL de un feed, fetch http y lee todas las noticias,
     Las convierte en Articles y devuelve lista"""

    def read(self, feed: Feed) -> list[Article]:
        url = feed.url
        medio = feed.medio

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            parsed_feed = feedparser.parse(response.content)
        except RequestException as e:
            print(f"Error de red: {e}")
            return []
        except Exception as e:
            print(f"Error leyendo feed {url}: {e}")
            return []

        if parsed_feed.bozo:
            print(f"Feed inválido {url}: {parsed_feed.bozo_exception}")
            return []

        articles = [Article]
        for entry in parsed_feed.entries:
            ## summary
            summary_raw = (
                    entry.get("summary")
                    or entry.get("description")
                    or (entry.get("content") or [{}])[0].get("value")
                    or ""
            )
            resumen = clean_html(summary_raw) if summary_raw else None

            # fecha publicacion
            pub_date = _get_pub_date(entry)

            # periodista
            periodista = (
                    entry.get("author")
                    or entry.get("dc_creator")
                    or parsed_feed.feed.get("author")
                    or parsed_feed.feed.get("dc_creator")
                    or None
            )

            articles.append(
                Article(
                    titulo=entry.get("title"),
                    resumen=resumen,
                    pub_date=pub_date,
                    ingest_date=datetime.today(),
                    periodista=periodista,
                    link=entry.get("link"),
                    medio=medio,
                    feed_url=url,
                    article_raw=str(entry),
                )
            )
        return articles
