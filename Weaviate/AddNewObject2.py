import json
import os

import weaviate
from weaviate import Client
from weaviate.classes.config import Property, DataType

def populate_weaviate_collection(client: Client, chunks_dir: str):

    chunks_collection = client.collections.get("ClientProcessChunks5")

    # 2. Читаем все JSON-файлы в указанной директории
    for filename in os.listdir(chunks_dir):
        if not filename.endswith('.json'):
            continue

        with open(os.path.join(chunks_dir, filename), 'r', encoding='utf-8') as f:
            try:
                chunk_data = json.load(f)

                # 3. Подготавливаем данные для вставки
                properties = {
                    "content": chunk_data["content"],
                    "chunk_id": chunk_data["id"],
                    "type": chunk_data.get("type", "")
                }

                # 4. Добавляем объект в коллекцию
                chunks_collection.data.insert(
                    properties=properties,
                    # vector=vector
                )

                print(f"Добавлен чанк: {chunk_data['id']}")

            except Exception as e:
                print(f"Ошибка при обработке {filename}: {str(e)}")


if __name__ == "__main__":
    CHUNKS_DIR = "C:/Users/MSI/PycharmProjects/PythonProject/chunks_2"
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )
    populate_weaviate_collection(client, CHUNKS_DIR)
    print("Загрузка чанков завершена")