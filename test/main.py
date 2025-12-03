import os
import re
import json
import weaviate
import warnings
import requests
import weaviate.classes as wvc
from weaviate.classes.config import Tokenization, Configure
from weaviate.classes.query import MetadataQuery

warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

# Вывод колекции weaviate в файл
def print_weaviate_collection(collection_name, output_file):
    try:
        # Подключаемся к Weaviate
        client = weaviate.connect_to_local(
            host="localhost",
            port=8081,
            grpc_port=50051
        )

        # Проверяем подключение
        if not client.is_ready():
            print("Ошибка: Не удалось подключиться к Weaviate")
            return

        # Проверяем существование коллекции
        available_collections = client.collections.list_all()
        if collection_name not in available_collections:
            print(f"Ошибка: Коллекция '{collection_name}' не найдена!")
            print(f"Доступные коллекции: {available_collections}")
            return

        # Получаем коллекцию
        collection = client.collections.get(collection_name)
        properties = ["label", "abbreviation", "definition", "chunks", "type", "hasStatement"]
        # Получаем объекты
        response = collection.query.fetch_objects(
            limit=2000,
            return_properties=properties,
            return_metadata=None,
            include_vector=False
        )

        # Подготавливаем данные для сохранения
        result = []
        for obj in response.objects:
            result.append(obj.properties)

        # Сохраняем в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Успешно! Проверено {len(result)} объектов")
        print(f"Результат сохранён в: {output_file}")
        client.close()

    except Exception as e:
        print(f"Ошибка при проверке коллекции: {str(e)}")
        client.close()

# Функция превращает файл TTL в Json файл
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

# Прохождение по папке с TTL и создание Json файлов с форматом Weaviate Base (TTL, CQ и Chunks)
def create_json_file():
    for i in os.listdir("../data/ttl_cache"):
        with open(os.path.join("../data/ttl_cache", i), "r", encoding="utf-8") as f:
            with open(os.path.join("../data/json_cache", i[:-3]) + "json", "w", encoding="utf-8") as w:
                json_ttl = parse_ttl_to_json(f.read())
                json.dump(json_ttl, w, ensure_ascii=False, indent=2)

