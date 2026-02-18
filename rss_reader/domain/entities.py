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
    poll_freq: int = 3 * 60
    active: bool = True


@dataclass
class Article:
    titulo: str
    descripcion: str | None
    fecha_publicacion: datetime | None
    fecha_polling: datetime | None
    creador: str | None
    link: str
    medio: str
    feed_url: str
    article_raw: str = ""
