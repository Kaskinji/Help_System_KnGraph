import requests
from Prompts.Prompt import prompt

response = requests.get("http://localhost:3301/v1/models", timeout=5)
print(f"✅ LM Studio доступен на порту 3301: {response.status_code}")

url = "http://localhost:3301/v1/chat/completions"
data = {
    "model": "mistralai/mistral-7b-instruct-v0.3",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.1
}

response = requests.post(url, json=data)
print(f"📨 Статус ответа: {response.text}")

result = response.json()["choices"][0]["message"]["content"]
print(result)
