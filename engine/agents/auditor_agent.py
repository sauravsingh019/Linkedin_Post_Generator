from engine.prompts.creator_prompt import build_auditor_prompt


def auditor_agent(state: dict) -> dict:
    profile = state["user_profile"]
    client = state["client"]
    model = state["model"]

    prompt = build_auditor_prompt(profile)

    try:
        if hasattr(client, "list_models"):  # OllamaClient
            insights = client.generate(prompt, model=model)
        else:  # GeminiClient
            insights = client.generate(prompt)
        state["auditor_insights"] = insights
    except Exception as exc:
        state["error"] = f"Auditor agent failed: {exc}"
        state["auditor_insights"] = (
            "Position as an industry expert. Focus on educational insights, "
            "clear frameworks, and direct value to the target audience."
        )

    return state
