import json
from pathlib import Path
from typing import Any

from config.settings import DEFAULT_POST_DAYS
from engine.prompts.creator_prompt import build_single_post_prompt, build_weekly_plan_prompt


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "posts.json"


def _load_reference_posts(limit: int = 5) -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open(encoding="utf-8") as file:
        posts = json.load(file)

    ranked = sorted(posts, key=lambda post: post.get("likes", 0), reverse=True)
    return ranked[:limit]


def _normalize_plan(raw_plan: Any, requested_count: int) -> dict[str, Any]:
    posts = raw_plan.get("posts", []) if isinstance(raw_plan, dict) else []
    normalized_posts = []

    for index, post in enumerate(posts[:requested_count]):
        normalized_posts.append(
            {
                "day": post.get("day") or DEFAULT_POST_DAYS[index],
                "angle": post.get("angle", "Authority builder"),
                "hook": post.get("hook", ""),
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


def _posts_within_range(posts: list[dict[str, Any]], target: int) -> bool:
    minimum, maximum = _word_range(target)
    return bool(posts) and all(minimum <= _count_words(post.get("post", "")) <= maximum for post in posts)


def _post_within_range(post: dict[str, Any], target: int) -> bool:
    minimum, maximum = _word_range(target)
    return minimum <= _count_words(post.get("post", "")) <= maximum


def generate_weekly_plan(client, model: str, profile: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    reference_posts = _load_reference_posts()
    schema = {
        "summary": "One short paragraph about the weekly strategy",
        "posts": [
            {
                "day": "Monday",
                "angle": "Story / lesson / framework / opinion / hiring / case study",
                "hook": "Opening line",
                "post": "Full LinkedIn post",
                "hashtags": ["#Example"],
                "cta": "Closing CTA",
            }
        ],
    }

    feedback = None
    best_plan = {"summary": "", "posts": []}

    for _ in range(2):
        prompt = build_weekly_plan_prompt(profile, settings, reference_posts, feedback=feedback)
        raw_plan = client.generate_json(prompt=prompt, model=model, schema=schema)
        normalized_plan = _normalize_plan(raw_plan, settings["posts_per_week"])
        best_plan = normalized_plan

        if _posts_within_range(normalized_plan["posts"], settings["post_length"]):
            return normalized_plan

        minimum, maximum = _word_range(settings["post_length"])
        feedback = (
            f"Regenerate the full plan. Every post body must stay between {minimum} and {maximum} words. "
            "Do not exceed the limit. Keep the same JSON shape."
        )

    return best_plan


def regenerate_single_post(client, model: str, profile: dict[str, Any], settings: dict[str, Any], post: dict[str, Any]) -> dict[str, Any]:
    reference_posts = _load_reference_posts()
    schema = {
        "day": post.get("day", "Monday"),
        "angle": post.get("angle", "Authority builder"),
        "hook": "Opening line",
        "post": "Full LinkedIn post",
        "hashtags": ["#Example"],
        "cta": "Closing CTA",
    }

    feedback = None
    best_post = post

    for _ in range(2):
        prompt = build_single_post_prompt(
            profile,
            settings,
            reference_posts,
            day=post.get("day", "Monday"),
            angle=post.get("angle", "Authority builder"),
            feedback=feedback,
        )
        candidate = client.generate_json(prompt=prompt, model=model, schema=schema)
        normalized_post = {
            "day": candidate.get("day") or post.get("day", "Monday"),
            "angle": candidate.get("angle") or post.get("angle", "Authority builder"),
            "hook": candidate.get("hook", ""),
            "post": candidate.get("post", "").strip(),
            "hashtags": candidate.get("hashtags", []),
            "cta": candidate.get("cta", "").strip(),
        }
        best_post = normalized_post

        if _post_within_range(normalized_post, settings["post_length"]):
            return normalized_post

        minimum, maximum = _word_range(settings["post_length"])
        feedback = (
            f"Regenerate this post. The post body must stay between {minimum} and {maximum} words. "
            "Do not exceed the limit. Keep the same JSON shape."
        )

    return best_post
