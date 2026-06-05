import json
from config.settings import DEFAULT_POST_DAYS


def build_auditor_prompt(profile: dict) -> str:
    return f"""
You are a master LinkedIn Brand Strategist.
Your job is to audit the user's profile and outline a clear content strategy.

User Profile:
- Expertise: {profile.get("expertise", "N/A")}
- Target Audience: {profile.get("audience", "N/A")}
- Tone: {profile.get("tone", "N/A")}
- Primary Goal: {profile.get("goal", "N/A")}
- Weekly Themes: {", ".join(profile.get("themes", [])) if profile.get("themes") else "General industry value"}

Provide a concise audit containing:
1. **Core Brand Identity**: Define the positioning.
2. **Key Messaging Pillars**: 2-3 content focus areas matching their themes.
3. **Strategic Angles**: Best formats to convert the target audience.

Keep your response brief, clear, and structured as bullet points. Do not write introductory filler.
"""


def build_analyst_prompt(reference_posts: list[dict]) -> str:
    reference_lines = "\n".join(
        f"- {post['text']} (likes: {post.get('likes', 'n/a')})" for post in reference_posts
    ) if reference_posts else "No reference posts available"

    return f"""
You are an expert Social Media Copywriter and Engagement Analyst.
Analyze these high-performing LinkedIn post templates to extract their secret formulas.

Example posts:
{reference_lines}

Identify:
1. **Hook Patterns**: How do they capture attention in the first 2 lines?
2. **Formatting & Structure**: How is the body spaced and organized?
3. **CTA Styles**: How do they drive engagement at the end?

Provide a concise analysis as bullet points. Highlight exact templates where applicable.
"""


def build_creator_prompt(profile: dict, settings: dict, auditor_insights: str, analyst_patterns: str) -> str:
    requested_days = DEFAULT_POST_DAYS[: settings["posts_per_week"]]
    tolerance = max(20, int(settings["post_length"] * 0.15))
    min_words = max(40, settings["post_length"] - tolerance)
    max_words = settings["post_length"] + tolerance

    question_rule = "End some posts with an engaging question." if settings["include_question"] else "Do not add questions."
    cta_rule = "Add a clear call to action (CTA) at the end of each post." if settings["include_cta"] else "Do not add CTA copy."

    return f"""
You are an elite LinkedIn Ghostwriter. You will write a weekly content plan based on strategy guidelines and copywriter analyses.

Profile strategy:
- Expertise: {profile.get("expertise")}
- Audience: {profile.get("audience")}
- Tone: {profile.get("tone")}

Strategic Guidelines (from Auditor):
{auditor_insights}

Copywriting Patterns (from Analyst):
{analyst_patterns}

Write {settings["posts_per_week"]} distinct LinkedIn posts for these days: {", ".join(requested_days)}.

Constraints:
- Each post body must stay between {min_words} and {max_words} words (aiming for roughly {settings["post_length"]} words).
- Use an emoji density level of {settings["emoji_level"]} out of 5.
- Include exactly {settings["hashtag_count"]} relevant hashtags per post.
- Keep the writing hook-driven, spaced with empty lines for readability, and human-like.
- {question_rule}
- {cta_rule}

Return JSON only in this exact shape:
{{
  "summary": "A brief, one-sentence overview of this week's strategy theme",
  "posts": [
    {{
      "day": "DayName",
      "angle": "Description of the post's core message / angle",
      "hook": "Opening hook line",
      "post": "The full body copy of the post (excluding hook, CTA, and hashtags)",
      "hashtags": ["#Tag1", "#Tag2"],
      "cta": "The closing call-to-action text"
    }}
  ]
}}
"""


def build_single_post_prompt(profile: dict, settings: dict, reference_posts: list, day: str, angle: str, feedback: str = None) -> str:
    reference_lines = "\n".join(
        f"- {post['text']} (likes: {post.get('likes', 'n/a')})" for post in reference_posts
    ) if reference_posts else "No reference posts available"
    tolerance = max(20, int(settings["post_length"] * 0.15))
    min_words = max(40, settings["post_length"] - tolerance)
    max_words = settings["post_length"] + tolerance

    question_rule = "End with a thoughtful question." if settings["include_question"] else "Do not add a question."
    cta_rule = "Add a clear CTA at the end." if settings["include_cta"] else "Do not add CTA copy."
    feedback_block = f"\nAdditional correction:\n- {feedback}\n" if feedback else ""

    return f"""
You are an expert LinkedIn ghostwriter. Create one polished post.

Post Requirements:
- Day: {day}
- Angle: {angle}
- Tone: {profile["tone"]}
- Expertise: {profile["expertise"]}
- Target Audience: {profile["audience"]}

Style Reference:
{reference_lines}

Rules:
- Post body must be between {min_words} and {max_words} words.
- Emoji level: {settings["emoji_level"]}/5.
- Add exactly {settings["hashtag_count"]} hashtags.
- Short hooks and natural spacing are critical.
- {question_rule}
- {cta_rule}
{feedback_block}

Return JSON only:
{{
  "day": "{day}",
  "angle": "{angle}",
  "hook": "Opening line",
  "post": "Full body copy of the post (excluding hook, CTA, and hashtags)",
  "hashtags": ["#Example"],
  "cta": "Closing CTA"
}}
"""


def build_refine_post_prompt(profile: dict, settings: dict, post: dict, instruction: str) -> str:
    tolerance = max(20, int(settings["post_length"] * 0.15))
    min_words = max(40, settings["post_length"] - tolerance)
    max_words = settings["post_length"] + tolerance

    return f"""
You are an expert LinkedIn copyeditor. Your task is to edit and refine a single post based on direct user instructions.

Original Post:
- Day: {post.get("day")}
- Angle: {post.get("angle")}
- Hook: {post.get("hook")}
- Body: {post.get("post")}
- CTA: {post.get("cta")}
- Hashtags: {", ".join(post.get("hashtags", []))}

Tone Context: {profile.get("tone")}
Target Word Count: {settings.get("post_length")} words (Range: {min_words}-{max_words})

USER REFINEMENT INSTRUCTION:
"{instruction}"

Apply the user's instruction precisely. Retain the day and angle. Keep the text formatted for LinkedIn with spacing.
Maintain emoji level {settings.get("emoji_level")}/5 and exactly {settings.get("hashtag_count")} hashtags unless the user specifies otherwise in their instruction.

Return JSON only:
{{
  "day": "{post.get("day")}",
  "angle": "{post.get("angle")}",
  "hook": "Refined opening line",
  "post": "Refined body copy of the post (excluding hook, CTA, and hashtags)",
  "hashtags": ["#Tag1"],
  "cta": "Refined CTA"
}}
"""
