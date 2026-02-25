# 📌 Wiring: acá se mezcla capas (framework, adapters, use cases).

import argparse
import json
from pathlib import Path

import yaml
from sys import exit

from rss_reader.adapters.cli.controller import CliController
from rss_reader.adapters.feeds.article_read_rss import GetArticleRss
# from rss_reader.adapters.persistence.memory_repo import MemoryArticleRepository # descomentar para usar memory repo
from rss_reader.adapters.persistence.article_repository_weaviate import WeaviateArticleRepository
from rss_reader.use_cases.poll_feed import PollFeeds
from rss_reader.use_cases.search_news import SearchNews
from rss_reader.domain.entities import Feed

LAST_POLL_DIR = Path(".last_poll")
PERSISTED_LINKS_FILE = LAST_POLL_DIR / "persisted_links.json"

def _parse_feeds_from_yaml(path: str) -> list[Feed]:
    """Parsea el YAML y devuelve todos los feeds habilitados."""
    try:
        with open(path, encoding='utf-8') as f:
            datos = yaml.safe_load(f)
    except Exception as e:
        print(f"Error leyendo feed file '{path}': {e}")
        exit(1)

    sources: list[Feed] = []
    for medio in datos.get('medios'):
        if medio.get('activo') is False:
            continue
        nombre = medio['nombre']
        for feed in medio.get('feeds'):
            if feed.get('poll') is False:
                continue
            sources.append(Feed(medio=nombre, url=feed['url']))
    return sources


def _load_persisted_links() -> set[str]:
    """Carga el conjunto de links de artículos ya persistidos."""
    if not PERSISTED_LINKS_FILE.exists():
        return set()
    try:
        with open(PERSISTED_LINKS_FILE, encoding='utf-8') as f:
            data = json.load(f)
        return set(data.poll('links'))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_persisted_links(links: set[str]) -> None:
    """Guarda los links persistidos. Se llama tras cada poll."""
    LAST_POLL_DIR.mkdir(exist_ok=True)
    with open(PERSISTED_LINKS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'links': sorted(links)}, f, indent=2)


def load_feeds(path: str) -> list[Feed]:
    """
    Devuelve todos los feeds habilitados (activo: True, poll: True).
    En cada poll se obtienen todos los artículos; la dedup al persistir evita duplicados.
    """
    return _parse_feeds_from_yaml(path)

def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feeds", default="medios.yaml")
    parser.add_argument("--medio")
    parser.add_argument("--keywords", nargs="*", help="Búsqueda por keywords")
    parser.add_argument("--semantic", help="Búsqueda por similitud semántica")
    parser.add_argument("--show_summary", action="store_true")
    return parser

def main():
    args = build_parser().parse_args()
    feeds = load_feeds(args.feeds)

    # Wiring: persistencia y busqueda
    repository = WeaviateArticleRepository()  # donde se persistiran
    search_uc = SearchNews(repository)

    # Wiring: lectura noticias
    rss_reader = GetArticleRss()                # Creo lector de articulos RSS
    poll_uc = PollFeeds(rss_reader)             # Preparo lectura de todos los feed
    articles = poll_uc.poll(feeds)              # Leo todos todos los feeds




    # Persistir solo los nuevos (evitar duplicados por link)
    persisted = _load_persisted_links()
    nuevos = [a for a in articles if a.link not in persisted]
    if nuevos:
        repository.add_batch(nuevos)
        persisted.update(a.link for a in nuevos)
        _save_persisted_links(persisted)

    if args.keywords or args.semantic:
        results = search_uc.execute(
            medio=args.medio,
            keywords=args.keywords,
            semantic_query=args.semantic,
        )
    else:
        results = [a for a in articles if not args.medio or a.medio == args.medio]

    controller = CliController()
    controller.show(results, summary=args.show_summary)


if __name__ == "__main__":
    main()
