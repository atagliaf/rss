from abc import ABC, abstractmethod

from rss_reader.domain.entities import Article, Feed


class GetArticle(ABC):
    """Puerto para leer feeds RSS desde una URL."""

    @abstractmethod
    def read(self, feed: Feed) -> list[Article]:
        """Obtiene los artículos desde la URL del feed."""