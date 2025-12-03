import weaviate
from weaviate.classes.query import MetadataQuery

def search(name, entity):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    ) # Подключаюсь к ВБД Weaviate

    collection = client.collections.get(name) # Подключаюсь к конкретной коллекции
    statements_str = " ".join(entity["hasStatement"])

    # Формирую запрос из полей сущности
    query_parts = [
        entity["uri"],
    ]

    # Объединяю непустые части в одну строку
    query_text = " ".join(filter(None, query_parts))

    # Фильтр по классу
    class_filter = weaviate.classes.query.Filter.by_property("type").equal(entity["type"])

    # Гибридный поиск с фильтром
    response = collection.query.hybrid(
        query=query_text,
        alpha=0.5,
        query_properties=["label"],
        filters=class_filter,
        return_metadata=MetadataQuery(score=True),
        limit=1
    )
    client.close()
    if len(response.objects) > 0:
      if entity["uri"] == response.objects[0].properties["uri"] or response.objects[0].metadata.score >= 0.8:
        print(f"Нашёл score: {response.objects[0].metadata.score}")
        return response.objects[0]  # Возвращаем найденный объект
    return None