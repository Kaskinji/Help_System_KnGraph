import json
import requests
from prompts.Prompt_1 import prompt

def llm_request(prompt: str, api_key: str) -> str:
  try:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "tngtech/deepseek-r1t2-chimera:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        })
    )

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Ошибка {response.status_code}: {response.text}"

  except Exception as e:
    return f"Ошибка при запросе: {str(e)}"


def extract_entities_from_chunk(prompt):
    return llm_request(prompt, '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')

if __name__ == "__main__":
    print("Запуск извлечения сущностей...")
    result = extract_entities_from_chunk(prompt)
    print(result)
