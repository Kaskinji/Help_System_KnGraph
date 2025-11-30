import json
import requests
import os
from typing import List, Dict
import glob


def parse_with_llm_backup(prompt: str) -> str:
    try:
        api_key = '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'
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            })
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Ошибка {response.status_code}: {response.text}"

    except Exception as e:
        return f"Ошибка при запросе: {str(e)}"


def save_qa_to_json(qa_pairs: List[Dict], output_dir: str):
    """
    Сохраняет QA пары в отдельные JSON файлы
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    saved_files = []
    for qa in qa_pairs:
        filename = f"chunk_{qa['id']}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as json_file:
            json.dump(qa, json_file, ensure_ascii=False, indent=4)

        saved_files.append(filename)

    return saved_files


def process_single_file(file_path: str, output_base_dir: str):
    """
    Обрабатывает один файл и создает JSON файлы
    """
    filename = os.path.basename(file_path)
    print(f"Обработка файла: {filename}")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Используем LLM для обработки
        prompt = f"""
Проанализируй следующий текст и извлеки все пары вопрос-ответ. 
Вопрос - это абзац, который идёт всегда перед ответом, вопрос начинаются с цифры  (например: "1. Как...?").
Ответы идут сразу после вопросов. В итоге весь файл представляет пары типа вопрос - ответ.

Текст:
{content}

Верни результат в формате JSON списка, где каждый элемент имеет структуру:
{{
    "id": номер_вопроса,
    "query": "полный текст вопроса",
    "content": "полный текст ответа"
}}

ВАЖНО: Верни ТОЛЬКО JSON без каких-либо дополнительных текстов, комментариев или объяснений. В поле querry не добавляй нумерацию вопроса, только текст вопроса. Поле "id" определяется по порядковому номеру обработанной пары(НЕ ПО НОМЕРУ ВОПРОСА) - то есть первая пара будет иметь id = 1, вторая - 2 и тд.
Пример правильного ответа:
[
    {{
        "id": 1,
        "query": "Как зарегистрировать заявку на подключение в системе Монета.ру?",
        "content": "Условие начала процесса Подключения: Клиент регистрируется на сайте PAW..."
    }},
    {{
        "id": 2, 
        "query": "Как узнать, что регистрация клиента в системе Монета.ру прошла успешно?",
        "content": "Если регистрация прошла успешно (Клиент корректно заполнил все поля), то..."
    }}
]
"""
        result = parse_with_llm_backup(prompt)
        print(f"Получен ответ от LLM: {result[:200]}...")  # Логируем начало ответа

        # Парсим JSON ответ от LLM
        try:
            # Очищаем ответ от возможных лишних символов
            result_clean = result.strip()
            # Убираем возможные markdown коды ```json ... ```
            if result_clean.startswith('```json'):
                result_clean = result_clean[7:]
            if result_clean.endswith('```'):
                result_clean = result_clean[:-3]
            result_clean = result_clean.strip()

            qa_pairs = json.loads(result_clean)
            # Если это не список, а один объект, оборачиваем в список
            if isinstance(qa_pairs, dict):
                qa_pairs = [qa_pairs]

            print(f"Успешно распарсено {len(qa_pairs)} QA пар")

        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON от LLM для файла {filename}: {e}")
            print(f"Сырой ответ: {result}")
            return 0

        # Создаем папку для выходных файлов
        output_dir = os.path.join(output_base_dir, os.path.splitext(filename)[0])
        saved_files = save_qa_to_json(qa_pairs, output_dir)

        print(f"Успешно обработан файл {filename}: создано {len(saved_files)} JSON файлов")
        return len(qa_pairs)

    except Exception as e:
        print(f"Ошибка при обработке файла {filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def process_all_txt_files(input_folder: str, output_base_dir: str = "json_output"):
    input_folder = os.path.abspath(input_folder)
    if not os.path.exists(input_folder):
        print(f"Ошибка: Папка '{input_folder}' не существует!")
        return

    # Ищем все txt файлы в папке
    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))

    if not txt_files:
        print(f"В папке '{input_folder}' не найдено txt файлов!")
        return

    print(f"Найдено {len(txt_files)} txt файлов для обработки...")

    total_qa_pairs = 0
    processed_files = 0

    for file_path in txt_files:
        qa_count = process_single_file(file_path, output_base_dir)
        if qa_count > 0:
            processed_files += 1
            total_qa_pairs += qa_count
        print("-" * 50)

    print(f"Обработка завершена!")
    print(f"Успешно обработано файлов: {processed_files}/{len(txt_files)}")
    print(f"Всего создано QA пар: {total_qa_pairs}")


def main():
    print("Запуск извлечения чанков из всех txt файлов в папке...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(current_dir, "QuestionForTesting")
    output_base_dir = os.path.join(current_dir, "json_output")

    print(f"Входная папка: {input_folder}")
    print(f"Выходная папка: {output_base_dir}")

    os.makedirs(output_base_dir, exist_ok=True)

    process_all_txt_files(input_folder, output_base_dir)

if __name__ == "__main__":
    main()