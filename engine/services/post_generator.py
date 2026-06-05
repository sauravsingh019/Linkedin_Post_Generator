from typing import Any, Dict

from config.settings import DEFAULT_POST_DAYS
from engine.graph.workflow import build_workflow
from engine.prompts.creator_prompt import (
    build_refine_post_prompt,
    build_single_post_prompt,
)
from engine.services.rag_service import RAGService


def _normalize_plan(raw_plan: Any, requested_count: int) -> dict[str, Any]:
    posts = raw_plan.get("posts", []) if isinstance(raw_plan, dict) else []
    normalized_posts = []

    for index, post in enumerate(posts[:requested_count]):
        # Fallback fields if model misses some keys
        normalized_posts.append(
            {
                "day": post.get("day") or DEFAULT_POST_DAYS[index],
                "angle": post.get("angle", "Authority builder"),
                "hook": post.get("hook", "").strip(),
                "post": post.get("post", "").strip(),
                "hashtags": post.get("hashtags", []),
                "cta": post.get("cta", "").strip(),
            }
        )

    return {
        "summary": raw_plan.get("summary", "") if isinstance(raw_plan, dict) else "",
        "posts": normalized_posts,
    }


def _count_words(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def _word_range(target: int) -> tuple[int, int]:
    tolerance = max(20, int(target * 0.15))
    return max(40, target - tolerance), target + tolerance


def _post_within_range(post: dict[str, Any], target: int) -> bool:
    minimum, maximum = _word_range(target)
    body_copy = post.get("post", "")
    return minimum <= _count_words(body_copy) <= maximum


def generate_weekly_plan(client: Any, model: str, profile: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    """Generates a weekly content plan by orchestrating the multi-agent LangGraph workflow."""
    # Deduce API Key and Provider from the active client
    api_key = getattr(client, "api_key", "")
    provider = "gemini" if hasattr(client, "api_key") else "ollama"

    # 1. Run RAG retrieval to fetch high-performing style reference posts
    rag = RAGService(provider=provider, model=model, api_key=api_key)
    reference_posts = rag.retrieve_similar_posts(query=profile.get("expertise", ""), limit=5)

    # 2. Setup initial state for the multi-agent system
    initial_state = {
        "user_profile": profile,
        "settings": settings,
        "reference_posts": reference_posts,
        "auditor_insights": "",
        "analyst_patterns": "",
        "weekly_plan": {},
        "error": "",
        "client": client,
        "model": model,
    }

    # 3. Compile and invoke the workflow (will run fallback graph if langgraph package is missing)
    workflow = build_workflow()
    final_state = workflow.invoke(initial_state)

    # 4. Extract and normalize weekly posts
    raw_plan = final_state.get("weekly_plan", {})
    return _normalize_plan(raw_plan, settings["posts_per_week"])


def regenerate_single_post(client: Any, model: str, profile: dict[str, Any], settings: dict[str, Any], post: dict[str, Any]) -> dict[str, Any]:
    """Regenerates a single day's post using style inspiration and niche context."""
    api_key = getattr(client, "api_key", "")
    provider = "gemini" if hasattr(client, "api_key") else "ollama"

    # Fetch references using RAG
    rag = RAGService(provider=provider, model=model, api_key=api_key)
    reference_posts = rag.retrieve_similar_posts(query=profile.get("expertise", ""), limit=5)

    schema = {
        "day": post.get("day", "Monday"),
        "angle": post.get("angle", "Authority builder"),
        "hook": "Opening hook",
        "post": "Body text",
        "hashtags": ["#Topic"],
        "cta": "Call to action",
    }

    feedback = None
    best_post = post

    # Try up to 2 times to generate a post within requested word count limits
    for _ in range(2):
        prompt = build_single_post_prompt(
            profile=profile,
            settings=settings,
            reference_posts=reference_posts,
            day=post.get("day", "Monday"),
            angle=post.get("angle", "Authority builder"),
            feedback=feedback,
        )

        if hasattr(client, "list_models"):  # OllamaClient
            candidate = client.generate_json(prompt=prompt, schema=schema, model=model)
        else:  # GeminiClient
            candidate = client.generate_json(prompt=prompt, schema=schema)

        normalized_post = {
            "day": candidate.get("day") or post.get("day", "Monday"),
            "angle": candidate.get("angle") or post.get("angle", "Authority builder"),
            "hook": candidate.get("hook", "").strip(),
            "post": candidate.get("post", "").strip(),
            "hashtags": candidate.get("hashtags", []),
            "cta": candidate.get("cta", "").strip(),
        }
        best_post = normalized_post

        if _post_within_range(normalized_post, settings["post_length"]):
            return normalized_post

        minimum, maximum = _word_range(settings["post_length"])
        feedback = (
            f"Please adjust length. The post body copy must be strictly between {minimum} "
            f"and {maximum} words. Rewrite accordingly."
        )

    return best_post


def refine_post_with_ai(client: Any, model: str, profile: dict[str, Any], settings: dict[str, Any], post: dict[str, Any], instruction: str) -> dict[str, Any]:
    """Applies specific user edit instructions to a post card using AI refinement."""
    prompt = build_refine_post_prompt(profile, settings, post, instruction)
    schema = {
        "day": post.get("day", "Monday"),
        "angle": post.get("angle", "Authority builder"),
        "hook": "Opening hook",
        "post": "Refined body copy",
        "hashtags": ["#Topic"],
        "cta": "Refined call to action",
    }

    try:
        if hasattr(client, "list_models"):  # OllamaClient
            candidate = client.generate_json(prompt=prompt, schema=schema, model=model)
        else:  # GeminiClient
            candidate = client.generate_json(prompt=prompt, schema=schema)

        return {
            "day": candidate.get("day") or post.get("day", "Monday"),
            "angle": candidate.get("angle") or post.get("angle", "Authority builder"),
            "hook": candidate.get("hook", "").strip(),
            "post": candidate.get("post", "").strip(),
            "hashtags": candidate.get("hashtags", []),
            "cta": candidate.get("cta", "").strip(),
        }
    except Exception:
        # Fallback to the original post if refinement fails
        return post
