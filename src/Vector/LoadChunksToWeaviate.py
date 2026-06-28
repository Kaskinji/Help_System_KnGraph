import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any

import weaviate
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.exceptions import WeaviateConnectionError

COLLECTION_NAME = "DocumentChunks"
DEFAULT_LIMIT = 10

RETURN_PROPERTIES = [
    "chunk_id",
    "document_id",
    "title",
    "abstract",
    "content",
    "section",
    "chapter",
    "chunk_type",
]


@dataclass
class SearchResult:
    rank: int
    chunk_id: str
    document_id: str
    title: str
    abstract: str
    content: str
    section: str
    chapter: str
    chunk_type: str
    distance: float
    score: float

    @property
    def certainty(self) -> float:
        return (1.0 + self.score) / 2.0

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует результат в словарь для JSON-сериализации."""
        data = asdict(self)
        data["certainty"] = self.certainty
        return data


def connect_to_weaviate():
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051,
        )
        if not client.is_ready():
            print("❌ Weaviate не готов")
            client.close()
            return None
        return client
    except WeaviateConnectionError as e:
        print(f"❌ Ошибка подключения к Weaviate: {e}")
        return None


def cosine_similarity(distance: float) -> float:
    """Косинусное сходство из косинусного расстояния Weaviate (distance = 1 - similarity)."""
    return 1.0 - distance


def search_chunks(
    query: str,
    limit: int = DEFAULT_LIMIT,
    collection_name: str = COLLECTION_NAME,
    document_id: Optional[str] = None,
) -> List[SearchResult]:
    """
    Векторный поиск по near_text. Результаты отсортированы по score (убывание).
    """
    client = connect_to_weaviate()
    if client is None:
        return []

    if not client.collections.exists(collection_name):
        print(f"❌ Коллекция '{collection_name}' не существует")
        client.close()
        return []

    collection = client.collections.get(collection_name)

    filters = None
    if document_id:
        filters = Filter.by_property("document_id").equal(document_id)

    try:
        response = collection.query.near_text(
            query=query,
            limit=limit,
            filters=filters,
            return_properties=RETURN_PROPERTIES,
            return_metadata=MetadataQuery(distance=True),
        )
    finally:
        client.close()

    results: List[SearchResult] = []
    for rank, obj in enumerate(response.objects, start=1):
        props = obj.properties
        distance = obj.metadata.distance if obj.metadata.distance is not None else 2.0
        results.append(
            SearchResult(
                rank=rank,
                chunk_id=props.get("chunk_id", ""),
                document_id=props.get("document_id", ""),
                title=props.get("title", ""),
                abstract=props.get("abstract", ""),
                content=props.get("content", ""),
                section=props.get("section", ""),
                chapter=props.get("chapter", ""),
                chunk_type=props.get("chunk_type", ""),
                distance=distance,
                score=cosine_similarity(distance),
            )
        )

    return results


def load_queries_from_file(file_path: Path) -> Dict[str, Dict[str, str]]:
    """Загружает запросы из JSON-файла."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_results_to_file(
    results: List[SearchResult],
    query_id: str,
    query_text: str,
    output_dir: Path,
) -> None:
    """Сохраняет результаты поиска в JSON-файл."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "query_id": query_id,
        "query": query_text,
        "total_results": len(results),
        "results": [r.to_dict() for r in results]
    }
    
    # Очищаем имя файла от недопустимых символов
    safe_filename = query_id.replace(" ", "_").replace("/", "_")
    output_path = output_dir / f"{safe_filename}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Сохранено: {output_path}")


def process_queries(
    queries_file: Path,
    output_dir: Path,
    limit: int = DEFAULT_LIMIT,
    collection_name: str = COLLECTION_NAME,
    document_id: Optional[str] = None,
) -> None:
    """
    Обрабатывает все запросы из файла и сохраняет результаты.
    """
    # Загружаем запросы
    queries = load_queries_from_file(queries_file)
    print(f"📁 Загружено {len(queries)} запросов из {queries_file}")
    print("=" * 80)
    
    # Обрабатываем каждый запрос
    for query_id, query_data in queries.items():
        query_text = query_data.get("query", "")
        if not query_text:
            print(f"⚠️ Пропуск {query_id}: пустой запрос")
            continue
        
        print(f"\n🔍 Обработка: {query_id}")
        print(f"   Запрос: {query_text}")
        
        # Выполняем поиск
        results = search_chunks(
            query=query_text,
            limit=limit,
            collection_name=collection_name,
            document_id=document_id,
        )
        
        print(f"   Найдено: {len(results)} результатов")
        
        # Сохраняем результаты
        save_results_to_file(results, query_id, query_text, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ Все запросы обработаны!")


def main():
    parser = argparse.ArgumentParser(
        description="Пакетный семантический поиск чанков по JSON-файлу с запросами"
    )
    parser.add_argument(
        "queries_file",
        type=str,
        help='Путь к JSON-файлу с запросами. Формат: {"q1": {"query": "текст"}, ...}',
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="search_results",
        help="Папка для сохранения результатов (по умолчанию: search_results)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Количество результатов на запрос (по умолчанию: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--document-id",
        type=str,
        default=None,
        help="Ограничить поиск одним документом (document_id)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=COLLECTION_NAME,
        help=f"Имя коллекции Weaviate (по умолчанию: {COLLECTION_NAME})",
    )

    args = parser.parse_args()
    
    queries_path = Path(args.queries_file)
    if not queries_path.exists():
        print(f"❌ Файл не найден: {queries_path}")
        return
    
    output_dir = Path(args.output_dir)
    
    process_queries(
        queries_file=queries_path,
        output_dir=output_dir,
        limit=args.limit,
        collection_name=args.collection,
        document_id=args.document_id,
    )


if __name__ == "__main__":
    main()