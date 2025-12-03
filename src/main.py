from RequestTTL import chat_request
import json

with open("Parsing/chunks.json", 'r', encoding='utf-8') as f:
    chunks = json.load(f)

for ch in chunks:
    print(f"Requesting Chunk {ch['id']}")
    ttl_text = chat_request(ch["content"])
    with open("TTL/" + ch["id"] + ".ttl", 'w', encoding='utf-8') as f:
        f.write(ttl_text)