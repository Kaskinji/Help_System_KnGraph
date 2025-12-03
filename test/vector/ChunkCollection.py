import weaviate
from weaviate.classes.config import Tokenization, Configure
import weaviate.classes as wvc

def chunk_collection(bd_name):
    # Стандартный порт для подключения к БД, это 8080. Но так как в docker-compose мы указали свободные порты 8081, то необходимо принудительно передать аргумент
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )
    if client.collections.exists(bd_name):
        client.collections.delete(bd_name)
    # Здесь создаём БД (коллекцию), перечисляем необходимые нам атрибуты у сущности
    collection = client.collections.create(
        name=bd_name, # название коллекции
            properties=[
            wvc.config.Property(
                name="id",  # имя атрибута
                data_type=wvc.config.DataType.TEXT,  # тип данных атрибута
                skip_vectorization=False,  # векторизовать этот атрибут? (True/False)
            ),
            wvc.config.Property(
                name="text", # имя атрибута
                data_type=wvc.config.DataType.TEXT, # тип данных атрибута
                vectorize_property_name=True,# векторизовать этот атрибут? (True/False)
                tokenization=Tokenization.LOWERCASE, # токенизация происходит под нижним регистром "Папа -> папа"
                index_filterable=True, # фильтрация для инвертированного индекса? (True/False)
                index_searchable=True, # поиск для инвертированного индекса? (True/False)
            )
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_transformers()
    )
    print(f"Коллекция {bd_name} создана!")
    client.close()