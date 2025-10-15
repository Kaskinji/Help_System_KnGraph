import weaviate
from weaviate.classes.config import Configure, Tokenization
import weaviate.classes as wvc

# Стандартный порт для подключения к БД, это 8080. Но так как в docker-compose мы указали свободные порт 8081, то необходимо принудительно передать аргумент
client = weaviate.connect_to_local(
    host="localhost",
    port=8081,
    grpc_port=50051,
)
try:
    client.collections.delete("ClientProcessChunks")
    collection = client.collections.create(
        name="ClientProcessChunks", # название коллекции
        properties=[
            wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT, description="Текст чанка"
            ),
            wvc.config.Property(
                name="chunk_id", data_type=wvc.config.DataType.TEXT, skip_vectorization=True
            ),
            wvc.config.Property(
                name="type", data_type=wvc.config.DataType.TEXT, index_filterable=True
            ),
            wvc.config.Property(
                name="source", data_type=wvc.config.DataType.TEXT, index_filterable=True
            ),
            wvc.config.Property(
                name="keywords", data_type=wvc.config.DataType.TEXT_ARRAY
            )
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_transformers(

            pooling_strategy="masked_mean"  # Лучше для коротких текстов
        )
    )
finally:
    print('Collection created')
    client.close()
