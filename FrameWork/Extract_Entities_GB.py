import json
import requests
import os
from prompts.Prompt2 import prompt
import time
def llm_request(full_prompt: str, api_key: str) -> str:
    try:
        time.sleep(10)
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "openai/gpt-5-mini",
                "messages": [{"role": "user", "content": full_prompt}],
                "temperature": 0.1
            })
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Ошибка {response.status_code}: {response.text}"

    except Exception as e:
        return f"Ошибка при запросе: {str(e)}"


def create_prompt(content: str, query: str) -> str:
    prompt_template = f'''
        {prompt}
        КОНТЕКСТ ЗАПРОСА КЛИЕНТА:
        {query}
        ТЕКСТ ДЛЯ ИЗВЛЕЧЕНИЯ: 
        {content}
        '''
    return prompt_template


def extract_entities_from_chunk(content: str, query: str, api_key: str) -> str:

    full_prompt = create_prompt(content, query)
    return llm_request(full_prompt, api_key)


def save_ttl_result(ttl_content: str, output_path: str):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ttl_content)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении TTL файла {output_path}: {e}")
        return False


def process_single_json_file(json_file_path: str, output_dir: str, api_key: str) -> bool:
    try:

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        content = data.get('content', '')
        chunk_id = data.get('id', 'unknown')
        query = data.get('query', '')

        if not content:
            print(f"⚠️ В файле {json_file_path} нет поля 'content'")
            return False

        print(f"🔍 Обработка чанка {chunk_id}...")

        print(f"  📨 Отправка запроса к LLM...")
        ttl_result = extract_entities_from_chunk(content, query, api_key)

        if ttl_result.startswith("Ошибка"):
            print(f"  ❌ Ошибка LLM: {ttl_result}")
            return False

        base_name = os.path.basename(json_file_path).replace('.json', '')
        ttl_filename = f"{base_name}.ttl"
        ttl_path = os.path.join(output_dir, ttl_filename)

        if save_ttl_result(ttl_result, ttl_path):
            print(f"  ✅ Успешно сохранен: {ttl_filename}")
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ Ошибка при обработке файла {json_file_path}: {e}")
        return False


def find_all_json_files(input_folder: str) -> list:
    json_files = []

    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))

    return json_files


def process_all_json_files(input_folder: str, output_dir: str, api_key: str):

    os.makedirs(output_dir, exist_ok=True)
    json_files = find_all_json_files(input_folder)

    if not json_files:
        print(f"❌ В папке '{input_folder}' не найдено JSON файлов!")
        return

    print(f"📁 Найдено {len(json_files)} JSON файлов для обработки...")

    successful_processed = 0
    failed_processed = 0

    for json_file in json_files:
        success = process_single_json_file(json_file, output_dir, api_key)

        if success:
            successful_processed += 1
        else:
            failed_processed += 1

        print("-" * 60)

    print(f"🎉 Обработка завершена!")
    print(f"✅ Успешно обработано: {successful_processed} файлов")
    print(f"❌ Не удалось обработать: {failed_processed} файлов")
    print(f"📊 Общее количество: {len(json_files)} файлов")


def main():
    print("🚀 Запуск извлечения сущностей из JSON файлов...")
    API_KEY = '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'

    INPUT_FOLDER = "json_output_test"
    OUTPUT_DIR = "ttl_output_gpt5mini"
    process_all_json_files(INPUT_FOLDER, OUTPUT_DIR, API_KEY)

if __name__ == "__main__":
    main()