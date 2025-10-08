import json
import os
from typing import List

# Константы
MAX_CHUNK_SIZE = 2500
SOURCE_FILE = "../Source_texts/b2boffer.txt"
API_KEY = "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"
OUTPUT_DIR = "../chunks_1"

def llm_request(prompt: str, api_key: str) -> str:
    try:
        import requests
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "deepseek/deepseek-r1-0528:free",
                "messages": [{"role": "user", "content": prompt}],
            })
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        return f"Ошибка при запросе: {str(e)}"

def split_text_into_paragraphs(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    paragraphs = [p.strip() for p in content.split("|||") if p.strip()]
    return paragraphs

def process_paragraphs(paragraphs: List[str], api_key: str) -> str:
    text_splited_result = ""

    for paragraph in paragraphs:
        prompt = f"""Раздели текст ниже на чанки по правилам:
1. Максимальный размер чанка - {MAX_CHUNK_SIZE} символов. ЧАНК ДОЛЖЕН БЫТЬ СТРОГО НЕ БОЛЬШЕ  {MAX_CHUNK_SIZE} СИМВОЛОВ.
2. Чанк должен включать в себя полностью целые абзацы, недопустимо, чтобы абзац начинался в одном чанке.
4. Между чанками ставь разделитель "%%%".
5. Сохраняй оригинальное форматирование.
6. Не добавляй заголовков или комментариев.
Текст для обработки:
{paragraph}"""

        response = llm_request(prompt, api_key)

        if text_splited_result:
            text_splited_result += "%%%"  # Добавляем разделитель между результатами
        text_splited_result += response

    return text_splited_result

def save_chunks_to_json(text: str, source: str):
    """Сохраняет чанки из текста (разделитель '%%%') в JSON-файлы."""
    chunks = [chunk.strip() for chunk in text.split("%%%") if chunk.strip()]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i, chunk in enumerate(chunks, 1):
        chunk_data = {
            "id": f"chunk_{i:02d}",
            "source": source,
            "content": chunk,
            "size": len(chunk)
        }
        with open(f"{OUTPUT_DIR}/chunk_{i:02d}.json", "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)


paragraphs = split_text_into_paragraphs(SOURCE_FILE)
print(f"Найдено параграфов: {len(paragraphs)}")

# 2. Обрабатываем каждый параграф через LLM
text_splited_result = process_paragraphs(paragraphs, API_KEY)

# 3. Сохраняем чанки в JSON
save_chunks_to_json(text_splited_result, SOURCE_FILE)
print(f"Сохранено чанков: {len(text_splited_result.split('%%%'))}")