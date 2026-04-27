from config.settings import DEFAULT_POST_DAYS


def build_weekly_plan_prompt(profile, settings, reference_posts, feedback=None):
    requested_days = DEFAULT_POST_DAYS[: settings["posts_per_week"]]
    theme_lines = "\n".join(f"- {theme}" for theme in profile["themes"]) or "- Use a thoughtful mix of practical and personal angles"
    reference_lines = "\n".join(
        f"- {post['text']} (likes: {post.get('likes', 'n/a')})" for post in reference_posts
    ) or "- No reference posts available"
    tolerance = max(20, int(settings["post_length"] * 0.15))
    min_words = max(40, settings["post_length"] - tolerance)
    max_words = settings["post_length"] + tolerance

    question_rule = "End some posts with a thoughtful question." if settings["include_question"] else "Do not add questions."
    cta_rule = "Add a clear CTA at the end of each post." if settings["include_cta"] else "Do not add CTA copy."
    feedback_block = f"\nAdditional correction:\n- {feedback}\n" if feedback else ""

    return f"""
You are an expert LinkedIn ghostwriter creating a weekly content plan.

Create {settings["posts_per_week"]} distinct LinkedIn posts for these days: {", ".join(requested_days)}.

Profile:
- Expertise: {profile["expertise"]}
- Audience: {profile["audience"]}
- Tone: {profile["tone"]}
- Goal: {profile["goal"]}

Themes to cover:
{theme_lines}

Reference posts with strong engagement:
{reference_lines}

Rules:
- Each post body must stay between {min_words} and {max_words} words.
- Aim for about {settings["post_length"]} words, but never go above {max_words}.
- Use an emoji level of {settings["emoji_level"]} out of 5.
- Include exactly {settings["hashtag_count"]} hashtags per post.
- Keep the writing polished, natural, and specific.
- Avoid repetitive hooks and repeated sentence structure.
- Make each day feel meaningfully different from the others.
- Keep hashtags relevant and not spammy.
- The hook should be short and strong.
- The CTA should feel natural, not salesy.
- {question_rule}
- {cta_rule}
{feedback_block}

Return JSON only.
"""


def build_single_post_prompt(profile, settings, reference_posts, day, angle, feedback=None):
    theme_lines = "\n".join(f"- {theme}" for theme in profile["themes"]) or "- Use a thoughtful mix of practical and personal angles"
    reference_lines = "\n".join(
        f"- {post['text']} (likes: {post.get('likes', 'n/a')})" for post in reference_posts
    ) or "- No reference posts available"
    tolerance = max(20, int(settings["post_length"] * 0.15))
    min_words = max(40, settings["post_length"] - tolerance)
    max_words = settings["post_length"] + tolerance

    question_rule = "End with a thoughtful question." if settings["include_question"] else "Do not add a question."
    cta_rule = "Add a clear CTA at the end." if settings["include_cta"] else "Do not add CTA copy."
    feedback_block = f"\nAdditional correction:\n- {feedback}\n" if feedback else ""

    return f"""
You are an expert LinkedIn ghostwriter creating one polished LinkedIn post.

Create one post for:
- Day: {day}
- Angle: {angle}

Profile:
- Expertise: {profile["expertise"]}
- Audience: {profile["audience"]}
- Tone: {profile["tone"]}
- Goal: {profile["goal"]}

Themes to consider:
{theme_lines}

Reference posts with strong engagement:
{reference_lines}

Rules:
- The post body must stay between {min_words} and {max_words} words.
- Aim for about {settings["post_length"]} words, but never go above {max_words}.
- Use an emoji level of {settings["emoji_level"]} out of 5.
- Include exactly {settings["hashtag_count"]} hashtags.
- Keep the hook short and strong.
- Keep the CTA natural and not salesy.
- Make the writing specific, polished, and non-repetitive.
- {question_rule}
- {cta_rule}
{feedback_block}

Return JSON only in this shape:
{{
  "day": "{day}",
  "angle": "{angle}",
  "hook": "Opening line",
  "post": "Full LinkedIn post",
  "hashtags": ["#Example"],
  "cta": "Closing CTA"
}}
"""
