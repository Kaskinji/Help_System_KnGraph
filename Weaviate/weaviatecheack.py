import weaviate

client = weaviate.connect_to_local(host="localhost", port=8081, grpc_port=50051)
collection = client.collections.get("ClientProcessChunks")

# Настройки пагинации
limit = 100  # Количество объектов за один запрос
cursor = None  # Для постраничного вывода
all_objects = []

while True:
    # Делаем запрос с пагинацией
    response = collection.query.fetch_objects(
        limit=limit,
        after=cursor
    )

    if not response.objects:
        break  # Прерываем цикл, если объектов больше нет

    all_objects.extend(response.objects)
    print(f"Загружено {len(response.objects)} объектов")

    if len(response.objects) < limit:
        break  # Это была последняя страница

    # Обновляем курсор для следующей страницы
    cursor = response.objects[-1].uuid

# Выводим все объекты
for i, obj in enumerate(all_objects, 1):
    print(f"\nОбъект #{i}:")
    print(obj.properties)

print(f"\nВсего объектов в коллекции: {len(all_objects)}")
client.close()