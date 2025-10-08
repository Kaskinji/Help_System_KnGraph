from Ontologies.New_Ontology import comcore_E_ontology
from Ontologies.Comcore_R_Ontology import comcore_R_ontology
from Testing_Ontology.Context import context

prompt = f'''
TECHNICAL SPECIFICATION:
Extract from the provided text ALL entities and relations that STRICTLY CORRESPOND to the ontology of entities and relations.
Output format MUST BE Turtle (ttl) without any explanations or comments.

STRICT REQUIREMENTS:
1. Extraction:
- ONLY entities and relations that STRICTLY correspond to the ontology classes and properties
- NO extraneous elements or interpretations
- If an entity does not match the ontology - DO NOT include it
- Identifiers for extracted entities are formed by the rule ":label", where label is the word form describing the entity (entity label or name); if the word form is longer than 40 characters, it is truncated at the 40th character; if the word form consists of multiple words, it is formed as one word with underscores instead of spaces (e.g., ":department_operator"); if such identifier already exists, then either it's the same entity and you only need to add new attributes or relations, or if it's another similar entity with the same initial name, form the identifier by adding an incremental number at the end (":department_operator_02")
- predicate_identifier is taken from the ontology file according to the format ont_name:predicate_name;

2. Identifier format:
- :lowercase_with_underscores
- Maximum 40 characters

3. (MANDATORY) For each entity minimum three triplets: type, label, and relation:
(entity_identifier, rdf:type, ont_name:class_name);
(entity_identifier, rdfs:label, "entity name");
(entity_identifier, predicate_identifier, entity_identifier_2);

4. PROHIBITED:
- Adding comments
- Changing output format
- Inventing properties that don't exist in the ontology

TEXT:
{context}
ONTOLOGY:
{comcore_E_ontology}
RELATIONS:
{comcore_R_ontology}

Example of CORRECT output:
    ```
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