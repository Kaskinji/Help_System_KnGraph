from Ontology.Entities_Ontology import E_Ontology
from Ontology.Connection_Ontology import C_Ontology
import requests
import json

api_key = "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"

def chat_request(text):
    model = "openai/gpt-5-image-mini"
    prompt = f'''
    ТЕХНИЧЕСКОЕ ЗАДАНИЕ:
    Извлеки из предоставленного текста ВСЕ сущности и отношения, СТРОГО СООТВЕТСТВУЮЩИЕ ОНТОЛОГИИ СУЩНОСТЕЙ И ОТНОШЕНИЙ.
    Формат вывода ТОЛЬКО Turtle (ttl) без каких-либо пояснений или комментариев. \n
    ТЕКСТ: \n
    "{text}"

    ПОЛНАЯ ОНТОЛОГИЯ:
    E_Ontology (Классы):\n
    {E_Ontology}

    C_Ontology (Свойства):\n
    {C_Ontology}

    ПРАВИЛА СОЗДАНИЯ СУЩНОСТЕЙ:

    1. ТОЛЬКО ЯВНЫЕ СУЩНОСТИ ИЗ ТЕКСТА:
       - Не добавляй выдуманных сущностей
       - Используй только то, что прямо упомянуто

    2. Идентификатор сущности:
       - Ключевые слова из текста
       - До 40 символов, пробелы → "_"

    3. Метка (rdfs:label):
       - Полное название на русском с "@ru"

    4. Сокращения:
       - Аббревиатуры (MCC) → отдельные сущности

    5. Анализ сложных фраз:
       - Разбивай на компоненты
       - Связывай через подходящие свойства из онтологии
       
    Пример КОРРЕКТНОГО вывода:
    :тариф rdf:type comcore:Resource ;
    rdfs:label "Тариф"@ru ;
    comcore:isResourceOf :упрощенная_идентификация ;
    comcore:canBeResourceFor :начисление_вознаграждения ;

    :торговая_площадка rdf:type comcore:Agent ;
    rdfs:label "Торговая площадка"@ru ;
    comcore:isActorOf :обеспечение_взаимодействия ;
    comcore:isResponsibleFor :программно-аппаратный_комплекс ;

    :упрощенная_идентификация rdf:type comcore:Process ;
    rdfs:label "Упрощенная идентификация"@ru ;
    comcore:hasResult :статус_неидентифицированного_клиента ;
    comcore:isPartOf :процедура_проверки_клиента ;
    dc:description """
    '''
    params = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }

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