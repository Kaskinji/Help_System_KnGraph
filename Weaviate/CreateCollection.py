import weaviate
from weaviate.classes.config import Configure, Tokenization
import weaviate.classes as wvc


def Create_Collection(client, collection_name):
    try:
        client.collections.delete(f"{collection_name}")
        collection = client.collections.create(
            name=f"{collection_name}", # название коллекции
            properties=[
                wvc.config.Property(
                    name="chunk_id",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="label",  # имя свойства
                    data_type=wvc.config.DataType.TEXT,  # тип данных
                    vectorize_property_name=True,  # векторизируем это свойство
                    tokenization=Tokenization.LOWERCASE,  # токенизация по нижнему регистру
                    index_filterable=True,  # индексация для фильтрации
                    index_searchable=True,  # индексация для поиска
                ),
                wvc.config.Property(
                    name="definition",
                    data_type=wvc.config.DataType.TEXT,
                    vectorize_property_name=True,
                    tokenization=Tokenization.LOWERCASE,
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="abbreviation",
                    data_type=wvc.config.DataType.TEXT_ARRAY,
                    vectorize_property_name=True,
                    tokenization=Tokenization.LOWERCASE,
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="hasStatement",
                    data_type=wvc.config.DataType.TEXT_ARRAY,
                    vectorize_property_name=True,
                    tokenization=Tokenization.LOWERCASE,
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="type",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,  # не векторизируем
                ),
            ],
            vectorizer_config=Configure.Vectorizer.text2vec_transformers()
        )
    finally:
        print('Collection created')


client = weaviate.connect_to_local(
    host="localhost",
    port=8081,
    grpc_port=50051,
)

collection_name = "saas"

Create_Collection(client, collection_name)

client.close()