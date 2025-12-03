from dataclasses import dataclass
from typing import List
import re


@dataclass
class Question:
    id: str
    content: str
    description: str

def parse_question(text: str) -> List[Question]:
    questions = []
    pattern = r'cqcore:(\S+)\s+rdf:type\s+cqcore:cquest\s*;\s*cqcore:content\s+"([^"]+)"\s*;\s*dcterms:description\s+"""([^"]+)"""'
    for match in re.finditer(pattern, text, re.DOTALL):
        questions.append(Question(
            id=match[1],
            content=match[2].strip(),
            description = match[3].strip()
        ))
    return questions

def save_json(question: List[Question], path: str):
    import json
    data = [{
        'id': q.id,
        'content': q.content,
        'description': q.description
    } for q in question]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

with open("GT1.ttl", 'r', encoding='utf-8') as f:
    chunks = parse_question(f.read())
    save_json(chunks, 'question.json')
    for c in chunks:
        print(f"{c.id}")