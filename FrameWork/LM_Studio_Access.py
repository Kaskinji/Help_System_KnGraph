import requests
import json

try:
    response = requests.get("http://localhost:1234/v1/models", timeout=10)
    models = response.json()
    print("📋 Доступные модели:")
    for model in models.get('data', []):
        print(f"  - {model['id']}")

except requests.exceptions.ConnectionError:
    print("❌ Не могу подключиться к LM Studio.")