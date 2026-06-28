import weaviate
from weaviate.classes.config import Tokenization, Configure, VectorDistances
import weaviate.classes as wvc

def create_chunk_collection(bd_name: str = "DocumentChunks"):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,
    )
    
    # Удаляем существующую коллекцию
    if client.collections.exists(bd_name):
        client.collections.delete(bd_name)
        print(f"🗑️ Коллекция {bd_name} удалена")
    
    collection = client.collections.create(
        name=bd_name,
        properties=[
            # === ИДЕНТИФИКАТОРЫ ===
            wvc.config.Property(
                name="chunk_id",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                index_filterable=True,
                index_searchable=False,
                description="Уникальный идентификатор чанка (например p_1_1)",
            ),
            wvc.config.Property(
                name="document_id",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                index_filterable=True,
                index_searchable=False,
                description="ID документа (например СМК-ПИ-3.01-07-2015)",
            ),
            
            # === ГЛАВНОЕ ПОЛЕ ДЛЯ ВЕКТОРИЗАЦИИ ===
            wvc.config.Property(
                name="search_text",
                data_type=wvc.config.DataType.TEXT,
                vectorize_property_name=False,
                tokenization=Tokenization.WHITESPACE,
                index_filterable=False,
                index_searchable=True,
                description="Составное поле: тип + заголовок + аннотация + контент (векторизуется)",
            ),
            
            # === ПОЛЯ ДЛЯ ПОИСКА И ФИЛЬТРАЦИИ ===
            wvc.config.Property(
                name="title",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                tokenization=Tokenization.LOWERCASE,
                index_filterable=True,
                index_searchable=True,
                description="Заголовок чанка",
            ),
            wvc.config.Property(
                name="abstract",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                tokenization=Tokenization.LOWERCASE,
                index_filterable=False,
                index_searchable=True,
                description="Краткая аннотация чанка",
            ),
            
            # === ПОЛЯ С ТЕКСТОМ (НЕ ВЕКТОРИЗУЮТСЯ, НО ИНДЕКСИРУЮТСЯ ДЛЯ ПОИСКА) ===
            wvc.config.Property(
                name="content",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                tokenization=Tokenization.WHITESPACE,
                index_filterable=False,
                index_searchable=True,
                description="Полный текст чанка (для отображения и текстового поиска)",
            ),
            
            # === СТРУКТУРНЫЕ МЕТАДАННЫЕ ===
            wvc.config.Property(
                name="section",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                index_filterable=True,
                index_searchable=False,
                description="Номер раздела (например 1.1)",
            ),
            wvc.config.Property(
                name="chapter",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                index_filterable=True,
                index_searchable=False,
                description="Номер главы (например 1)",
            ),
            wvc.config.Property(
                name="chunk_type",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                index_filterable=True,
                index_searchable=False,
                description="Тип чанка: list, rule, procedure, definition, reference",
            ),
            
            # === ЧИСЛОВЫЕ ПОЛЯ ===
            wvc.config.Property(
                name="size",
                data_type=wvc.config.DataType.INT,
                skip_vectorization=True,
                index_filterable=True,
                index_searchable=False,
                description="Размер чанка в символах",
            ),
            wvc.config.Property(
                name="serial",
                data_type=wvc.config.DataType.INT,
                skip_vectorization=True,
                index_filterable=True,
                index_searchable=False,
                description="Порядковый номер чанка в документе",
            ),
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE,
        ),
    )
    
    print(f"✅ Коллекция {bd_name} создана!")
    print(f"   Векторизатор: text2vec-transformers")
    client.close()
    return collection

if __name__ == "__main__":
    create_chunk_collection("DocumentChunks")