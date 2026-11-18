import os
import requests

def ask_llm(prompt: str) -> str:
    """
    Groq અથવા xAI પરથી જવાબ મેળવે છે
    """
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY")
    
    if not api_key:
        return "API Key not found in secrets"

    # Groq API (gsk_ key માટે)
    if api_key.startswith("gsk_"):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
    else:
        # xAI API
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
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"
