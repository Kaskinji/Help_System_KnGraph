R_Ontology = '''
comcore:hasSubProcess a owl:ObjectProperty;
  owl:inverseOf comcore:isSubProcessOf;
  rdf:type owl:IrreflexiveProperty;
  rdfs:label "имеет подпроцесс"@ru;
  rdfs:domain comcore:Process;
  rdfs:range comcore:Process;
  rdfs:comment "Связывает процесс с его подпроцессами".

comcore:isSubProcessOf a owl:ObjectProperty;
  rdfs:label "является подпроцессом"@ru;
  rdfs:comment "Указывает, что процесс является подпроцессом другого процесса".

comcore:hasSource a owl:ObjectProperty;
  owl:inverseOf comcore:isSourceOf;
  rdf:type owl:IrreflexiveProperty;
  rdfs:label "имеет источник"@ru;
  rdfs:label "has source"@en;
  rdfs:domain comcore:TextChunk;
  rdfs:range comcore:Document.

comcore:isSourceOf a owl:ObjectProperty;
  rdfs:label "является источником"@ru;
  rdfs:label "is source of"@en;
  rdfs:domain comcore:Document;
  rdfs:range comcore:TextChunk.

comcore:isResultOf a owl:ObjectProperty;
  owl:inverseOf comcore:hasResult;
  rdf:type owl:IrreflexiveProperty;
  rdfs:label "является результатом"@ru;
  rdfs:label "is result of"@en;
  rdfs:domain [ owl:unionOf (comcore:Resource comcore:Event) ];  # Process не может быть результатом!
  rdfs:range comcore:Process;
  rdfs:comment "Указывает, что Ресурс или Событие является результатом Процесса".

comcore:hasResult a owl:ObjectProperty;
  rdfs:label "имеет результат"@ru;
  rdfs:label "has result"@en;
  rdfs:domain comcore:Process;
  rdfs:range [ owl:unionOf (comcore:Resource comcore:Event) ].

comcore:isResourceOf a owl:ObjectProperty;
  owl:inverseOf comcore:hasResource;
  rdfs:label "является ресурсом"@ru;
  rdfs:label "is resource of"@en;
  rdfs:domain comcore:Resource;
  rdfs:range comcore:Process;
  rdfs:comment "Указывает, что Ресурс является входным ресурсом Процесса".

comcore:hasResource a owl:ObjectProperty;
  rdfs:label "имеет ресурс"@ru;
  rdfs:label "has resource"@en;
  rdfs:domain comcore:Process;
  rdfs:range comcore:Resource.

comcore:isActorOf a owl:ObjectProperty;
  owl:inverseOf comcore:hasActor;
  rdfs:label "является актором"@ru;
  rdfs:label "is actor of"@en;
  rdfs:comment "Указывает Агента, который участвует в Процессе";
  rdfs:domain comcore:Agent;
  rdfs:range comcore:Process.

comcore:hasActor a owl:ObjectProperty;
  rdfs:label "имеет актора"@ru;
  rdfs:label "has actor"@en;
  rdfs:domain comcore:Process;
  rdfs:range comcore:Agent.

comcore:initiates a owl:ObjectProperty;
  rdfs:label "инициирует"@ru;
  rdfs:label "initiates"@en;
  rdfs:comment "Указывает, что субъект инициирует Процесс";
  rdfs:domain [ owl:unionOf (comcore:Agent comcore:Event) ];
  rdfs:range comcore:Process.

comcore:isPartOf a owl:ObjectProperty;
  rdfs:subPropertyOf dcterms:isPartOf;
  owl:inverseOf comcore:hasPart;
  rdf:type owl:IrreflexiveProperty;
  rdf:type owl:TransitiveProperty;
  rdfs:label "является частью"@ru;
  rdfs:label "is part of"@en;
  rdfs:domain [ owl:unionOf (comcore:Process comcore:Resource) ];
  rdfs:range [ owl:unionOf (comcore:Process comcore:Resource) ];
  rdfs:comment "Указывает, что субъект является частью объекта".

comcore:hasPart a owl:ObjectProperty;
  rdfs:label "имеет часть"@ru;
  rdfs:label "has part"@en;
  rdfs:domain [ owl:unionOf (comcore:Process comcore:Resource) ];
  rdfs:range [ owl:unionOf (comcore:Process comcore:Resource) ].

comcore:isResponsibleFor a owl:ObjectProperty;
  rdfs:subPropertyOf dcterms:contributor;
  rdfs:label "ответственный за"@ru;
  rdfs:label "responsible for"@en;
  rdfs:comment "Указывает, что Агент отвечает за Ресурс или Процесс";
  rdfs:domain comcore:Agent;
  rdfs:range [ owl:unionOf (comcore:Resource comcore:Process) ].

comcore:hasStatus a owl:ObjectProperty;
  rdfs:label "имеет статус"@ru;
  rdfs:label "has status"@en;
  rdfs:comment "Указывает текущий статус процесса или ресурса";
  rdfs:domain [ owl:unionOf (comcore:Process comcore:Resource) ];
  rdfs:range comcore:Status.
'''
extra_relations = '''
comcore:isStatementOf a owl:ObjectProperty;
  owl:inverseOf comcore:hasStatement;
  rdf:type owl:IrreflexiveProperty;
  rdfs:label "является утверждением"@ru;
  rdfs:label "is statement of"@en;
  rdfs:domain comcore:Statement;
  rdfs:range comcore:TextChunk;
  rdfs:comment "Указывает, что Утверждение принадлежит данному Чанку".

comcore:hasStatement a owl:ObjectProperty;
  rdfs:label "имеет утверждение"@ru;
  rdfs:label "has statement"@en;
  rdfs:domain comcore:TextChunk;
  rdfs:range comcore:Statement.
'''