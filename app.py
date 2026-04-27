import json

import streamlit as st

from config.settings import APP_DESCRIPTION, APP_TITLE, DEFAULT_MODEL
from engine.llm.ollama_client import OllamaClient, OllamaConnectionError
from engine.services.post_generator import generate_weekly_plan, regenerate_single_post
from engine.utils.helpers import (
    build_download_bundle,
    render_calendar_preview,
    render_live_preview,
    plan_to_markdown,
    render_overview_metrics,
    render_post_card,
)


st.set_page_config(page_title=APP_TITLE, page_icon=":memo:", layout="wide")


def init_state() -> None:
    defaults = {
        "weekly_plan": None,
        "generation_error": None,
        "profile_snapshot": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def sidebar_controls(client: OllamaClient) -> tuple[str, dict]:
    st.sidebar.title("LinkedIn Post Studio")
    st.sidebar.caption(APP_DESCRIPTION)

    models = client.list_models()
    model_names = [model["name"] for model in models] or [DEFAULT_MODEL]
    default_index = model_names.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_names else 0

    selected_model = st.sidebar.selectbox("Ollama model", model_names, index=default_index)

    settings = {
        "posts_per_week": st.sidebar.slider("Posts per week", 3, 7, 5),
        "post_length": st.sidebar.slider("Approx words per post", 80, 280, 160, step=10),
        "emoji_level": st.sidebar.slider("Emoji level", 0, 5, 2),
        "hashtag_count": st.sidebar.slider("Hashtags per post", 2, 8, 4),
        "include_question": st.sidebar.checkbox("Add engagement question", value=True),
        "include_cta": st.sidebar.checkbox("Add clear CTA", value=True),
    }

    if models:
        st.sidebar.success("Ollama is connected")
    else:
        st.sidebar.warning(
            "Could not read the Ollama model list. If Ollama is running, you can still try generating with the default model."
        )

    return selected_model, settings


def main() -> None:
    init_state()

    st.title(APP_TITLE)
    st.caption(APP_DESCRIPTION)

    client = OllamaClient()
    selected_model, settings = sidebar_controls(client)

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.subheader("Strategy")
        expertise = st.text_input(
            "Expertise / niche",
            placeholder="AI tools, career growth, data science, SaaS marketing...",
        )
        audience = st.text_input(
            "Target audience",
            placeholder="Recruiters, founders, developers, students...",
        )
        tone = st.selectbox(
            "Tone",
            ["Professional", "Storytelling", "Educational", "Bold", "Inspirational"],
        )
        goal = st.text_area(
            "What should these posts help you achieve?",
            placeholder="Build personal brand, attract hiring managers, get consulting leads, grow authority...",
            height=120,
        )
        themes = st.text_area(
            "Weekly themes or talking points",
            placeholder="Write one idea per line: lessons learned, client wins, hiring advice, framework breakdowns...",
            height=120,
        )

        generate_clicked = st.button("Generate weekly plan", type="primary", use_container_width=True)

    with right:
        st.subheader("What you'll get")
        st.markdown(
            """
- weekly content structure you can scan quickly
- target word-range guidance before generation
- better post-by-post refinement after generation
"""
        )
        render_live_preview(
            profile={
                "expertise": expertise.strip(),
                "audience": audience.strip(),
                "tone": tone,
                "goal": goal.strip(),
                "themes": [line.strip() for line in themes.splitlines() if line.strip()],
            },
            settings=settings,
        )

    if generate_clicked:
        missing_fields = [label for label, value in {
            "Expertise / niche": expertise.strip(),
            "Target audience": audience.strip(),
            "Goal": goal.strip(),
        }.items() if not value]

        if missing_fields:
            st.session_state["generation_error"] = f"Please fill: {', '.join(missing_fields)}"
            st.session_state["weekly_plan"] = None
        else:
            st.session_state["generation_error"] = None
            profile_payload = {
                "expertise": expertise.strip(),
                "audience": audience.strip(),
                "tone": tone,
                "goal": goal.strip(),
                "themes": [line.strip() for line in themes.splitlines() if line.strip()],
            }
            st.session_state["profile_snapshot"] = profile_payload
            with st.spinner("Generating your weekly LinkedIn plan..."):
                try:
                    st.session_state["weekly_plan"] = generate_weekly_plan(
                        client=client,
                        model=selected_model,
                        profile=profile_payload,
                        settings=settings,
                    )
                except OllamaConnectionError as exc:
                    st.session_state["weekly_plan"] = None
                    st.session_state["generation_error"] = str(exc)
                except Exception as exc:  # pragma: no cover - UI fallback
                    st.session_state["weekly_plan"] = None
                    st.session_state["generation_error"] = f"Generation failed: {exc}"

    if st.session_state["generation_error"]:
        st.error(st.session_state["generation_error"])

    plan = st.session_state["weekly_plan"]
    if not plan:
        st.info("Fill in your strategy on the left, then generate your weekly LinkedIn plan.")
        return

    st.divider()
    render_overview_metrics(plan)
    render_calendar_preview(plan, settings["post_length"])

    download_markdown, download_json = build_download_bundle(plan)
    download_col_1, download_col_2 = st.columns(2)
    download_col_1.download_button(
        "Download markdown",
        data=download_markdown,
        file_name="linkedin_weekly_plan.md",
        mime="text/markdown",
        use_container_width=True,
    )
    download_col_2.download_button(
        "Download JSON",
        data=download_json,
        file_name="linkedin_weekly_plan.json",
        mime="application/json",
        use_container_width=True,
    )

    st.subheader("Weekly plan")
    profile_snapshot = st.session_state.get("profile_snapshot") or {
        "expertise": expertise.strip(),
        "audience": audience.strip(),
        "tone": tone,
        "goal": goal.strip(),
        "themes": [line.strip() for line in themes.splitlines() if line.strip()],
    }

    for index, post in enumerate(plan["posts"]):
        render_post_card(post, target_words=settings["post_length"])
        button_key = f"regen_post_{index}_{post['day']}"
        if st.button(f"Regenerate {post['day']} post", key=button_key, use_container_width=True):
            with st.spinner(f"Regenerating {post['day']}..."):
                try:
                    refreshed_post = regenerate_single_post(
                        client=client,
                        model=selected_model,
                        profile=profile_snapshot,
                        settings=settings,
                        post=post,
                    )
                    st.session_state["weekly_plan"]["posts"][index] = refreshed_post
                    st.session_state["generation_error"] = None
                    st.rerun()
                except OllamaConnectionError as exc:
                    st.session_state["generation_error"] = str(exc)
                    st.rerun()
                except Exception as exc:  # pragma: no cover - UI fallback
                    st.session_state["generation_error"] = f"Regeneration failed: {exc}"
                    st.rerun()

    with st.expander("Markdown preview"):
        st.code(plan_to_markdown(plan), language="markdown")

    with st.expander("Raw JSON"):
        st.code(json.dumps(plan, indent=2, ensure_ascii=False), language="json")


if __name__ == "__main__":
    main()
