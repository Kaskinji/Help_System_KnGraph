import weaviate
import json
from typing import Optional
from weaviate.classes.query import MetadataQuery


def check_weaviate_collection(collection_name, output_file):
    try:
        # Подключаемся к Weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=8081,
            grpc_port=50051
        )

        # Проверяем подключение
        if not client.is_ready():
            print("Ошибка: Не удалось подключиться к Weaviate")
            return

        # Проверяем существование коллекции
        available_collections = client.collections.list_all()
        if collection_name not in available_collections:
            print(f"Ошибка: Коллекция '{collection_name}' не найдена!")
            print(f"Доступные коллекции: {available_collections}")
            return

        # Получаем коллекцию
        collection = client.collections.get(collection_name)
        properties = ["label", "abbreviation", "definition", "chunks", "type", "hasStatement"]
        # Получаем объекты
        response = collection.query.fetch_objects(
            limit=2000,
            return_properties=properties,
            return_metadata=None,
            include_vector=False
        )

        # Подготавливаем данные для сохранения
        result = []
        for obj in response.objects:
            result.append(obj.properties)

        # Сохраняем в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Успешно! Проверено {len(result)} объектов")
        print(f"Результат сохранён в: {output_file}")
        client.close()

    except Exception as e:
        print(f"Ошибка при проверке коллекции: {str(e)}")
        client.close()



