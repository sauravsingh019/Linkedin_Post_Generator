import json
import math
from pathlib import Path
from typing import Any, Dict, List

import requests

from config.settings import OLLAMA_BASE_URL

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
POSTS_PATH = DATA_DIR / "posts.json"
CACHE_PATH = DATA_DIR / "embeddings_cache.json"


def dot_product(v1: List[float], v2: List[float]) -> float:
    return sum(x * y for x, y in zip(v1, v2))


def magnitude(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    mag1 = magnitude(v1)
    mag2 = magnitude(v2)
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product(v1, v2) / (mag1 * mag2)


class RAGService:
    def __init__(self, provider: str = "ollama", model: str = "mistral", api_key: str = "", base_url: str = OLLAMA_BASE_URL):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def get_embedding(self, text: str) -> List[float]:
        """Fetch embedding vector for a given text string from active provider."""
        if not text.strip():
            return []

        if self.provider == "gemini":
            if not self.api_key.strip():
                return []
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"
            payload = {
                "model": "models/text-embedding-004",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            try:
                response = requests.post(url, json=payload, timeout=20)
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", {}).get("values", [])
            except Exception:
                return []
        else:
            url = f"{self.base_url}/api/embeddings"
            payload = {
                "model": self.model,
                "prompt": text
            }
            try:
                response = requests.post(url, json=payload, timeout=20)
                response.raise_for_status()
                return response.json().get("embedding", [])
            except Exception:
                return []

    def load_posts(self) -> List[Dict[str, Any]]:
        if not POSTS_PATH.exists():
            return []
        with POSTS_PATH.open(encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []

    def get_cached_embeddings(self) -> Dict[str, Any]:
        if not CACHE_PATH.exists():
            return {}
        with CACHE_PATH.open(encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}

    def save_cached_embeddings(self, cache_data: Dict[str, Any]):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with CACHE_PATH.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

    def synchronize_cache(self, force: bool = False) -> List[Dict[str, Any]]:
        """Ensures local JSON embeddings cache matches the current posts database and provider configuration."""
        posts = self.load_posts()
        if not posts:
            return []

        cache = self.get_cached_embeddings()
        cache_provider = cache.get("provider")
        cache_model = cache.get("model")
        cached_items = cache.get("embeddings", [])

        # Check if cache is structurally out-of-date
        cached_texts = {item["text"] for item in cached_items}
        posts_texts = {p["text"] for p in posts}

        if (
            force
            or cache_provider != self.provider
            or cache_model != self.model
            or cached_texts != posts_texts
        ):
            # Rebuild cache in parallel
            from concurrent.futures import ThreadPoolExecutor

            new_embeddings = []

            def embed_item(post: Dict[str, Any]) -> Dict[str, Any] | None:
                txt = post["text"]
                vector = self.get_embedding(txt)
                if vector:
                    return {
                        "text": txt,
                        "likes": post.get("likes", 0),
                        "vector": vector
                    }
                return None

            with ThreadPoolExecutor(max_workers=6) as executor:
                results = executor.map(embed_item, posts)
                for res in results:
                    if res:
                        new_embeddings.append(res)

            # If we couldn't create any vectors (e.g. offline/no key), don't wipe the old cache if it existed
            if not new_embeddings and cached_items:
                return cached_items

            cache = {
                "provider": self.provider,
                "model": self.model,
                "embeddings": new_embeddings
            }
            self.save_cached_embeddings(cache)
            return new_embeddings

        return cached_items

    def retrieve_similar_posts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve highest scoring matching posts from vector cache."""
        cached_items = self.synchronize_cache()
        if not cached_items:
            # Fallback to general high-likes posts
            posts = self.load_posts()
            return sorted(posts, key=lambda p: p.get("likes", 0), reverse=True)[:limit]

        query_vector = self.get_embedding(query)
        if not query_vector:
            # Fallback to highest likes if embedding generation fails
            return sorted(cached_items, key=lambda p: p.get("likes", 0), reverse=True)[:limit]

        scored_posts = []
        for item in cached_items:
            sim = cosine_similarity(query_vector, item["vector"])
            scored_posts.append({
                "text": item["text"],
                "likes": item.get("likes", 0),
                "score": sim
            })

        scored_posts.sort(key=lambda p: p["score"], reverse=True)
        return scored_posts[:limit]
