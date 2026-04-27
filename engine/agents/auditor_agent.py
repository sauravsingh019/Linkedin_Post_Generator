from engine.prompts.auditor_prompt import auditor_prompt
from engine.llm.ollama_client import call_llm

def auditor_agent(state):
    profile = state["user_profile"]

    prompt = f"""
You are a LinkedIn branding expert.

From this user profile, extract ONLY writing style hints.

Return ONLY a short bullet list of:
- Preferred tone
- Audience focus
- Content angle

Do NOT explain.
Do NOT write paragraphs.
Do NOT add examples.

User profile:
{profile}
"""

    patterns = call_llm(prompt)

    state["patterns"] = [patterns]
    return state
