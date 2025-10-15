import CreateCollection, AddNewObject
import weaviate
from weaviate.classes.query import MetadataQuery
import json
import os

CHUNKS_DIR = "../../json_triplets"
COLLECTION_NAME = "Knowledge_graph_text1_final"

client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )

client.collections.delete("Knowledge_graph_text1_final")
CreateCollection.Create_Collection(client, COLLECTION_NAME)
collection = client.collections.get(COLLECTION_NAME)

files = [f for f in os.listdir(CHUNKS_DIR) if f.endswith('.json')]
AddNewObject.populate_weaviate_collection(files[0], collection, CHUNKS_DIR)

for filename in files[1:]:
    with open(f"{CHUNKS_DIR}/{filename}", "r", encoding="utf-8") as f:
        test_entity = json.load(f)
        print(f"Загружено {len(test_entity)} сущностей из {filename}")

    for i, entity in enumerate(test_entity):
        query_parts = [
            entity["label"],
            entity["abbreviation"],
        ]
        query_text = " ".join(filter(None, query_parts))
        print(f"Поиск для сущности: {entity['label']}, query: {query_text}, type: {entity['type']}")

        class_filter = weaviate.classes.query.Filter.by_property("type").equal(entity["type"])

        response = collection.query.hybrid(
            query=query_text,
            alpha=0.4,
            query_properties=["label", "hasStatement", "abbreviation", "definition"],
            filters=class_filter,
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit=1
        )

        new_properties = {
            "chunk_id": entity.get("chunk_id", ""),
            "label": entity.get("label", ""),
            "definition": entity.get("definition", ""),
            "abbreviation": entity.get("abbreviation", []),
            "hasStatement": entity.get("hasStatement", []),
            "type": entity.get("type", "")
        }

        if len(response.objects) == 0 or response.objects[0].metadata.score < 0.7:
            collection.data.insert(properties=new_properties)
            print(f"Добавлен объект: {entity['label']}")

        else:
            existing_obj = response.objects[0]
            existing_uuid = existing_obj.uuid
            existing_properties = existing_obj.properties

            updated_chunks_id = f"{existing_properties["chunk_id"]} {new_properties["chunk_id"]}".strip()
            updated_has_statement = list(set(existing_properties["hasStatement"] + new_properties["hasStatement"]))
            updated_abbreviation = list(set(existing_properties["abbreviation"] + new_properties["abbreviation"]))
            updated_definition = f"{existing_properties["definition"]} {new_properties["definition"]}".strip()

            if new_properties["label"] != existing_properties["label"] and new_properties["label"] not in existing_properties["abbreviation"]:
                updated_abbreviation.append(new_properties["label"])

            collection.data.update(
                uuid=existing_uuid,
                properties={
                    "chunks_id": updated_chunks_id,
                    "hasStatement": updated_has_statement,
                    "abbreviation": updated_abbreviation,
                    "definition": updated_definition,
                }
            )
            print(f"Обновлен объект: {existing_properties['label']}")

client.close()