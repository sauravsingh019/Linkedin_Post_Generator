from engine.prompts.creator_prompt import build_analyst_prompt


def analyst_agent(state: dict) -> dict:
    reference_posts = state.get("reference_posts", [])
    client = state["client"]
    model = state["model"]

    prompt = build_analyst_prompt(reference_posts)

    try:
        if hasattr(client, "list_models"):  # OllamaClient
            patterns = client.generate(prompt, model=model)
        else:  # GeminiClient
            patterns = client.generate(prompt)
        state["analyst_patterns"] = patterns
    except Exception as exc:
        state["error"] = f"Analyst agent failed: {exc}"
        state["analyst_patterns"] = (
            "- Hook pattern: Start with a personal insight, hook-driven quote, or failure-to-success narrative.\n"
            "- Structure: Break thoughts into single-line spacings. Use bullet points for list details.\n"
            "- CTA pattern: End with a soft, relevant question or call-to-action that encourages comment engagement."
        )

    return state
