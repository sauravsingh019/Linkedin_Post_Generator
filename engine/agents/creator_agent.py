from engine.prompts.creator_prompt import build_creator_prompt


def creator_agent(state: dict) -> dict:
    profile = state["user_profile"]
    settings = state["settings"]
    auditor_insights = state.get("auditor_insights", "")
    analyst_patterns = state.get("analyst_patterns", "")
    client = state["client"]
    model = state["model"]

    prompt = build_creator_prompt(profile, settings, auditor_insights, analyst_patterns)

    schema = {
        "summary": "One short sentence summarizing the week's approach",
        "posts": [
            {
                "day": "Monday",
                "angle": "Brief theme description",
                "hook": "Strong opening line",
                "post": "Main body text formatted with line breaks",
                "hashtags": ["#Topic"],
                "cta": "Engaging CTA / Question"
            }
        ]
    }

    try:
        if hasattr(client, "list_models"):  # OllamaClient
            plan = client.generate_json(prompt, schema=schema, model=model)
        else:  # GeminiClient
            plan = client.generate_json(prompt, schema=schema)
        state["weekly_plan"] = plan
    except Exception as exc:
        state["error"] = f"Creator agent failed: {exc}"
        state["weekly_plan"] = {}

    return state
