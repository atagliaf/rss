"""
Adapter: persistencia en Weaviate con embeddings para búsqueda semántica.

Requiere: pip install weaviate-client

Configuración típica:
- WEAVIATE_URL (ej. http://localhost:8080)
- Colección "Article" con vectorizer (text2vec-openai, text2vec-transformers, etc.)
"""
from pprint import pprint
from pydoc import classname
import weaviate
from rss_reader.domain.entities import Article
from rss_reader.domain.ports.article_repository_port import ArticleRepositoryPort
import traceback
from weaviate.classes.config import Configure, Property, DataType
from pprint import pprint

# WEAVIATE_URL=http://localhost:8080
COLLECTION="news"

class WeaviateArticleRepository(ArticleRepositoryPort):
    """
    Implementación con Weaviate.
    """

    def _helper_create_collection(self) -> None:
        """Crea una colección con auto-embedding"""

        # Abortar si ya existe
        if self.client.collections.exists(self.collection_name):
            print(f"error: intentando crear colección {self.collection_name} prexistente")
            exit(1)

        # Crear la clase
        properties = [
            Property(
                name="content",
                data_type=DataType.TEXT,
                description="Título del artículo + descripción/summary",
                index_filterable=False,  # No necesario para filtrado exacto
                index_searchable=True,  # Se vectoriza para búsqueda semántica
                vectorize=True,
            ),
            # Metadatos (todos indexFilterable=True para filtrado con where)
            Property(
                name="publish_date",
                data_type=DataType.DATE,
                description="Fecha de publicación original",
                index_filterable=True,
                index_searchable=False,
            ),
            Property(
                name="poll_date",
                data_type=DataType.DATE,
                description="Fecha de polling/extracción",
                index_filterable=True,
                index_searchable=False,
            ),
            Property(
                name="source",
                data_type=DataType.TEXT,
                description="Medio de origen",
                index_filterable=True,
                index_searchable=False,
            ),
            Property(
                name="url",
                data_type=DataType.TEXT,
                description="URL del artículo",
                index_filterable=True,
                index_searchable=False,
            ),
            # Campo de almacenamiento (no vectorizado)
            Property(
                name="raw",
                data_type=DataType.TEXT,
                description="Contenido raw del artículo",
                index_filterable=False,
                index_searchable=False,  # No se vectoriza (solo almacenamiento)
            ),
        ]
        try:
            # Definir el schema
            self.client.collections.create(
                self.collection_name,
                description="noticias bajadas feeds rss",
                vector_config=[
                    Configure.Vectors.text2vec_transformers(
                        name="content",
                        source_properties=["content"]
                    )
                ],
                properties=properties
            )
        except Exception as e:
            print(f"Error al crear collection weaviate:\n{e}")
            print("Propiedades de la collection:")
            pprint(properties)
            self.client.close()
            exit(1)
        return

    def __init__(self):
        try:
            self.client = weaviate.connect_to_local()

        except Exception as e:
            print(f"Error conectandose a weaviate local: {e}")
            traceback.print_exc()
            exit(1)
        if self.client.is_ready():
            print(f"conexion weaviate lista: {self.client.get_meta()['hostname']}")
            # pprint(self.client.get_meta())
        else:
            print("Error de conexión")
            exit(1)
        print(f"weaviate version: {weaviate.__version__}")

        self.collection_name = COLLECTION
        if self.client.collections.exists(self.collection_name):
            print(f"Usando collection {self.collection_name}")
            return
        else:
            self._helper_create_collection()

    def save(self, article: Article) -> None:
        properties = {
            "content": article.titulo.lower() + " " + article.descripcion.lower(),
            "publish_date": article.fecha_publicacion,
            "poll_date": article.fecha_polling,
            "source": article.medio,
            "url": article.link,
            "raw": article.article_raw,
        }

        # Obtener la colección
        try:
            collection = self.client.collections.get(self.collection_name)
            result = collection.data.insert(properties=properties)
        except Exception as e:
            print(f"Error al agregar datos a collection weaviate '{self.collection_name}':\n{e}")
            print("Propiedades del objeto:")
            pprint(properties)
            self.client.close()
            exit(1)
        print(f"Artículo guardado con UUID: {result}")
        return

    def save_batch(self, articles: list[Article]) -> None:
        for art in articles:
            self.save(art)
        return

    def seach_proximity(self, concepts: list[str], limit=10, certainty=0.6, source=None, avoid: list[str]|None = None, avoid_force: float|None=0.6):
        """
        Busca artículos por conceptos con filtro opcional de fuente
        """
        # Construir el diccionario near_text base
        near_text_params = {
            "concepts": concepts,
            "certainty": certainty
        }
        if avoid:
            near_text_params["moveAwayFrom"] = {
                "concepts": avoid,
                "force": avoid_force
            }

        query_builder = self.client.query.get(
            self.collection_name,
            ["content"]
        ).with_near_text(near_text_params).with_limit(limit)

        # Añadir filtro si se especifica fuente
        if source:
            query_builder = query_builder.with_where({
                "path": ["source"],
                "operator": "Equal",
                "valueString": source
            })
        response = query_builder.do()

        # Extraer resultados
        if response and "data" in response:
            return response["data"]["Get"][self.collection_name]
        return []


    def find_by_keywords(
        self, keywords: list[str], medio: str | None = None, limit: int = 20
    ) -> list[Article]:
        # TODO: query Weaviate con filtro por keywords
        if self._fallback:
            return self._fallback.find_by_keywords(keywords, medio, limit)
        return self._simple_keyword_search(keywords, medio, limit)

    def find_similar(self, query: str, medio: str | None = None, limit: int = 20) -> list[Article]:
        return self.seach_proximity(self,concepts=query, source=medio, limit=limit)

    def _simple_keyword_search(
        self, keywords: list[str], medio: str | None, limit: int
    ) -> list[Article]:
        result = []
        kw_lower = [k.lower() for k in keywords]
        for a in self._articles:
            if medio and a.medio != medio:
                continue
            texto = f"{(a.titulo or '')} {(a.descripcion or '')}".lower()
            if any(k in texto for k in kw_lower):
                result.append(a)
                if len(result) >= limit:
                    break
        return result
