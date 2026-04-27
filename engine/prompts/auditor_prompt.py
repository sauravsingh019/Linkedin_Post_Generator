def auditor_prompt(profile: dict) -> str:
    return f"""
You are a LinkedIn profile auditor.

Analyze the following user profile and extract:
- Niche
- Target audience
- Writing tone
- Content themes

Profile:
{profile}

Return insights as bullet points.
"""
