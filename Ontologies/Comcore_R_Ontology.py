comcore_R_ontology = '''

comcore:isStatementOf rdf:type owl:ObjectProperty;
  owl:inverseOf comcore:hasStatement;
  rdf:type owl:IrreflexiveProperty;
  rdfs:label "является утверждением"@ru;
  rdfs:label "is statement of"@en;
  rdfs:domain comcore:Statement;
  rdfs:range comcore:TextChunk;
  rdfs:comment """
  Указывает, что Утверждение (субъект) принадлежит данному Чанку (объект).
  """
  
comcore:hasSource rdf:type owl:ObjectProperty;
  owl:inverseOf comcore:isSourseOf;
  rdf:type owl:IrreflexiveProperty;
  rdfs:label "имеет источник"@ru;
  rdfs:label "has source"@en;
  rdfs:domain comcore:TextChunk;
  rdfs:range comcore:Document;
  rdfs:comment """
  """
  
comcore:isResultOf rdf:type owl:ObjectProperty;
  owl:inverseOf comcore:hasResult;
  rdf:type owl:IrreflexiveProperty;
  rdfs:label "результат"@ru;
  rdfs:label "result"@en;
  rdfs:domain comcore:Resource;
  rdfs:domain comcore:Event;
  rdfs:range comcore:Process;
  rdfs:comment """
Указывает что Событие или Ресурс (субъект) является результатом Процесса (объект).
Пример: Регистрация в форме может закончиться неуспешно если ИНН или Email уже зарегистрирован.
Субъекты: Успешная регистрация, ИНН уже зарегистрирован, Email уже зарегистрирован.""".

comcore:canBeResourceFor a owl:ObjectProperty;
  rdfs:label "может быть Ресурсом для"@ru;
  rdfs:label "can be resource for"@en;
  rdfs:domain comcore:Resource;
  rdfs:range comcore:Process;
  rdfs:comment """Указывает что Ресурс (субъект) может использоваться в качестве входного Ресурса данного Процесса (объект). Например, ответ на секретный вопрос может использоваться при аутентификации""" .

comcore:isResourceOf rdf:type owl:ObjectProperty;
  owl:inverseOf comcore:hasResource;
  rdfs:label "является Ресурсом"@ru;
  rdfs:label "is Resource of"@en;
  rdfs:domain comcore:Resource;
  rdfs:range comcore:Process;
  rdfs:comment """Указывает что Ресурс (субъект) является необходимым входным Ресурсом данного Процесса (объект). Например, логин или пароль при аутентификации""" .

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
  
comcore:extractedFrom a owl:ObjectProperty;
  rdfs:label "извлечен из"@ru;
  rdfs:label "extracted from"@en;
  rdfs:domain comcore:Triple;
  rdfs:range comcore:TextChunk;
  rdfs:comment "Связывает триплет с фрагментом текста, из которого он был извлечен".

comcore:hasCondition a owl:ObjectProperty;
   rdfs:label "имеет условие"@ru;
   rdfs:label "has condition"@en;
   rdfs:domain comcore:Answer;
   rdfs:domain comcore:Event;
   rdfs:range comcore:Condition;
   rdfs:comment "Условие или причина ответа.
'''