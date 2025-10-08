import json
import os
from pathlib import Path


def merge_json_files(input_folder, output_file):
    """
    Объединяет все JSON-файлы из папки в один файл

    :param input_folder: Путь к папке с JSON-файлами
    :param output_file: Путь для сохранения объединенного файла
    """
    merged_data = []
    processed_files = 0
    duplicate_count = 0

    # Проверяем существование папки
    if not os.path.exists(input_folder):
        print(f"Ошибка: Папка {input_folder} не существует")
        return

    # Собираем все JSON-файлы в папке
    json_files = list(Path(input_folder).glob('*.json'))
    if not json_files:
        print(f"В папке {input_folder} не найдено JSON-файлов")
        return

    # Обрабатываем каждый файл
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Проверяем, что файл содержит список объектов
                if isinstance(data, list):
                    for item in data:
                        # Проверяем дубликаты по label и chunk_id
                        if not any(existing['label'] == item['label'] and
                                   existing['chunk_id'] == item['chunk_id']
                                   for existing in merged_data):
                            merged_data.append(item)
                        else:
                            duplicate_count += 1
                    processed_files += 1
                else:
                    print(f"Файл {json_file.name} не содержит список объектов")
        except Exception as e:
            print(f"Ошибка при обработке файла {json_file.name}: {str(e)}")

    # Сохраняем объединенный результат
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    # Выводим статистику
    print(f"\nОбработка завершена:")
    print(f"- Обработано файлов: {processed_files}")
    print(f"- Найдено дубликатов: {duplicate_count}")
    print(f"- Всего уникальных записей: {len(merged_data)}")
    print(f"- Объединенный файл сохранен как: {output_file}")


# Пример использования
if __name__ == "__main__":
    input_folder = "C:/Users/MSI/PycharmProjects/PythonProject/json_triplets"  # Замените на ваш путь
    output_file = "merge_json.json"  # Имя выходного файла

    merge_json_files(input_folder, output_file)