from engine.llm.ollama_client import call_llm
import json
import re

def creator_agent(state):
    profile = state["user_profile"]
    patterns = state["patterns"]

    prompt = f"""
You are an AI LinkedIn Growth Engine.

User profile:
{profile}

Winning LinkedIn patterns:
{patterns}

Generate a 7-day LinkedIn content plan.
Each post must:
- Follow the hook & CTA patterns
- Match the tone and audience
- Include hashtags

Return STRICT JSON in this format:
[
  {{
    "day": "Monday",
    "type": "Story / Tip / Hiring / Personal",
    "post": "Full LinkedIn post",
    "hashtags": ["#AI", "#Careers"]
  }}
]
"""

    raw = call_llm(prompt)

    match = re.search(r"\[.*\]", raw, re.S)
    if match:
        data = json.loads(match.group())
    else:
        data = []

    state["weekly_posts"] = data
    return state
