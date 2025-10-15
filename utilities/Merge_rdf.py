import os
from pathlib import Path
import re


def merge_ttl_files(input_dir, output_file):
    """
    Объединяет все TTL-файлы из input_dir в один output_file,
    удаляя дубликаты и сохраняя валидный синтаксис.
    """
    # Собираем все содержимое файлов
    all_content = []
    seen_entities = set()

    # Регулярные выражения для обработки TTL
    entity_pattern = re.compile(r'^:([^\s]+)')
    prefix_pattern = re.compile(r'^@prefix\s+')
    comment_pattern = re.compile(r'^#')
    end_of_statement = re.compile(r'[;.]\s*$')

    # Обрабатываем каждый файл
    for ttl_file in Path(input_dir).glob('*.ttl'):
        with open(ttl_file, 'r', encoding='utf-8') as f:
            current_entity = None
            entity_lines = []

            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Пропускаем префиксы и комментарии
                if prefix_pattern.match(line) or comment_pattern.match(line):
                    continue

                # Находим новые сущности
                entity_match = entity_pattern.match(line)
                if entity_match:
                    entity_name = entity_match.group(1)
                    if current_entity and entity_lines:
                        # Удаляем возможную точку/точку с запятой в последней строке
                        last_line = entity_lines[-1].rstrip(' ;.')
                        entity_lines[-1] = last_line
                        if current_entity not in seen_entities:
                            all_content.append('\n'.join(entity_lines) + ' .\n')
                            seen_entities.add(current_entity)
                        entity_lines = []
                    current_entity = entity_name

                # Удаляем точку/точку с запятой в конце строки (добавим в конце)
                line = line.rstrip(' ;.')
                entity_lines.append(line)

            # Добавляем последнюю сущность из файла
            if current_entity and entity_lines:
                # Удаляем возможную точку/точку с запятой в последней строке
                last_line = entity_lines[-1].rstrip(' ;.')
                entity_lines[-1] = last_line
                if current_entity not in seen_entities:
                    all_content.append('\n'.join(entity_lines) + ' .\n')
                    seen_entities.add(current_entity)

    # Записываем объединенный файл
    with open(output_file, 'w', encoding='utf-8') as f:
        # Добавляем стандартные префиксы
        f.write("@prefix : <http://example.org/ontology#> .\n")
        f.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
        f.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
        f.write("@prefix comcore: <http://example.org/comcore#> .\n\n")

        # Записываем все сущности
        f.write('\n'.join(all_content))

    print(f"Объединено {len(seen_entities)} уникальных сущностей в файл {output_file}")


# Пример использования
input_directory = "C:/Users/MSI/PycharmProjects/PythonProject/triplets1/triplets1"
output_ttl = "merge_rdf.ttl"
merge_ttl_files(input_directory, output_ttl)