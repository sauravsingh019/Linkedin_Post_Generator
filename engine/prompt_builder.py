def build_prompt(data: dict):
    return f"""
You are a professional LinkedIn content writer.

GOAL:
Generate ONE authentic, human-like LinkedIn post.

USER INPUT:
Topic / Expertise: {data['expertise']}
Audience: {data['audience']}
Tone: {data['tone']}
User Idea / Thoughts:
{data['purpose']}

CONSTRAINTS:
- Approx {data['post_length']} words
- Emoji level: {data['emoji_level']} (0 = none, 3 = high)
- Add exactly {data['hashtag_count']} hashtags at the END
- No repeated sentences
- No generic filler lines
- Do NOT sound like AI

STRUCTURE:
1. Strong hook (first 2 lines)
2. Personal insight / learning
3. Value for audience
4. Clear CTA (question or action)

STYLE:
- Short paragraphs
- LinkedIn-friendly spacing
- Natural human flow

IMPORTANT:
Write only the final post. Nothing else.
"""
