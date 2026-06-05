import json
from typing import Any

import requests


class GeminiClient:
    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(self, prompt: str) -> str:
        if not self.is_configured():
            raise ValueError("Gemini API key is not configured. Please add it in Settings.")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""
        except requests.RequestException as exc:
            raise RuntimeError(f"Gemini API request failed: {exc}") from exc

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured():
            raise ValueError("Gemini API key is not configured. Please add it in Settings.")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        full_prompt = (
            f"{prompt}\n\n"
            "Return valid JSON only. Match this shape exactly:\n"
            f"{json.dumps(schema, indent=2)}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": full_prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    raw = parts[0].get("text", "").strip()
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        start = raw.find("{")
                        end = raw.rfind("}")
                        if start == -1 or end == -1:
                            raise ValueError("The model did not return valid JSON.")
                        return json.loads(raw[start : end + 1])
            raise ValueError("Empty response returned from Gemini API.")
        except requests.RequestException as exc:
            raise RuntimeError(f"Gemini API request failed: {exc}") from exc
