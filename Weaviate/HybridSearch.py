import sys

# Добавляем путь к папке проекта в sys.path
sys.path.append(str('/Users/ilya/Documents/GitHub/Help_System_Moneta'))  # или явно: sys.path.append("/полный/путь/к/ваш_проект")


import weaviate
from weaviate.classes.query import HybridFusion
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from typing import List, Dict
from Entities_extraction.Extract_Entities_Querry import extract_entities_from_chunk2

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

client = weaviate.connect_to_local(
    host="localhost",
    port=8081,
    grpc_port=50051,
)

def extract_relevant_part(text: str, query: str, min_similarity: float = 0.7) -> str:
    sentences = re.split(r'([.!?]\s+)', text)
    sentences = [sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else '')
                 for i in range(0, len(sentences), 2) if sentences[i].strip()]

    if not sentences:
        return ""

    query_embedding = model.encode(query)
    sentence_embeddings = model.encode([re.sub(r'[.!?]\s*$', '', s) for s in sentences])

    similarities = cosine_similarity([query_embedding], sentence_embeddings)[0]

    first_relevant_idx = next(
        (i for i, score in enumerate(similarities) if score >= min_similarity),
        -1
    )

    if first_relevant_idx == -1:
        return sentences[np.argmax(similarities)].strip()

    relevant_part = ''.join(sentences[first_relevant_idx:]).strip()
    relevant_part = re.sub(r'(?<!\w)\.(?!\s|$)', '', relevant_part)

    return relevant_part

def search_precise_answer(user_query: str, limit: int = 1):
    try:
        chunks_collection = client.collections.get("ClientProcessChunks")
        response = chunks_collection.query.hybrid(
            query=user_query,
            fusion_type=HybridFusion.RELATIVE_SCORE,
            limit=limit,
            alpha=0.7,
            return_metadata=["score"],
            return_properties=["content", "chunk_id"]
        )

        if not response.objects:
            return {"status": "not_found", "message": "Ответ не найден"}

        best_chunk = response.objects[0]
        relevant_part = extract_relevant_part(
            best_chunk.properties["content"],
            user_query,
            min_similarity=0.6
        )

        if not relevant_part:
            relevant_part = "Точный ответ не найден в документе. Обратитесь к эксперту."

        return {
            "status": "success",
            "answer": relevant_part,
            "source": best_chunk.properties["chunk_id"],
            "score": best_chunk.metadata.score
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
