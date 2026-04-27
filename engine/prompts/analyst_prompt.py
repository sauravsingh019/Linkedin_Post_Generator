def analyst_prompt(posts: list) -> str:
    return f"""
You are a LinkedIn content analyst.

Analyze the following high-performing posts and extract:
- Hook patterns
- CTA styles
- Content formats

Posts:
{posts}

Return concise patterns.
"""
