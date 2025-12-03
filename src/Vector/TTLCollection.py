import weaviate
from weaviate.classes.config import Tokenization, Configure
import weaviate.classes as wvc

def ttl_collection(bd_name):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )
    if client.collections.exists(bd_name):
        client.collections.delete(bd_name)
    collection = client.collections.create(
        name=bd_name, # название коллекции
            properties=[
            wvc.config.Property(
                name="uri",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
            ),
            wvc.config.Property(
                name="label", # имя атрибута
                data_type=wvc.config.DataType.TEXT, # тип данных атрибута
                vectorize_property_name=True,# векторизовать этот атрибут? (True/False)
                tokenization=Tokenization.LOWERCASE, # токенизация происходит под нижним регистром "Папа -> папа"
                index_filterable=True, # фильтрация для инвертированного индекса? (True/False)
                index_searchable=True, # поиск для инвертированного индекса? (True/False)
            ),
            wvc.config.Property(
                name="abbreviation",
                data_type=wvc.config.DataType.TEXT,
                vectorize_property_name=True,
                tokenization=Tokenization.LOWERCASE,
                index_filterable=True,
                index_searchable=True,
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
                name="chunks",
                data_type=wvc.config.DataType.TEXT_ARRAY,
                vectorize_property_name=True,
                index_filterable=True,
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
                skip_vectorization=True,
            ),
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_transformers()
    )
    print(f"Коллекция {bd_name} создана!")
    client.close()