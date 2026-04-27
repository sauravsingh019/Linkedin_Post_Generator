import json
from typing import Any

import requests

from config.settings import DEFAULT_MODEL, OLLAMA_BASE_URL, REQUEST_TIMEOUT_SECONDS


class OllamaConnectionError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout: int = REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_models(self) -> list[dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            payload = response.json()
            return payload.get("models", [])
        except requests.RequestException:
            return []

    def generate(self, prompt: str, model: str = DEFAULT_MODEL) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.RequestException as exc:
            raise OllamaConnectionError(
                "Could not reach Ollama. Start Ollama, make sure the model is pulled, and try again."
            ) from exc

    def generate_json(self, prompt: str, schema: dict[str, Any], model: str = DEFAULT_MODEL) -> dict[str, Any]:
        full_prompt = (
            f"{prompt}\n\n"
            "Return valid JSON only. Match this shape exactly:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        raw = self.generate(prompt=full_prompt, model=model)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("The model did not return valid JSON.")
            return json.loads(raw[start : end + 1])
