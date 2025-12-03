import os
import json
import re

from Framework.ChatRequest import ChatRequest

model = 'deepseek/deepseek-chat-v3-0324:free'

def get_ttl_from_text(text: str) -> str:
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
    print("Requesting")
    text = ChatRequest.chat_request(prompt, model)
    print("Request Complete")
    return text


def ttl_from_chunk(chunk_path: str, res_dir: str) -> None:
    file_name = chunk_path.split('/')[-1].split('.')[0]
    with open(chunk_path, 'r', encoding='utf-8') as chunk_file, \
         open(f'{res_dir}/{file_name}.ttl', 'w', encoding='utf-8') as ttl_file:
        data = json.load(chunk_file)
        text = get_ttl_from_text(data['content'])
        ttl_file.write(text)

def ttl_file_to_json(ttl_path: str, res_dir: str) -> None:
    file_name = ttl_path.split('/')[-1].split('.')[0]
    json_path = f"{res_dir}/{file_name}.json"
    with open(ttl_path, 'r', encoding='utf-8') as ttl_file, \
         open(json_path, 'w', encoding='utf-8') as json_file:
        content = ttl_file.read()
        data = parse_ttl_to_json(content)
        json.dump(data, json_file, ensure_ascii=False, indent=4)
