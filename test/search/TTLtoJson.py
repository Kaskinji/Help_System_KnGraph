import re

def parse_ttl_to_json(ttl_content: str):
    entities = {}
    statements = []

    # Удаляем комментарии и префиксы
    alhpabet = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    ttl_content = ttl_content.replace("\ufeff", "")
    ttl_content = ttl_content.replace("\u200c", "")
    lines = [line.strip() for line in ttl_content.split('\n')
             if line.strip() and not line.strip().startswith(('@prefix', '#', '`')) and line.strip()[0] not in alhpabet]

    # Объединяем многострочные записи
    records = []
    current_record = []
    for line in lines:
        current_record.append(line)
        if line.endswith('.'):
            records.append(' '.join(current_record).rstrip(' .'))
            current_record = []

    # Обрабатываем каждую запись
    for record in records:
        # Извлекаем субъект (название сущности)
        subject_match = re.match(r'^:?([^\s]+)', record)
        if not subject_match:
            continue
        entity_id = subject_match.group(1).lower()[:40]

        # Извлекаем тип сущности
        type_match = re.search(r'rdf:type\s+comcore:(\w+)', record)
        entity_type = type_match.group(1) if type_match else 'Unknown'

        # Извлекаем метку
        label_match = re.search(r'rdfs:label\s+"([^"]+)"@?ru?', record)
        label = label_match.group(1).replace("_", " ") if label_match else entity_id

        # Извлекаем abbreviation (если есть)
        abbrev_match = re.search(r'comcore:abbreviation\s+"([^"]+)"', record)
        abbreviation = abbrev_match.group(1) if abbrev_match else ""

        # Извлекаем definition (если есть)
        definition_match = re.search(r'dc:definition\s+"([^"]+)"', record)
        definition = definition_match.group(1) if definition_match else ""

        # Создаем структуру для сущности
        entities[entity_id] = {
            "uri": entity_id,
            "label": label,
            "abbreviation": abbreviation,
            "definition": definition,
            "chunks": [],
            "type": entity_type,
            "hasStatement": []
        }

        # Извлекаем все отношения hasPart
        has_part_matches = re.finditer(r'comcore:hasPart\s+:([^\s,;]+)', record)
        for match in has_part_matches:
            target = match.group(1)
            statements.append(f"{entity_id} hasPart {target}")
            statements.append(f"{target} isPartOf {entity_id}")

        # Извлекаем все отношения isPartOf
        is_part_of_matches = re.finditer(r'comcore:isPartOf\s+:([^\s,;]+)', record)
        for match in is_part_of_matches:
            target = match.group(1)
            statements.append(f"{entity_id} isPartOf {target}")
            statements.append(f"{target} hasPart {entity_id}")

        # Извлекаем все отношения isActorOf
        is_actor_of_matches = re.finditer(r'comcore:isActorOf\s+:([^\s,;]+)', record)
        for match in is_actor_of_matches:
            target = match.group(1)
            statements.append(f"{entity_id} isActorOf {target}")
            statements.append(f"{target} hasActor {entity_id}")

        # Извлекаем все отношения isResourceOf
        is_resource_of_matches = re.finditer(r'comcore:isResourceOf\s+:([^\s,;]+)', record)
        for match in is_resource_of_matches:
            target = match.group(1)
            statements.append(f"{entity_id} isResourceFor {target}")
            statements.append(f"{target} hasResource {entity_id}")

        # Извлекаем все отношения isResultOf
        is_result_of_matches = re.finditer(r'comcore:isResultOf\s+:([^\s,;]+)', record)
        for match in is_result_of_matches:
            target = match.group(1)
            statements.append(f"{entity_id} isResultOf {target}")
            statements.append(f"{target} hasResult {entity_id}")

        # Извлекаем отношения из списков
        list_matches = re.finditer(r'(comcore:\w+)\s+((?::[^\s,]+\s*,\s*)+:[^\s,;]+)', record)
        for match in list_matches:
            rel_type = match.group(1).split(':')[-1]
            targets = [t.strip().strip(':') for t in match.group(2).split(',')]
            for target in targets:
                if target:
                    if rel_type == "hasPart":
                        statements.append(f"{entity_id} hasPart {target}")
                        statements.append(f"{target} isPartOf {entity_id}")
                    elif rel_type == "isActorOf":
                        statements.append(f"{entity_id} isActorOf {target}")
                        statements.append(f"{target} hasActor {entity_id}")
                    elif rel_type == "isResourceOf":
                        statements.append(f"{entity_id} isResourceFor {target}")
                        statements.append(f"{target} hasResource {entity_id}")

    # Распределяем statements по соответствующим сущностям
    for stmt in statements:
        parts = stmt.split()
        if len(parts) >= 3:
            subject = ' '.join(parts[:-2])
            if subject in entities:
                entities[subject]["hasStatement"].append(stmt)
    return list(entities.values())
