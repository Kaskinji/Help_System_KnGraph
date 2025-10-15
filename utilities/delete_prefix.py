import os
import re


def process_ttl_files(folder_path):
    # Паттерн для поиска удаляемых записей
    patterns_to_remove = [
        r'@prefix : <#> \.',
        r'@prefix comcore: <https://kb\.moneta\.ru/terms/common/coreontology#> \.',
        r'@prefix rdf: <http://www\.w3\.org/1999/02/22-rdf-syntax-ns#> \.',
        r'@prefix rdfs: <http://www\.w3\.org/2000/01/rdf-schema#> \.',
        r'# Чанк \d+'  # Изменено для удаления любого чанка (не только "Чанк N")
    ]

    # Компилируем регулярные выражения
    regex_patterns = [re.compile(pattern) for pattern in patterns_to_remove]

    # Получаем список всех .ttl файлов в папке
    for filename in os.listdir(folder_path):
        if filename.endswith('.ttl'):
            file_path = os.path.join(folder_path, filename)

            # Читаем содержимое файла
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Проверяем, есть ли хотя бы одно вхождение удаляемых записей
            found = any(pattern.search(content) for pattern in regex_patterns)

            if not found:
                print(f"Файл {filename} не содержит указанных записей - пропускаем")
                continue

            # Удаляем указанные записи
            modified_content = content
            for pattern in regex_patterns:
                modified_content = pattern.sub('', modified_content)

            # Удаляем пустые строки только в начале файла
            lines = modified_content.split('\n')
            while lines and not lines[0].strip():
                lines.pop(0)
            modified_content = '\n'.join(lines)

            # Записываем изменения обратно в файл только если они отличаются
            if modified_content != content:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(modified_content)
                print(f"Обработан файл: {filename} (внесены изменения)")
            else:
                print(f"Файл {filename} не требует изменений")


if __name__ == "__main__":
    folder_path = input("Введите путь к папке с .ttl файлами: ")

    if os.path.isdir(folder_path):
        process_ttl_files(folder_path)
        print("Обработка завершена.")
    else:
        print("Указанная папка не существует.")