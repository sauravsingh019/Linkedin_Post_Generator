import json
import os
import subprocess
import time
from typing import Any, Generator

import requests

from config.settings import DEFAULT_MODEL, OLLAMA_BASE_URL, REQUEST_TIMEOUT_SECONDS


class OllamaConnectionError(RuntimeError):
    pass


def ensure_ollama_running(base_url: str = OLLAMA_BASE_URL) -> bool:
    """Verifies if Ollama is running, attempts to start it if not, and waits for it to become ready."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            return True
    except requests.RequestException:
        pass

    # Attempt to start Ollama server in background
    try:
        # On Windows, try launching using standard 'ollama serve'
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )
    except Exception:
        # Fallback to local user app installation on Windows
        if os.name == "nt":
            user_dir = os.path.expanduser("~")
            ollama_app = os.path.join(user_dir, "AppData", "Local", "Programs", "Ollama", "ollama app.exe")
            if os.path.exists(ollama_app):
                try:
                    subprocess.Popen(
                        [ollama_app],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception:
                    pass

    # Wait up to 10 seconds for the service to start responding
    for _ in range(10):
        time.sleep(1.0)
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass

    return False


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout: int = REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_healthy(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> list[dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            payload = response.json()
            return payload.get("models", [])
        except requests.RequestException:
            return []

    def pull_model_stream(self, model: str) -> Generator[dict[str, Any], None, None]:
        """Trigger model download and yield progress status and percentages."""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": True},
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    status = chunk.get("status", "")
                    completed = chunk.get("completed", 0)
                    total = chunk.get("total", 0)
                    progress = int((completed / total) * 100) if total > 0 else 0
                    yield {"status": status, "progress": progress}
        except requests.RequestException as exc:
            raise OllamaConnectionError(f"Failed to pull model '{model}' from Ollama registry.") from exc

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
