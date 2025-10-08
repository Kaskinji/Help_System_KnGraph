import json
import glob

def extract_content_from_json(file_path):
    """
    Извлекает поле 'content' из JSON-файла.

    :param file_path: Путь к JSON-файлу
    :return: Текст из поля 'content' или None, если поле отсутствует
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('content')
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: Файл {file_path} не является валидным JSON.")
        return None


# Обработка всех JSON-файлов в папке chunks_1
all_contents = []
for json_file in glob.glob("C:/Users/MSI/PycharmProjects/PythonProject/egor_chunks/chunks_111/*.json"):
    content = extract_content_from_json(json_file)
    if content:
        all_contents.append(content)