# Создание векторной базы для TTL
def ttl_collection(bd_name):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )
    if client.collections.exists(bd_name):
        client.collections.delete(bd_name)
    client.collections.create(
        name=bd_name, # название коллекции
            properties=[
            wvc.config.Property(
                name="uri",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
            ),
            wvc.config.Property(
                name="label", # имя атрибута
                data_type=wvc.config.DataType.TEXT, # тип данных атрибута
                vectorize_property_name=True,# векторизовать этот атрибут? (True/False)
                tokenization=Tokenization.LOWERCASE, # токенизация происходит под нижним регистром "Папа -> папа"
                index_filterable=True, # фильтрация для инвертированного индекса? (True/False)
                index_searchable=True, # поиск для инвертированного индекса? (True/False)
            ),
            wvc.config.Property(
                name="abbreviation",
                data_type=wvc.config.DataType.TEXT,
                vectorize_property_name=True,
                tokenization=Tokenization.LOWERCASE,
                index_filterable=True,
                index_searchable=True,
            ),
            wvc.config.Property(
                name="definition",
                data_type=wvc.config.DataType.TEXT,
                vectorize_property_name=True,
                tokenization=Tokenization.LOWERCASE,
                index_filterable=True,
                index_searchable=True,
            ),
            wvc.config.Property(
                name="chunks",
                data_type=wvc.config.DataType.TEXT_ARRAY,
                vectorize_property_name=True,
                index_filterable=True,
            ),
            wvc.config.Property(
                name="hasStatement",
                data_type=wvc.config.DataType.TEXT_ARRAY,
                vectorize_property_name=True,
                tokenization=Tokenization.LOWERCASE,
                index_filterable=True,
                index_searchable=True,
            ),
            wvc.config.Property(
                name="type",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
            ),
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_transformers()
    )
    print(f"Коллекция {bd_name} создана!")
    client.close()

# Добавление объекта в векторную базу
def add_new_object(bd_name, json_path):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    )

    # Чтение данных из JSON-файла
    with open(json_path, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    collection = client.collections.get(bd_name)

    for entity in entities:
        # Маппинг полей из Entity.json в структуру Weaviate
        new_properties = {
            "uri": entity.get("uri", ""),
            "label": entity.get("label", ""),
            "abbreviation": entity.get("abbreviation", ""),
            "definition": entity.get("definition", ""),
            "chunks": entity.get("chunks", []) + [json_path.split("/")[-1]],
            "hasStatement": entity.get("hasStatement", []),
            "type": entity.get("type", ""),
        }

        # Поиск существующего объекта
        response = search(bd_name, entity)

        if response is None:
            # Если объекта нет — добавляем новый
            collection.data.insert(properties=new_properties)
            print(f"Добавлен объект: {new_properties["uri"]}")
        else:
            # Если объект уже существует — обновляем его
            existing_uuid = response.uuid
            existing_properties = response.properties


            # Объединяем chunks и hasStatement
            updated_chunks = list(set(existing_properties["chunks"] + new_properties["chunks"]))
            updated_has_statement = list(set(existing_properties["hasStatement"] + new_properties["hasStatement"]))
            if existing_properties["definition"] != "":
                updated_definition = new_properties["definition"]
            else:
                updated_definition = ""

            if existing_properties["abbreviation"] != "":
                updated_abbreviation = new_properties["abbreviation"]
            else:
                updated_abbreviation = ""

            # Обновляем только нужные поля
            collection.data.update(
                uuid=existing_uuid,
                properties={
                    "chunks": updated_chunks,
                    "hasStatement": updated_has_statement,
                    "definition": updated_definition,
                    "abbreviation": updated_abbreviation
                }
            )
            print(f"ОБНОВЛЕНИЕ ОБЪЕКТ: {existing_properties["uri"]} СОЕДИНИЛ С {new_properties["uri"]}")
    # Статистика
    current_count = collection.aggregate.over_all(total_count=True).total_count
    print(f"\nИтоговое количество объектов: {current_count}")

    client.close()

# Семантический поиск по вектрной базе
def search(name, entity):
    client = weaviate.connect_to_local(
        host="localhost",
        port=8081,
        grpc_port=50051,
    ) # Подключаюсь к ВБД Weaviate

    collection = client.collections.get(name) # Подключаюсь к конкретной коллекции
    statements_str = " ".join(entity["hasStatement"])

    # Формирую запрос из полей сущности
    query_parts = [
        entity["uri"],
    ]

    # Объединяю непустые части в одну строку
    query_text = " ".join(filter(None, query_parts))

    # Фильтр по классу
    class_filter = weaviate.classes.query.Filter.by_property("type").equal(entity["type"])

    # Гибридный поиск с фильтром
    response = collection.query.hybrid(
        query=query_text,
        alpha=0.5,
        query_properties=["label"],
        filters=class_filter,
        return_metadata=MetadataQuery(score=True),
        limit=1
    )
    client.close()
    if len(response.objects) > 0:
      if entity["uri"] == response.objects[0].properties["uri"] or response.objects[0].metadata.score >= 0.8:
        print(f"Нашёл score: {response.objects[0].metadata.score}")
        return response.objects[0]  # Возвращаем найденный объект
    return None

def query(text):
    model = 'deepseek/deepseek-chat-v3-0324:free'
    comcore_ontology = f"""
    @prefix comcore: <https://kb.moneta.ru/terms/common/coreontology> .
        @prefix dc: <http://purl.org/dc/elements/1.1/> .
        @prefix dcmtype: <http://purl.org/dc/dcmitype/> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        <https://kb.moneta.ru/terms/common/coreontology#> a owl:Ontology;
             dc:title "Самая общая онтология суперклассов для описания бизнес-процессов сервисов компании" ;
             rdfs:comment "Данная онтология описывает суперклассы и их отношения, которые используются при анализе текстовых документов/чанков. Содержит описание сервисов и их вариантов использования - основных классов и составляющих бизнес-процессов: Процессов, Акторов, входных Ресурсов и результирующих продуктов (артефактов), Событий, определяющих цепочку простых Процессов (Актов). " ;
             rdfs:isDefinedBy <https://docs.moneta.ru/common/terms/coreontology/>;
             rdfs:seeAlso <https://www.w3.org/TR/owl2-overview/>, <https://www.w3.org/TR/2004/REC-owl-guide-20040210/>;
             owl:imports <https://www.w3.org/2000/01/rdf-schema>, <https://www.w3.org/2002/07/owl>, <https://purl.org/dc/elements/1.1/>, <https://purl.org/dc/terms/>;
             owl:versionIRI <https://docs.moneta.ru/common/terms/coreontology/>;
             owl:versionInfo "$Date: 2025/25/04 10:54:12 $".

        comcore:Process a rdfs:Class;
          rdfs:label "Процесс"@ru;
          rdfs:label "Process"@en;
          rdfs:comment "Процесс, который является подпроцессом Бизнес-процессов";
          dc:description "Процесс-это продолжительное взаимодействие или работа, выполняемая или инициируемая Акторами (Агентами в роли Акторов) в зависимости от происходящих Событий (сигналов для Акторов, Процессов или других Событий) с использованием Ресурсов с целью создания других Ресурсов и формирования исходов, условий наступления Событий, которые могут стать сигналом для инициации очередного Процесса; ".

        comcore:Resource rdfs:subClassOf rdfs:Resource;
          rdfs:label "Ресурс"@ru;
          rdfs:label "Resource"@en;
          rdfs:comment "Это всё, что используется Акторами для реализации Процесса";
          dc:description "
        Ресурс - это то, что используется/тратится при реализации процесса или создается в результате процесса. Как правило, за обеспечение Процесса данным Ресурсом отвечает один или несколько Акторов.
        Пример: В Процессе подключения Клиента к платежной системе обрабатываются Заявка Клиента на подключение в которой должен обязательно быть его ИНН.
        Ресурсы: Заявка Клиента на подключение, ИНН Клиента.".

        comcore:Agent rdfs:subClassOf dcmtype:Agent;
          rdfs:label "Агент"@ru;
          rdfs:label "Agent"@en;
          rdfs:comment "Это сущность, которая активно участвует в Процессе(Бизнес-процессе) и выполняет какую-то роль, реализует определенную функцию";
          dc:description "
        Агент - это сущность, которая участвует в Процессе и выполняет какую-то роль, реализует функцию или отвечает за Событие. Агенты взаимодействуют в Процессе. Они инициализируют Подпроцессы, отдельные Акты, результаты которых используют другие Агенты.
        Например, для реализации Процесса сопровождения в качестве Агента со стороны компании
        может выступать Агент - Сотрудник службы сопровождения, а может выступать Агент - искусственный интеллект или просто какой-то микросервис.
        Агент способен получать сообщения и выполнять на их основе какие-то действия, реализовать функцию.
        Агент использует для реализации своей функции Ресурсы. Он может быть ответственным за обеспечение Процесса даннным Ресурсом.
        Пример: При подключении Клиента к платежной системе задействуются Сотрудник службы безопасности компании, Сотрудник отдела по обслуживанию, сервис мониторинга заполненности ЛК.
        Агенты: Сотрудник службы безопасности компании, Сотрудник отдела по обслуживанию, Сервис мониторинга заполненности ЛК.".

    	comcore:abbreviation a owl:DatatypeProperty;
          rdfs:label "сокращение"@ru;
          rdfs:label "abbreviation"@en;
          rdfs:domain rdfs:Resource;  # Может применяться к любым ресурсам
          rdfs:range xsd:string;      # Значение — строка
          rdfs:comment "Сокращенная форма термина".

        comcore:Event rdfs:subClassOf dcmtype:Event;
          rdfs:label "Событие"@ru;
          rdfs:label "Event"@en;
          rdfs:comment "Событие - стартовое условие запуска следующего Процесса, может быть результатом предыдущего Процесса или инициироваться Агентом (Клиентом, Оператором, ПО)";
          dc:description "
        Это описание какого-то исхода в результате реализации Процесса, или События, инициирующего Процесс.
        Пример: Проверка MRM задачи может иметь три статуса (Согласовано, Отказано, Нет решения), при отсутствии решения отправляется запрос дополнительных документов.
        События: Статус Согласовано, Статус Отказано, Статус Нет решения, Отправка запроса дополнительных документов.".

        comcore:isResultOf rdf:type owl:ObjectProperty;
          owl:inverseOf comcore:hasResult;
          rdf:type owl:IrreflexiveProperty;
          rdfs:label "результат"@ru;
          rdfs:label "result"@en;
          rdfs:domain comcore:Resource;
          rdfs:domain comcore:Event;
          rdfs:range comcore:Process;
          rdfs:comment "
        Указывает что Событие или Ресурс (субъект) является результатом Процесса (объект).
        Пример: Регистрация в форме может закончиться неуспешно если ИНН или Email уже зарегистрирован.
        Субъекты: Успешная регистрация, ИНН уже зарегистрирован, Email уже зарегистрирован.".

        comcore:canBeResourceFor rdf:type owl:ObjectProperty;
          rdfs:label "может быть Ресурсом"@ru;
          rdfs:label "может использоваться как Ресурс в"@ru;
          rdfs:label "can be resource for"@en;
          rdfs:label "can be resource in"@en;
          rdfs:domain comcore:Resource;
          rdfs:range comcore:Process;
          rdfs:comment "Указывает что Ресурс (субъект) может использоваться в качестве входного Ресурса данного Процесса (объект). Например, ответ на секретный вопрос может использоваться при аутентификации" .

        comcore:isResourceOf rdf:type owl:ObjectProperty;
          owl:inverseOf comcore:hasResource;
          rdfs:label "является Ресурсом"@ru;
          rdfs:label "is Resource of"@en;
          rdfs:domain comcore:Resource;
          rdfs:range comcore:Process;
          rdfs:comment "Указывает что Ресурс (субъект) является необходимым входным Ресурсом данного Процесса (объект). Например, логин или пароль при аутентификации" .

        comcore:isActorOf rdf:type owl:ObjectProperty;
          owl:inverseOf comcore:hasActor;
          rdfs:label "является Актором"@ru;
          rdfs:label "is Actor of"@en;
          rdfs:comment "Указывает Агента (субъект), который в какой-то роли принимает участие в Процессе (объект)";
          rdfs:domain comcore:Agent;
          rdfs:range comcore:Process.

        comcore:Initiates rdfs:subPropertyOf comcore:;
          rdfs:label "инициирует"@ru;
          rdfs:label "initiates"@en;
          rdfs:comment "Указывает что субъект инициирует данный Процесс.";
          rdfs:domain comcore:Event;
          rdfs:domain comcore:Agent;
          rdfs:range comcore:Process.

        comcore:isPartOf rdfs:subPropertyOf dcterms:isPartOf;
          owl:inverseOf comcore:hasPart;
          rdf:type owl:IrreflexiveProperty;
          rdf:type owl:TransitiveProperty;
          rdfs:label "является частью"@ru;
          rdfs:label "is part of"@en;
          rdfs:domain comcore:Process;
          rdfs:domain comcore:Resource;
          rdfs:range comcore:Process;
          rdfs:range comcore:Resource;
          rdfs:comment "Указывает, что субъект является частью для данного объекта".

        comcore:isResponsibleFor rdfs:subPropertyOf dcterms:contributor;
          rdfs:label "ответственный"@ru;
          rdfs:label "responsible"@en;
          rdfs:comment "Указывает, что Агент (субъект) отвечает за наличие/создание данного Ресурса (объект) или является ответственным за проведение Процесса";
          rdfs:domain comcore:Agent;
          rdfs:range comcore:Resource;
          rdfs:range comcore:Process.

        comcore:relation rdfs:subPropertyOf dcterms:relation;
          rdf:type owl:IrreflexiveProperty;
          rdfs:label "связан с"@ru;
          rdfs:label "relation"@en;
          rdfs:comment "Указывает, что одна сущность (субъект) как-то связана с другой сущностью (объект). Отношение используется, если не подходят вышеперечисленные отношения".
        """
    prompt = f"""
        Извлеките из ТЕКСТА все сущности классов, описанных в ОНТОЛОГИИ и ВСЕ отношения между ними;
        ТРЕБОВАНИЯ:
        Извлекаются ВСЕ ВОЗМОЖНЫЕ(всё что можешь, проанализируй каждое слово) объекты, которые подходят под описание в онтологии;
        Одно слова может входить в разные сущности, если например одна сущность Process а другая Resource
        Триплет это представления ввида: субъект - предикат - объект
        У каждого объекта должно быть хотя бы МИНИМУМ ЧЕТЫРЕ триплета:
        1. триплет, который описывает тип сущности: ":личный_кабинет rdf:type comcore:Resource ;"
        2. триплет с именем сущности: "rdfs:label " rdfs:label "личный кабинет"@ru ;"
        3. отношение между двумя сущностями: "comcore:isResourceOf :заполнение личного кабинета ."
            идентификатор_предиката берется из файла описывающего онтологию в соответствии с форматом ont_name:predicate_name;
            сущность должна быть связана с другой сущностью отношением, описанным в ОНТОЛОГИИ
        4. Для каждого термина у которого есть определение в тексте" : 
            триплет с описанием (определением) объекта: "dc:definition Личный кабинет (ЛК) - раздел в Системе МОНЕТА.РУ, который содержит данные о Получателе..."
        Так же может быть:
            5. триплет с аббревиатурой: "comcore:abbreviation "ЛК""


        ТЕКСТ: {text}
        ОНТОЛОГИЯ: {comcore_ontology}

        НЕЛЬЗЯ ДОБОВЛЯТЬ ЛИШНИЕ СИМВОЛЫ ОТ СЕБЯ
        и НЕ НАДО никаких ```
        ПРИМЕР ВЫВОДА:
        :клиент rdf:type comcore:Agent ;
          rdfs:label "Клиент" ;
          comcore:isResposibleFor :личный кабинет ;
          comcore:isActorOf :заполнение личного кабинета .

        :личный_кабинет rdf:type comcore:Resource ;
          rdfs:label "личный кабинет"@ru ;
          rdfs:label "ЛК"@ru ;
          comcore:isResourceOf :заполнение личного кабинета .

        :заполнение_личного_кабинета rdf:type comcore:Process ;
          rdfs:label "заполнение личного кабинета" ;
          comcore:isPartOf :подключение_к_Системе_МОНЕТА_РУ .
        """
    params = {
                "model": model,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }
    api_key = "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"
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        data=json.dumps(params)
    )
    print(response)
    return response.json()['choices'][0]['message']['content']

def main():
    # Создание коллекции для TTL
    # ttl_collection("TTL")
    # for i in os.listdir("../data/json_cache"):
    #    add_new_object("TTL", f"../data/json_cache/{i}"

    # print_weaviate_collection("TTL", 'output.json')
    pass

if __name__ == "__main__":
    main()


# Создание коллекции для TTL
#ttl_collection("CQ")

# Создание коллекцию для TTL
#chunk_collection("Chunk")