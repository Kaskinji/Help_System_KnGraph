extra = '''

comcore:Template rdfs:subClassOf comcore:Resource;
   rdfs:label "Шаблон"@ru;
   rdfs:label "Template"@en;
   rdfs:comment "Данные которые используются как пример"

## Answer ( отрицательный - причина, положительный - ок ) 
## отказ - условие
## шаблон ответа

comcore:Statement rdfs:subClassOf rdf:Statement;
    rdfs:label "Триплет"@ru;
    rdfs:label "Triple"@en;
    rdfs:comment "Триплет (субъект-предикат-объект), извлеченный из текста, с метаданными о происхождении".

comcore:TextChunk a rdfs:Class;
   rdfs:label "Текстовый фрагмент"@ru;
   rdfs:label "Text Chunk"@en;
   rdfs:comment "Фрагмент исходного текста, из которого были извлечены знания".

comcore:Document a rdfs:Class;
   rdfs:label "Документ"@ru;
   rdfs:label "Document"@en;
   rdfs:comment "Документ с информацией".

##отношения для Statement
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

comcore:Client rdfs:subClassOf comcore:Agent;
  rdfs:label "Клиент"@ru;
  rdfs:label "Client"@en;
  rdfs:comment "Агент, выступающий в роли клиента или заказчика услуг".

comcore:Employee rdfs:subClassOf comcore:Agent;
  rdfs:label "Сотрудник"@ru;
  rdfs:label "Employee"@en;
  rdfs:comment "Агент, являющийся сотрудником организации".

comcore:System rdfs:subClassOf comcore:Agent;
  rdfs:label "Система"@ru;
  rdfs:label "System"@en;
  rdfs:comment "Программная система или сервис, выступающий в роли Агента".

'''