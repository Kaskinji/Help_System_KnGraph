import weaviate
import json
from weaviate.classes.query import Filter

def populate_weaviate_collection(file_name, collection, CHUNKS_DIR):
    with open(f"{CHUNKS_DIR}/{file_name}", 'r', encoding='utf-8') as f:
        entities = json.load(f)

    for entity in entities:
        properties = {
            "chunk_id": entity.get("chunk_id", ""),
            "label": entity.get("label", ""),
            "definition": entity.get("definition", ""),
            "abbreviation": entity.get("abbreviation", []),
            "hasStatement": entity.get("hasStatement", []),
            "type": entity.get("type", "")
        }

        collection.data.insert(properties=properties)

