import requests, json
import time, random
from Framework.ChatRequest import Keys


def get_info(response):
    provider_name = response["provider"]
    model = response["model"]

    url = f"https://openrouter.ai/api/v1/models/{model}/endpoints"
    provider_response = requests.get(url).json()
    provider = list(filter(lambda x: x["provider_name"] == provider_name, provider_response["data"]["endpoints"]))[0]

    provider_info = {"name": provider_name,
                     "full_name": provider["name"],
                     "context_length": provider["context_length"],
                     }

    info = {
        "provider": provider_info,
        "model": model,
        "finish_reason": response["choices"][0]["finish_reason"],
        "native_finish_reason": response["choices"][0]["native_finish_reason"],
        "prompt_tokens": response["usage"]["prompt_tokens"],
        "completion_tokens": response["usage"]["completion_tokens"],
        "total_tokens": response["usage"]["total_tokens"],
    }

    print("---------------------------------------------------------------------------------------------------")
    print(provider_info["full_name"])
    print(f"prompt_tokens: {info['prompt_tokens']}\tcompletion_tokens: {info['completion_tokens']}\ttotal_tokens: {info['total_tokens']}")
    print(f"provider_tokens: {provider_info['context_length']}")
    print(f"finish_reason: {info['finish_reason']}\tnative_finish_reason: {info['native_finish_reason']}")
    print("---------------------------------------------------------------------------------------------------")

def chat_request(prompt, model, temperature=1, debug=True, json_format = ""):
    params = {
                "model": model,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }
    if json_format:
      params["response_format"] =  json_format

    for _ in range(Keys.key_count()):
        api_key = Keys.get_key()
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps(params)
        )
        time.sleep(random.uniform(0, 1))
        if response.status_code == 429 or response.status_code == 401:
            Keys.next_key()
        elif response.status_code == 200:
            print(response.text)
            try:
                if debug:
                    get_info(response.json())
                return response.json()['choices'][0]['message']['content']
            except:
                return "Bruh"
        else:
            print(f'Failed to retrieve response. Status code: {response.status_code}')
            return "Bruh"
    return "Error: you're a beggar"

