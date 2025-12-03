from dataclasses import dataclass
from typing import List
import re


@dataclass
class Chunk:
    id: str
    title: str
    source: str
    serial: int
    size: int
    abstract: str
    content: str

def parse_chunks(text: str) -> List[Chunk]:
    chunks = []
    pattern = r'chunks:(\S+).*?title "([^"]+)".*?source (\S+).*?serial_num (\d+).*?extent (\d+).*?abstract "([^"]+)".*?content """([^"]+)"""'
    for match in re.finditer(pattern, text, re.DOTALL):
        chunks.append(Chunk(
            id=match[1],
            title=match[2],
            source=match[3],
            serial=int(match[4]),
            size=int(match[5]),
            abstract=match[6],
            content=match[7].strip()
        ))

    return chunks

def save_json(chunks: List[Chunk], path: str):
    import json
    data = [{
        'id': c.id,
        'title': c.title,
        'source': c.source,
        'serial': c.serial,
        'size': c.size,
        'abstract': c.abstract,
        'content': c.content
    } for c in chunks]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

with open("GT1.ttl", 'r', encoding='utf-8') as f:
    chunks = parse_chunks(f.read())
    save_json(chunks, 'chunks.json')
    for c in chunks:
        print(f"{c.id}: {c.title}")