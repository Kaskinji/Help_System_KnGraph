import requests

OPENROUTER_API_KEY = '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'  # Replace with your actual API key

response = requests.get(
    "https://openrouter.ai/api/v1/auth/key",
    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
)

# To print the response
print(response.json())