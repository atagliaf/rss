# Entidades de dominio: existen independientemente de YAML, RSS, Weaviate, etc.

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Medio:
    nombre: str
    pais: str
    idioma: str
    orientacion_politica: str


@dataclass
class Feed:
    url: str
    medio: str
    last_poll: datetime | None = None
    poll_freq: int = 4 * 60 # in minutes
    active: bool = True     # inhibir polling automatico si False

@dataclass
class Article:
    titulo: str
    resumen: str | None
    pub_date: datetime | None
    ingest_date: datetime | None
    periodista: str | None
    link: str
    medio: str
    feed_url: str
    article_raw: str = ""
