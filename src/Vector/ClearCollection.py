import weaviate

def quick_clear(collection_name: str = "DocumentChunks"):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,
    )
    
    if client.collections.exists(collection_name):
        collection = client.collections.get(collection_name)
        count = collection.aggregate.over_all().total_count
        print(f"🗑️ Очистка {collection_name}... (было {count} объектов)")
        
        # ✅ Используем delete_where
        result = collection.data.delete_where(
            where={"path": ["chunk_id"], "operator": "Like", "valueText": "*"}
        )
        print(f"   Удалено: {result}")
        
        # Проверяем
        count_after = collection.aggregate.over_all().total_count
        print(f"   Осталось: {count_after}")
        print(f"✅ Коллекция очищена")
    else:
        print(f"❌ Коллекция {collection_name} не существует")
    
    client.close()

if __name__ == "__main__":
    quick_clear()