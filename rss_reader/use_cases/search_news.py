from rss_reader.domain.entities import Article
from rss_reader.domain.ports.article_repository_port import ArticleRepositoryPort


class SearchNews:
    """Caso de uso: buscar noticias por keywords o por similitud semántica."""

    def __init__(self, article_repo: ArticleRepositoryPort):
        self.article_repo = article_repo

    def execute(
        self,
        medio: str | None = None,
        keywords: list[str] | None = None,
        semantic_query: str | None = None,
        limit: int = 20,
    ) -> list[Article]:
        if semantic_query:
            return self.article_repo.find_similar(
                query=semantic_query, medio=medio, limit=limit
            )
        if keywords:
            return self.article_repo.find_by_keywords(
                keywords=keywords, medio=medio, limit=limit
            )
        return []
