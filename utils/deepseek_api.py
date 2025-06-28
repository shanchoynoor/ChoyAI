# utils/deepseek_api.py
import requests
import os
from typing import Dict, Any

class DeepSeekAPI:
    def __init__(self, api_key: str):
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, message: str, model: str = "deepseek-chat") -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.7
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
