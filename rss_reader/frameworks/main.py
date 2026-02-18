# 📌 Wiring: acá se mezcla capas (framework, adapters, use cases).

import argparse
import yaml
from sys import exit

from rss_reader.adapters.cli.controller import CliController
from rss_reader.adapters.feeds.rss_reader import RssFeedReader
from rss_reader.adapters.persistence.memory_repo import MemoryArticleRepository
from rss_reader.adapters.persistence.weaviate_repository import WeaviateArticleRepository
from rss_reader.use_cases.dto import FeedSource
from rss_reader.use_cases.poll_feed import PollFeed
from rss_reader.use_cases.search_news import SearchNews


def load_feeds(path: str) -> list[FeedSource]:
    """
    :param path: file con el yaml listando medios y feeds
    :return: lista feeds como objetos FeedSource

    Omite los feeds:
        - Que no tengan novedad desde el poll anterior (guarda ultimo poll en FEED_LAST)
        - Que tengan "poll: False" o cuyos medios tengan "activo: False".
    En este ejemplo, devuelve FeedSource unicamente para linea 5; omite 7, 14 y 16
        $ head medios.yaml
         1	        medios:
         2	          - nombre: clarin
         3	            pais: Argentina
         4	            feeds:
         5	              - url: https://www.clarin.com/rss/lo-ultimo/
         6	                poll: True
         7	              - url: https://www.clarin.com/rss/politica/
         8	                poll: False
         9
        10	          - nombre: El Universal
        11	            pais: México
        12	            activo: False
        13	            feeds:
        14	              - url: https://eluniversal.com.mx/rss/principal.xml
        15	                poll: True
        16                - url: https://eluniversal.com.mx/rss/cdmx.xml
        17                  poll: True
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            datos = yaml.safe_load(f)

    except Exception as e:
        print(f"Error leyendo feed file '{path}': {e}")
        exit(1)

    FEED_LAST= '.last_poll'
    sources: list[FeedSource] = []
    for medio in datos['medios']:
        if medio.get('activo', True) == False:
            # print(f"debug> Medio inactivo, salteando: {medio['nombre']}")
            continue
        for feed in medio.get('feeds', []):
            if feed.get('poll', True) == False:
                # print(f"debug> Feed inactivo, saltenado:  {feed['url']}")
                continue
            sources.append(FeedSource(medio=medio['nombre'], url=feed['url']))
    #print(f"debug> sources:\n{sources}")
    return sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feeds", default="medios.yaml")
    parser.add_argument("--medio")
    parser.add_argument("--keywords", nargs="*")
    parser.add_argument("--semantic", help="Búsqueda por similitud semántica")
    parser.add_argument("--show_summary", action="store_true")
    args = parser.parse_args()

    feeds = load_feeds(args.feeds)

    # Wiring
    rss_reader = RssFeedReader()                    # como se bajan feeds de Internet
    article_repo = WeaviateArticleRepository()        # como persisto las noticias (tiene metodos "save", "save_batch")
    poll_uc = PollFeed(rss_reader, article_repo)    # implementa uc leer feeds y persistir
    search_uc = SearchNews(article_repo)            # implementa uc buscar en el repositorio persistido
    controller = CliController()

    articles = poll_uc.execute(feeds)

    if args.keywords or args.semantic:
        results = search_uc.execute(
            medio=args.medio,
            keywords=args.keywords,
            semantic_query=args.semantic,
        )
    # else:
    #     results = [a for a in articles if not args.medio or a.medio == args.medio]

    controller.show(results, summary=args.show_summary)


if __name__ == "__main__":
    main()
