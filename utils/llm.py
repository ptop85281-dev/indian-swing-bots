import os
import requests

def ask_llm(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY")
    
    if not api_key:
        return "API Key not found in secrets"

    if api_key.startswith("gsk_"):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
        "model": "llama3-8b-8192",     
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1024
        }
    else:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "grok-3",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=45)
        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"
