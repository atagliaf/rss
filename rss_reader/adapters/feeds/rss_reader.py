import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from requests import RequestException

from rss_reader.domain.entities import Article, Feed
from rss_reader.domain.ports.rss_reader_port import RssReaderPort


def clean_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(" ", strip=True)


def _parse_datetime(entry) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None)
    if parsed:
        try:
            return datetime(*parsed[:6])
        except (TypeError, ValueError):
            pass
    return None


class RssFeedReader(RssReaderPort):
    """Adapter: lee feeds RSS desde URLs (feedparser + requests)."""

    def fetch(self, feed: Feed) -> list[Article]:
        url = feed.url
        medio = feed.medio

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
        except RequestException as e:
            print(f"Error de red: {e}")
            return []
        except Exception as e:
            print(f"Error leyendo feed {url}: {e}")
            return []

        if parsed.bozo:
            print(f"Feed inválido {url}: {parsed.bozo_exception}")
            return []

        articles = []
        for entry in parsed.entries:
            summary_raw = (
                entry.get("summary")
                or entry.get("description")
                or (entry.get("content", [{}]) or [{}])[0].get("value")
                or ""
            )
            descripcion = clean_html(summary_raw) if summary_raw else None

            fecha_parsed = _parse_datetime(entry)
            creador = (
                entry.get("author")
                or entry.get("dc_creator")
                or parsed.feed.get("author")
                or parsed.feed.get("dc_creator")
                or None
            )

            articles.append(
                Article(
                    titulo=entry.get("title", ""),
                    descripcion=descripcion,
                    fecha_publicacion=fecha_parsed,
                    fecha_polling=datetime.today(),
                    creador=creador,
                    link=entry.get("link", ""),
                    medio=medio,
                    feed_url=url,
                    article_raw=str(entry),
                )
            )
        return articles
