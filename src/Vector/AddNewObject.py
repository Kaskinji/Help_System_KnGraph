import weaviate
import json
from weaviate.classes.query import Filter
import SearchHybridUp

def add_new_object(bd_name, json_path):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )

    # Чтение данных из JSON-файла
    with open(json_path, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    collection = client.collections.get(bd_name)

    for entity in entities:
        # Маппинг полей из Entity.json в структуру Weaviate
        new_properties = {
            "uri": entity.get("uri", ""),
            "label": entity.get("label", ""),
            "abbreviation": entity.get("abbreviation", ""),
            "definition": entity.get("definition", ""),
            "chunks": entity.get("chunks", []),
            "hasStatement": entity.get("hasStatement", []),
            "type": entity.get("type", ""),
        }

        # Поиск существующего объекта
        response = SearchHybridUp.search(bd_name, entity)

        if response is None:
            # Если объекта нет — добавляем новый
            collection.data.insert(properties=new_properties)
            print(f"Добавлен объект: {new_properties["uri"]}")
        else:
            # Если объект уже существует — обновляем его
            existing_uuid = response.uuid
            existing_properties = response.properties


            # Объединяем chunks и hasStatement
            updated_chunks = list(set(existing_properties["chunks"] + new_properties["chunks"]))
            updated_has_statement = list(set(existing_properties["hasStatement"] + new_properties["hasStatement"]))
            if existing_properties["definition"] != "":
                updated_definition = new_properties["definition"]
            else:
                updated_definition = ""

            if existing_properties["abbreviation"] != "":
                updated_abbreviation = new_properties["abbreviation"]
            else:
                updated_abbreviation = ""

            # Обновляем только нужные поля
            collection.data.update(
                uuid=existing_uuid,
                properties={
                    "chunks": updated_chunks,
                    "hasStatement": updated_has_statement,
                    "definition": updated_definition,
                    "abbreviation": updated_abbreviation
                }
            )
            print(f"ОБНОВЛЕНИЕ ОБЪЕКТ: {existing_properties["uri"]} СОЕДИНИЛ С {new_properties["uri"]}")
    # Статистика
    current_count = collection.aggregate.over_all(total_count=True).total_count
    print(f"\nИтоговое количество объектов: {current_count}")

    client.close()
