import weaviate

def check_collections():
    client = weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,
    )
    
    # Получить список всех коллекций
    collections = client.collections.list_all()
    
    print("📚 Список всех коллекций:")
    for name in collections:
        print(f"  - {name}")
    
    # Проверить конкретную коллекцию
    collection_name = "DocumentChunks"  # или ваше название
    if client.collections.exists(collection_name):
        collection = client.collections.get(collection_name)
        count = collection.aggregate.over_all().total_count
        print(f"\n✅ Коллекция '{collection_name}' существует")
        print(f"   Количество объектов: {count}")
    else:
        print(f"\n❌ Коллекция '{collection_name}' не найдена")
    
    client.close()
    return collections

# Запустить проверку
check_collections()