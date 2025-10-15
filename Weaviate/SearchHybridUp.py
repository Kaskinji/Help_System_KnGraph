import weaviate
from weaviate.classes.query import MetadataQuery
import json
import re

def search_hybrid_up(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        entities = json.load(f)
        print(f"Загружено {len(entities)} сущностей")

    # Подключение к Weaviate
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )
    
    try:
        collection = client.collections.get("Knowledge_graph1")
        all_results = []

        for entity in entities:
            # Формируем запрос из доступных полей
            query_parts = [
                entity.get("label", ""),
                entity.get("abbreviation", ""),
            ]
            query_text = " ".join(filter(None, query_parts))
            entity_type = entity.get("type")
            
            class_filter = weaviate.classes.query.Filter.by_property("type").equal(entity_type) if entity_type else None

            try:
                response = collection.query.hybrid(
                    query=query_text,
                    alpha=0.4,
                    query_properties=["label^2", "definition"],
                    filters=class_filter,
                    return_metadata=MetadataQuery(score=True),
                    limit=5
                )

                for obj in response.objects:
                    if obj.metadata.score > 0.5:
                        label = obj.properties.get("label", obj.properties.get("name", "N/A"))
                        definition = obj.properties.get("definition", "No definition available")
                        score = obj.metadata.score
                        
                        if definition: 
                            result_str = f"{entity.get('label', '')}({label}) - {definition} (score: {score:.2f})\n"
                            all_results.append(result_str)
                            # Убрал return здесь, чтобы обработать все сущности

            except Exception as e:
                all_results.append(f"Ошибка при поиске для {entity.get('label', 'N/A')}: {str(e)}")
        
        return "".join(all_results) if all_results else "Не найдено подходящих результатов"
    
    finally:
        client.close()  # Гарантированное закрытие соединения