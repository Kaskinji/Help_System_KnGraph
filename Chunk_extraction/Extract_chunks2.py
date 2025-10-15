import json
import os
import re
from typing import List, Dict
import PyPDF2
import requests
from tqdm import tqdm

# Конфигурация
API_KEY = "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"
OUTPUT_DIR = "/2text_chunks/chunks2"
CHUNK_TARGET_SIZE = 1000  # Примерный размер чанка в символах
MODEL = "anthropic/claude-3-haiku"  # Более качественная модель для анализа


def llm_chunking_request(text: str, api_key: str) -> List[Dict]:
    """Запрос к LLM для структурированного разбиения текста"""
    prompt = f"""Проанализируй текст и раздели его на тематические чанки. Каждый чанк должен содержать:
- Законченную мысль/процедуру
- Относиться к одному из типов: registration, rejection, verification, agreement, process_description
- Сохранять оригинальный текст без изменений
- Чанк должен включать в себя полностью целые абзацы, недопустимо, чтобы абзац начинался в одном чанке.

Верни ответ в формате JSON:
{{
  "chunks_1": [
    {{
      "id": "уникальный_ид",
      "content": "текст",
      "type": "тип_чанка",
      "size": число_символов
    }}
  ]
}}

Требования:
 - нигде не обрезай текст. Чанки во совокупности должны представлять весь исходный текст без исключения.
Текст для обработки:
{text[:5000]}"""  # Ограничиваем размер для одного запроса

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }),
            timeout=60
        )

        if response.status_code == 200:
            return json.loads(response.json()['choices'][0]['message']['content'])["chunks_1"]
        else:
            print(f"Ошибка API: {response.status_code}")
            return []
    except Exception as e:
        print(f"Ошибка запроса: {str(e)}")
        return []


def extract_text_from_pdf(pdf_path: str) -> str:
    """Извлекает текст из PDF с сохранением структуры"""
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return clean_text(text)


def clean_text(text: str) -> str:
    """Очистка текста от лишних пробелов и переносов"""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def process_large_text(text: str, api_key: str) -> List[Dict]:
    """Обработка больших текстов с разбиением на части"""
    chunks = []
    total_size = len(text)
    processed = 0

    with tqdm(total=total_size, desc="Обработка текста") as pbar:
        while processed < total_size:
            chunk_end = min(processed + 10000, total_size)  # Ограничение на размер запроса
            text_part = text[processed:chunk_end]

            result = llm_chunking_request(text_part, api_key)
            if result:
                chunks.extend(result)

            processed = chunk_end
            pbar.update(chunk_end - processed)

    return merge_small_chunks(chunks)


def merge_small_chunks(chunks: List[Dict], min_size=300) -> List[Dict]:
    """Объединение слишком маленьких чанков"""
    merged = []
    temp_chunk = None

    for chunk in chunks:
        if temp_chunk is None:
            temp_chunk = chunk.copy()
        elif len(temp_chunk["content"]) < min_size and temp_chunk["type"] == chunk["type"]:
            temp_chunk["content"] += "\n\n" + chunk["content"]
            temp_chunk["size"] = len(temp_chunk["content"])
        else:
            merged.append(temp_chunk)
            temp_chunk = chunk.copy()

    if temp_chunk:
        merged.append(temp_chunk)

    return merged


def save_chunks(chunks: List[Dict], source_name: str):
    """Сохранение чанков в JSON файлы"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i, chunk in enumerate(chunks, 1):
        chunk["id"] = f"chunk_{i:03d}"
        chunk["source"] = source_name

        with open(f"{OUTPUT_DIR}/{chunk['id']}.json", "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)


def process_pdf(pdf_path: str, api_key: str):
    """Основной процесс обработки PDF"""
    print(f"Обработка файла: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    print(f"Извлечено {len(text)} символов")

    chunks = process_large_text(text, api_key)
    print(f"Сгенерировано {len(chunks)} тематических чанков")

    save_chunks(chunks, os.path.basename(pdf_path))
    print(f"Чанки сохранены в {OUTPUT_DIR}")


if __name__ == "__main__":
    pdf_path = "/connecting_client.pdf"
    process_pdf(pdf_path, API_KEY)