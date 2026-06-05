import base64
import json
import os
from pathlib import Path
import requests
import streamlit as st

from config.settings import APP_DESCRIPTION, APP_TITLE, DEFAULT_MODEL
from engine.llm.gemini_client import GeminiClient
from engine.llm.ollama_client import OllamaClient, ensure_ollama_running
from engine.services.post_generator import (
    generate_weekly_plan,
    regenerate_single_post,
    refine_post_with_ai,
)
from engine.utils.helpers import (
    build_download_bundle,
    count_words,
    plan_to_markdown,
    render_calendar_preview,
    render_copy_button,
    render_live_preview,
    render_overview_metrics,
    render_post_card,
    to_unicode_bold,
    to_unicode_italic,
    show_preview_dialog,
    render_linkedin_feed_preview,
)

# Page Configuration
st.set_page_config(page_title=APP_TITLE, page_icon=":chart_with_upwards_trend:", layout="wide")

DATA_PATH = Path(__file__).resolve().parent / "data" / "posts.json"
CACHE_PATH = Path(__file__).resolve().parent / "data" / "embeddings_cache.json"


def load_inspiration_posts() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    try:
        with DATA_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_inspiration_posts(posts: list[dict]):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    # Invalidate RAG embeddings cache immediately to force rebuild
    if CACHE_PATH.exists():
        try:
            CACHE_PATH.unlink()
        except Exception:
            pass


def init_session_state() -> None:
    defaults = {
        "weekly_plan": None,
        "generation_error": None,
        "profile_snapshot": None,
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "provider": "Local Ollama",
        "ollama_active": False,
        "linkedin_token": os.environ.get("LINKEDIN_ACCESS_TOKEN", ""),
        "linkedin_urn": "",
        "linkedin_display_name": "Your Name",
        "scheduled_posts": [],
        "form_expertise": "",
        "form_audience_select": "Founders & Entrepreneurs",
        "form_audience_custom": "",
        "form_goal": "",
        "form_themes": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def inject_custom_styles() -> None:
    """Inject premium CSS styling overrides for Streamlit elements."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

        /* Base Theme Overrides with Custom Fonts */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', 'Outfit', -apple-system, sans-serif !important;
            background-color: #080d1a !important;
            color: #cbd5e1 !important;
        }

        /* Slide-up animations for content loading */
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .stTabs, div[data-testid="stVerticalBlock"] > div {
            animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
        }

        /* Sidebar Glassmorphic Style */
        section[data-testid="stSidebar"] {
            background-color: #0c1224 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        /* Sleek startup headings */
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif !important;
            letter-spacing: -0.5px !important;
            font-weight: 700 !important;
            color: #f8fafc !important;
        }

        /* Centered Tabs styling list (centered across screen) */
        .stTabs [data-baseweb="tab-list"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            gap: 12px;
            background-color: rgba(12, 18, 36, 0.7);
            backdrop-filter: blur(8px);
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 24px;
            border-radius: 8px;
            color: #94a3b8;
            font-weight: 600;
            border: none;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #38bdf8;
            background-color: rgba(255, 255, 255, 0.03);
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(56, 189, 248, 0.1) !important;
            color: #38bdf8 !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
        }

        /* Premium 3D buttons with animated depth for ALL clickable buttons */
        div.stButton > button, 
        div.stDownloadButton > button, 
        button[data-testid*="baseButton"] {
            border-radius: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px !important;
            transition: all 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            transform: translateY(0) !important;
        }

        /* Primary and standard 3D buttons */
        div.stButton > button:first-child, 
        div.stDownloadButton > button:first-child,
        button[data-testid*="baseButton-primary"] {
            background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%) !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 0px #312e81, 0 8px 15px rgba(99, 102, 241, 0.25) !important; /* Premium matching indigo bottom shadow */
        }
        div.stButton > button:first-child:hover, 
        div.stDownloadButton > button:first-child:hover,
        button[data-testid*="baseButton-primary"]:hover {
            background: linear-gradient(135deg, #7073f3 0%, #4ec5f9 100%) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 0px #312e81, 0 12px 20px rgba(99, 102, 241, 0.4) !important;
        }
        div.stButton > button:first-child:active, 
        div.stDownloadButton > button:first-child:active,
        button[data-testid*="baseButton-primary"]:active {
            transform: translateY(2px) !important;
            box-shadow: 0 1px 0px #312e81, 0 4px 6px rgba(99, 102, 241, 0.15) !important;
        }

        /* Secondary actions button style override (styled in gradient as requested) */
        div.stButton > button[kind="secondary"],
        button[data-testid*="baseButton-secondary"] {
            background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%) !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 0px #312e81, 0 8px 15px rgba(99, 102, 241, 0.25) !important;
        }
        div.stButton > button[kind="secondary"]:hover,
        button[data-testid*="baseButton-secondary"]:hover {
            background: linear-gradient(135deg, #7073f3 0%, #4ec5f9 100%) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 0px #312e81, 0 12px 20px rgba(99, 102, 241, 0.4) !important;
        }
        div.stButton > button[kind="secondary"]:active,
        button[data-testid*="baseButton-secondary"]:active {
            transform: translateY(2px) !important;
            box-shadow: 0 1px 0px #312e81, 0 4px 6px rgba(99, 102, 241, 0.15) !important;
        }

        /* Backdrop filter blur for dialog overlays (ONLY blur the background overlay behind the popup) */
        div[data-testid="stModalBackdrop"] {
            backdrop-filter: blur(12px) !important;
            background-color: rgba(8, 13, 26, 0.6) !important;
        }
        
        /* Ensure the dialog itself is sharp and clear */
        div[data-testid="stDialog"], 
        div[role="dialog"], 
        div[data-testid="stModal"] {
            backdrop-filter: none !important;
        }

        /* Center the Streamlit modal dialog and remove border spacing */
        div[data-testid="stDialog"] {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            max-width: 580px !important;
            width: 100% !important;
            overflow: hidden !important;
            margin: auto !important;
        }
        
        div[data-testid="stDialog"] > div:first-child {
            background-color: transparent !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        /* Hide scrollbars inside dialog container wrapper */
        div[data-testid="stDialog"] iframe {
            overflow: hidden !important;
        }
        div[data-testid="stDialog"] .element-container {
            overflow: hidden !important;
        }
        div[data-testid="stDialog"] .stMarkdown {
            overflow: hidden !important;
        }
        div[data-testid="stDialog"] [data-testid="stVerticalBlock"] {
            overflow: hidden !important;
            gap: 0 !important;
            padding: 0 !important;
        }

        /* Expander Custom Card styling */
        div[data-testid="stExpander"] {
            background-color: rgba(12, 18, 36, 0.45) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            margin-bottom: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stExpander"]:hover {
            border-color: rgba(56, 189, 248, 0.2) !important;
        }

        /* Startup Glassmorphism Post Cards (USP) */
        .startup-post-card {
            background: rgba(12, 18, 36, 0.5) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-left: 4px solid #6366f1 !important;
            border-radius: 16px !important;
            padding: 24px !important;
            margin: 18px 0 !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15) !important;
        }
        .startup-post-card:hover {
            transform: translateY(-4px) !important;
            border-left-color: #38bdf8 !important;
            border-color: rgba(56, 189, 248, 0.2) !important;
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15) !important;
        }
        .startup-post-hook {
            font-size: 1.15em !important;
            font-weight: 700 !important;
            color: #ffffff !important;
            margin-bottom: 14px !important;
            line-height: 1.4 !important;
        }
        .startup-post-body {
            font-size: 0.98em !important;
            color: #cbd5e1 !important;
            line-height: 1.65 !important;
            white-space: pre-wrap !important;
        }
        .startup-post-cta {
            font-size: 1em !important;
            font-weight: 600 !important;
            color: #38bdf8 !important;
            margin-top: 14px !important;
            line-height: 1.4 !important;
        }
        .startup-post-tags {
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
            font-size: 0.9em !important;
            color: #818cf8 !important;
            margin-top: 10px !important;
        }

        /* Auto-resizing Textareas without scrollbars (grow/shrink as user types) */
        textarea {
            field-sizing: content !important;
            height: auto !important;
            min-height: 90px !important;
            overflow-y: hidden !important;
            resize: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# (Local render_linkedin_feed_preview moved to engine/utils/helpers.py to avoid duplication)


def main() -> None:
    init_session_state()
    inject_custom_styles()

    # Premium Startup Hero Section
    st.markdown(
        """
        <div style="text-align: center; margin-top: 10px; margin-bottom: 30px;">
            <span style="
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(56, 189, 248, 0.15) 100%);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                padding: 6px 16px;
                border-radius: 30px;
                font-size: 0.8em;
                font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
            ">
                ⚡ Powered by LangGraph & Gemini
            </span>
            <h1 style="font-size: 3.2em; margin-top: 15px; background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">
                LinkedIn Post Studio
            </h1>
            <p style="color: #94a3b8; font-size: 1.15em; max-width: 600px; margin: 0 auto; line-height: 1.5;">
                Orchestrate multi-agent workflows to build, style, and refine high-converting content pipelines.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize Active client based on selection
    gemini_key = st.session_state["gemini_api_key"]
    provider = st.session_state["provider"]

    if provider == "Google Gemini":
        client = GeminiClient(api_key=gemini_key)
        selected_model = "gemini-2.5-flash"
    else:
        client = OllamaClient()
        selected_model = DEFAULT_MODEL

    # 1. Background Daemon Check & Start Hook (Optimized: check only once on startup if local selected)
    if provider == "Local Ollama" and not st.session_state["ollama_active"] and not st.session_state.get("ollama_checked", False):
        st.session_state["ollama_checked"] = True
        with st.spinner("Checking local Ollama service..."):
            is_running = ensure_ollama_running()
            st.session_state["ollama_active"] = is_running

    # Main Tabs Interface
    tab_creator, tab_calendar, tab_library, tab_settings = st.tabs(
        ["📝 Post Studio", "📅 Content Calendar", "💡 Inspiration Library", "⚙️ Engine Settings"]
    )

    # ==================== SETTINGS TAB ====================
    with tab_settings:
        st.subheader("Model Engine Configurations")

        provider_select = st.radio(
            "Select AI Provider",
            ["Local Ollama", "Google Gemini"],
            index=0 if provider == "Local Ollama" else 1,
        )

        if provider_select != provider:
            st.session_state["provider"] = provider_select
            # Reset checked flag if user switches provider so they can trigger check
            if "ollama_checked" in st.session_state:
                del st.session_state["ollama_checked"]
            st.rerun()

        if provider_select == "Google Gemini":
            api_key_input = st.text_input(
                "Gemini API Key",
                value=gemini_key,
                type="password",
                help="Configure your Google Gemini API Key. It is only held in browser session memory.",
            )
            if api_key_input != gemini_key:
                st.session_state["gemini_api_key"] = api_key_input
                st.rerun()

            if client.is_configured():
                st.success("Gemini API key is configured!")
            else:
                st.warning("Please enter your Gemini API key to proceed.")

        else:  # Local Ollama
            st.markdown("### local Ollama Management")
            if st.session_state["ollama_active"]:
                st.success("Ollama service daemon is running locally.")
                models = client.list_models()
                model_names = [model["name"] for model in models] or [DEFAULT_MODEL]
                default_index = model_names.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_names else 0

                ollama_model_select = st.selectbox(
                    "Select Local Model", model_names, index=default_index
                )

                # Auto-Pull tool
                st.markdown("---")
                st.markdown("**Model Downloader**")
                pull_name = st.text_input("Enter model name to pull", value="mistral")
                if st.button("Download Model"):
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()
                    try:
                        for chunk in client.pull_model_stream(pull_name):
                            status_text.write(f"Status: **{chunk['status']}**")
                            progress_bar.progress(chunk["progress"] / 100.0)
                        st.success(f"Model '{pull_name}' downloaded successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Download failed: {e}")
            else:
                st.error("Could not establish a connection to local Ollama (localhost:11434).")
                st.info("Make sure Ollama is installed on your computer and running in the background.")

        # LinkedIn Config Panel
        st.markdown("---")
        st.subheader("🔗 LinkedIn Integration Settings")
        st.caption("Publish directly to your feed. Set an OAuth developer token here.")
        
        li_token = st.text_input(
            "LinkedIn Member Access Token",
            value=st.session_state["linkedin_token"],
            type="password"
        )
        if li_token != st.session_state["linkedin_token"]:
            st.session_state["linkedin_token"] = li_token
            st.rerun()

        if li_token.strip():
            if st.button("🔌 Test LinkedIn Connection"):
                headers = {
                    "Authorization": f"Bearer {li_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                }
                try:
                    res = requests.get("https://api.linkedin.com/v2/me", headers=headers, timeout=10)
                    if res.status_code == 200:
                        profile = res.json()
                        first_name = profile.get("localizedFirstName", "")
                        last_name = profile.get("localizedLastName", "")
                        st.session_state["linkedin_urn"] = f"urn:li:person:{profile.get('id', '')}"
                        st.session_state["linkedin_display_name"] = f"{first_name} {last_name}".strip() or "Your Name"
                        st.success(f"Connected successfully! Profile: **{first_name} {last_name}** ({st.session_state['linkedin_urn']})")
                    else:
                        st.error(f"Failed connection check. Status: {res.status_code}. Response: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.info("Direct publishing is locked. Provide a token to activate.")

    # ==================== POST CREATOR WORKSPACE ====================
    with tab_creator:
        # Strategy Blueprint Templates (5 Options: Tech and Non-Tech)
        st.markdown("### 💡 Strategy Blueprint Templates")
        st.caption("Click a prebuilt blueprint below to fill in high-converting themes and goals automatically.")
        col_x, col_y, col_z, col_w, col_v = st.columns(5)
        with col_x:
            if st.button("🤖 AI Engineer"):
                st.session_state["form_expertise"] = "AI Engineering & LLMs"
                st.session_state["form_audience_select"] = "Software Engineers & Tech Leads"
                st.session_state["form_audience_custom"] = ""
                st.session_state["form_themes"] = (
                    "Why agentic workflows are replacing raw prompt engineering\n"
                    "Building local RAG pipelines with Ollama in under 10 minutes\n"
                    "Fine-tuning vs RAG: When to use which for small LLMs"
                )
                st.session_state["form_goal"] = "Grow technical authority, share actionable tutorials, and attract B2B consulting contracts."
                st.rerun()
        with col_y:
            if st.button("💻 Full-Stack Dev"):
                st.session_state["form_expertise"] = "Full-Stack Development"
                st.session_state["form_audience_select"] = "Software Engineers & Tech Leads"
                st.session_state["form_audience_custom"] = ""
                st.session_state["form_themes"] = (
                    "Scaling Next.js apps beyond 100k active users\n"
                    "Why clean architecture is worth the initial design slowdown\n"
                    "Choosing database systems: self-hosted pgSQL vs managed DBaaS"
                )
                st.session_state["form_goal"] = "Build engineering credibility, demonstrate clean architecture practices, and secure contract dev gigs."
                st.rerun()
        with col_z:
            if st.button("📈 B2B SaaS Growth"):
                st.session_state["form_expertise"] = "B2B SaaS Marketing"
                st.session_state["form_audience_select"] = "Founders & Entrepreneurs"
                st.session_state["form_audience_custom"] = ""
                st.session_state["form_themes"] = (
                    "Fixing B2B SaaS onboarding drop-off bottlenecks\n"
                    "How we built an inbound content machine that drove $10k MRR\n"
                    "Why cold emailing developers is completely broken"
                )
                st.session_state["form_goal"] = "Generate qualified inbound leads for our marketing agency and grow founder authority."
                st.rerun()
        with col_w:
            if st.button("🎨 UX/UI Design"):
                st.session_state["form_expertise"] = "UX/UI Design & Product Strategy"
                st.session_state["form_audience_select"] = "Founders & Entrepreneurs"
                st.session_state["form_audience_custom"] = ""
                st.session_state["form_themes"] = (
                    "Heuristic user errors that are killing landing page conversions\n"
                    "Contrast ratios and spacing rules for modern dark mode UI layouts\n"
                    "Why prototyping with lorem ipsum copy ruins product validation"
                )
                st.session_state["form_goal"] = "Highlight product strategy skills, share design teardowns, and secure startup design contracts."
                st.rerun()
        with col_v:
            if st.button("✍️ Content Creator"):
                st.session_state["form_expertise"] = "Personal Branding & Copywriting"
                st.session_state["form_audience_select"] = "Marketers & Content Creators"
                st.session_state["form_audience_custom"] = ""
                st.session_state["form_themes"] = (
                    "Writing LinkedIn hooks that stop the feed scroll\n"
                    "Lessons from publishing daily for 100 days straight\n"
                    "The creator tools stack I use to produce 5 weekly posts"
                )
                st.session_state["form_goal"] = "Build personal brand reach, grow email newsletter list, and sell digital template products."
                st.rerun()

        st.markdown("---")
        

        left, right = st.columns([1.1, 0.9], gap="large")

        with left:
            st.subheader("Content Strategy & Niche")
            
            # Form Inputs bound directly to st.session_state keys
            expertise = st.text_input(
                "Expertise / Niche",
                key="form_expertise",
                placeholder="AI engineering, B2B SaaS marketing, personal branding...",
            )
            
            AUDIENCES = [
                "Founders & Entrepreneurs", 
                "Software Engineers & Tech Leads", 
                "Recruiters & HR Professionals", 
                "Marketers & Content Creators", 
                "Consultants & Freelancers",
                "General Professionals",
                "Custom (Type below)..."
            ]
            
            current_sel = st.session_state.get("form_audience_select", "Founders & Entrepreneurs")
            if current_sel not in AUDIENCES:
                current_sel = "Custom (Type below)..."
                
            audience_selection = st.selectbox(
                "Target Audience",
                AUDIENCES,
                index=AUDIENCES.index(current_sel),
                key="form_audience_select_box"
            )
            
            # Sync selection key
            st.session_state["form_audience_select"] = audience_selection
            
            if audience_selection == "Custom (Type below)...":
                audience = st.text_input(
                    "Type target audience",
                    key="form_audience_custom",
                    placeholder="Enter custom audience...",
                )
            else:
                audience = audience_selection
                
            tone = st.selectbox(
                "Tone & Voice",
                ["Professional", "Storytelling", "Educational", "Bold", "Inspirational"],
            )
            goal = st.text_area(
                "Primary Post Goal",
                key="form_goal",
                placeholder="Generate consulting leads, position as authority, drive newsletter signups...",
            )
            themes = st.text_area(
                "Weekly Themes / Talking Points (one per line)",
                key="form_themes",
                placeholder="Lessons from early failures\nWhy SaaS pricing is broken\nFramework for hiring interns",
            )

            # Sidebar strategy parameters
            st.markdown("---")
            st.markdown("#### Plan Parameters")
            col_a, col_b = st.columns(2)
            with col_a:
                posts_per_week = st.slider("Weekly Frequency", 3, 7, 5)
                # Word limit extended to 500
                post_length = st.slider("Target Words per Post", 80, 500, 160, step=10)
            with col_b:
                emoji_level = st.slider("Emoji Density (0-5)", 0, 5, 2)
                hashtag_count = st.slider("Hashtags per Post", 2, 8, 4)

            include_question = st.checkbox("Add engagement questions", value=True)
            include_cta = st.checkbox("Add call-to-actions (CTAs)", value=True)

            settings = {
                "posts_per_week": posts_per_week,
                "post_length": post_length,
                "emoji_level": emoji_level,
                "hashtag_count": hashtag_count,
                "include_question": include_question,
                "include_cta": include_cta,
            }

            # Generate Action
            generate_clicked = st.button("✨ Compile Weekly Plan", type="primary")

        with right:
            # Blueprint Live Preview
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
            missing_fields = [
                label
                for label, val in {
                    "Expertise": expertise.strip(),
                    "Target Audience": audience.strip(),
                    "Post Goal": goal.strip(),
                }.items()
                if not val
            ]

            if missing_fields:
                st.session_state["generation_error"] = f"Please complete: {', '.join(missing_fields)}"
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

                # Active model/client validation
                if provider == "Google Gemini" and not client.is_configured():
                    st.error("Please configure your Gemini API Key in Engine Settings tab first.")
                elif provider == "Local Ollama" and not st.session_state["ollama_active"]:
                    st.error("Ollama service is offline. Please start it locally.")
                else:
                    with st.spinner("Executing Auditor -> Analyst -> Creator LangGraph Workflow..."):
                        try:
                            st.session_state["weekly_plan"] = generate_weekly_plan(
                                client=client,
                                model=selected_model,
                                profile=profile_payload,
                                settings=settings,
                            )
                        except Exception as exc:
                            st.session_state["weekly_plan"] = None
                            st.session_state["generation_error"] = f"Pipeline execution failed: {exc}"

        if st.session_state["generation_error"]:
            st.error(st.session_state["generation_error"])

        # Display Weekly Post Workspace
        plan = st.session_state["weekly_plan"]
        if plan:
            st.markdown("---")
            render_overview_metrics(plan)

            # Plan Action Controls
            download_markdown, download_json = build_download_bundle(plan)
            d_col_1, d_col_2 = st.columns(2)
            d_col_1.download_button(
                "📥 Download Markdown Plan",
                data=download_markdown,
                file_name="linkedin_weekly_plan.md",
                mime="text/markdown",
                use_container_width=True,
            )
            d_col_2.download_button(
                "📥 Download JSON Bundle",
                data=download_json,
                file_name="linkedin_weekly_plan.json",
                mime="application/json",
                use_container_width=True,
            )

            st.subheader("⚡ Draft Post Workspace")
            profile_snapshot = st.session_state.get("profile_snapshot") or {
                "expertise": expertise.strip(),
                "audience": audience.strip(),
                "tone": tone,
                "goal": goal.strip(),
                "themes": [line.strip() for line in themes.splitlines() if line.strip()],
            }

            for index, post in enumerate(plan["posts"]):
                # Render post card with character limits
                render_post_card(post, target_words=settings["post_length"])

                # Post Actions Grid
                c1, c2 = st.columns([0.4, 0.6])
                with c1:
                    render_copy_button(
                        f"{post['hook']}\n\n{post['post']}\n\n{post['cta']}\n\n{' '.join(post['hashtags'])}",
                        button_key=f"copy_{index}_{post['day']}",
                    )

                    if st.button(f"Regenerate {post['day']} Post", key=f"regen_{index}_{post['day']}"):
                        with st.spinner(f"Refilling {post['day']} draft..."):
                            try:
                                refreshed = regenerate_single_post(
                                    client=client,
                                    model=selected_model,
                                    profile=profile_snapshot,
                                    settings=settings,
                                    post=post,
                                )
                                st.session_state["weekly_plan"]["posts"][index] = refreshed
                                st.rerun()
                            except Exception as e:
                                st.error(f"Regeneration failed: {e}")

                    # Media Upload / AI Image Gen Panel
                    with st.expander("🖼️ Media Attachments"):
                        local_path = Path(__file__).resolve().parent / "data" / f"{post['day'].lower()}_post_image.png"
                        media_b64 = ""
                        
                        uploaded_file = st.file_uploader(
                            "Upload custom post image", 
                            type=["png", "jpg", "jpeg"], 
                            key=f"media_file_{index}"
                        )
                        
                        if uploaded_file:
                            bytes_data = uploaded_file.read()
                            uploaded_file.seek(0)
                            local_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(local_path, "wb") as img_f:
                                img_f.write(bytes_data)
                            media_b64 = f"data:image/png;base64,{base64.b64encode(bytes_data).decode('utf-8')}"
                        elif local_path.exists():
                            with open(local_path, "rb") as img_f:
                                media_b64 = f"data:image/png;base64,{base64.b64encode(img_f.read()).decode('utf-8')}"
                                
                        st.markdown("**AI Image Generator**")
                        img_prompt = st.text_input(
                            "Describe target scene", 
                            placeholder="e.g. minimalist neon server setup, clean workspace mockup...", 
                            key=f"img_prompt_{index}"
                        )
                        if st.button("🎨 Generate AI Image", key=f"img_gen_{index}"):
                            if img_prompt.strip():
                                gemini_key = st.session_state.get("gemini_api_key", "").strip()
                                if not gemini_key:
                                    st.error("Please configure your Gemini API Key in the Engine Settings tab first to generate images.")
                                else:
                                    with st.spinner("Generating image via Gemini Imagen 3..."):
                                        try:
                                            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={gemini_key}"
                                            headers = {"Content-Type": "application/json"}
                                            payload = {
                                                "numberOfImages": 1,
                                                "prompt": img_prompt.strip(),
                                                "aspectRatio": "1:1",
                                                "outputMimeType": "image/png"
                                            }
                                            res = requests.post(url, headers=headers, json=payload, timeout=40)
                                            if res.status_code == 200:
                                                data = res.json()
                                                img_b64 = data["generatedImages"][0]["image"]["imageBytes"]
                                                img_bytes = base64.b64decode(img_b64)
                                                
                                                local_path.parent.mkdir(parents=True, exist_ok=True)
                                                with open(local_path, "wb") as img_f:
                                                    img_f.write(img_bytes)
                                                
                                                st.success("🎉 Image generated successfully and saved to disk!")
                                                st.rerun()
                                            else:
                                                st.error(f"Image generation failed: {res.status_code} - {res.text}")
                                        except Exception as e:
                                            st.error(f"Error calling Imagen API: {e}")

                    # Dynamic Popup Preview Button
                    display_name = st.session_state.get("linkedin_display_name", "Your Name")
                    if st.button("👀 LinkedIn Preview", key=f"preview_btn_{index}_{post['day']}", use_container_width=True):
                        show_preview_dialog(post, display_name, expertise or "Professional", media_b64)

                    # LinkedIn Scheduler & Publisher (USP)
                    with st.expander("🔗 LinkedIn Auto-Scheduler & Publisher"):
                        sch_date = st.date_input("Scheduled Publish Date", key=f"li_date_{index}")
                        sch_time = st.time_input("Scheduled Publish Time", key=f"li_time_{index}")
                        
                        col_pub1, col_pub2 = st.columns(2)
                        with col_pub1:
                            if st.button("🚀 Schedule Share", key=f"sch_btn_{index}"):
                                full_text = f"{post['hook']}\n\n{post['post']}\n\n{post['cta']}\n\n{' '.join(post['hashtags'])}"
                                st.session_state["scheduled_posts"].append({
                                    "day": post["day"],
                                    "date": str(sch_date),
                                    "time": str(sch_time),
                                    "text": full_text,
                                    "status": "Scheduled"
                                })
                                st.success(f"Post marked as Scheduled for {sch_date} at {sch_time}!")
                        with col_pub2:
                            if st.button("⚡ Publish Now", key=f"pub_btn_{index}"):
                                token = st.session_state.get("linkedin_token", "").strip()
                                if not token:
                                    st.error("Please configure your LinkedIn Access Token in Settings first.")
                                else:
                                    with st.spinner("Publishing to LinkedIn..."):
                                        full_text = f"{post['hook']}\n\n{post['post']}\n\n{post['cta']}\n\n{' '.join(post['hashtags'])}"
                                        headers = {
                                            "Authorization": f"Bearer {token}",
                                            "Content-Type": "application/json",
                                            "X-Restli-Protocol-Version": "2.0.0"
                                        }
                                        try:
                                            # Fetch URN if not cached
                                            if not st.session_state.get("linkedin_urn"):
                                                me_res = requests.get("https://api.linkedin.com/v2/me", headers=headers, timeout=10)
                                                if me_res.status_code == 200:
                                                    st.session_state["linkedin_urn"] = f"urn:li:person:{me_res.json().get('id')}"
                                                else:
                                                    raise ValueError(f"Could not verify profile URN. HTTP Code {me_res.status_code}.")
                                            
                                            author_urn = st.session_state["linkedin_urn"]
                                            payload = {
                                                "author": author_urn,
                                                "lifecycleState": "PUBLISHED",
                                                "specificContent": {
                                                    "com.linkedin.ugc.ShareContent": {
                                                        "shareCommentary": {
                                                            "text": full_text
                                                        },
                                                        "shareMediaCategory": "NONE"
                                                    }
                                                },
                                                "visibility": {
                                                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                                                }
                                            }
                                            post_res = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload, timeout=10)
                                            if post_res.status_code == 201:
                                                st.success("🎉 Successfully posted directly to your LinkedIn feed!")
                                            else:
                                                st.error(f"Posting failed: {post_res.json().get('message', post_res.text)}")
                                        except Exception as e:
                                            st.error(f"Error publishing: {e}")

                with c2:
                    # RAG Inline Editor Tool (USP)
                    with st.expander("✨ AI Refinement Tool"):
                        refine_instr = st.text_input(
                            "Instructions for the writer",
                            placeholder="e.g. make the hook shorter, translate to French, add a coding analogy...",
                            key=f"instr_{index}",
                        )
                        if st.button("Apply AI Refinement", key=f"apply_{index}"):
                            if refine_instr.strip():
                                with st.spinner("Editing post card..."):
                                    try:
                                        refined = refine_post_with_ai(
                                            client=client,
                                            model=selected_model,
                                            profile=profile_snapshot,
                                            settings=settings,
                                            post=post,
                                            instruction=refine_instr,
                                        )
                                        st.session_state["weekly_plan"]["posts"][index] = refined
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Refinement failed: {e}")

                    # Unicode Formatter Toolbar (USP)
                    with st.expander("🔤 Unicode Spicing Toolkit"):
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.button("Bold Hook", key=f"bold_hook_{index}"):
                                st.session_state["weekly_plan"]["posts"][index]["hook"] = (
                                    to_unicode_bold(post["hook"])
                                )
                                st.rerun()
                            if st.button("Bold CTA", key=f"bold_cta_{index}"):
                                st.session_state["weekly_plan"]["posts"][index]["cta"] = (
                                    to_unicode_bold(post["cta"])
                                )
                                st.rerun()
                        with col_y:
                            if st.button("Italic Hook", key=f"italic_hook_{index}"):
                                st.session_state["weekly_plan"]["posts"][index]["hook"] = (
                                    to_unicode_italic(post["hook"])
                                )
                                st.rerun()
                            if st.button("Italic CTA", key=f"italic_cta_{index}"):
                                st.session_state["weekly_plan"]["posts"][index]["cta"] = (
                                    to_unicode_italic(post["cta"])
                                )
                                st.rerun()
                st.markdown("---")

            with st.expander("Full Plan Markdown Preview"):
                st.code(plan_to_markdown(plan), language="markdown")

            with st.expander("Raw JSON Structure"):
                st.code(json.dumps(plan, indent=2, ensure_ascii=False), language="json")

    # ==================== WEEKLY CALENDAR TAB ====================
    with tab_calendar:
        if plan:
            render_calendar_preview(plan, settings["post_length"])
            
            # (Redundant Interactive Post Inspector removed since every day has its own modal popup)
            pass
        else:
            st.info("Plan not generated yet. Go to Post Studio and compile a plan first.")

        # Show Scheduled Queue
        sch_posts = st.session_state.get("scheduled_posts", [])
        if sch_posts:
            st.markdown("---")
            st.markdown("### ⏰ Scheduled Publishing Queue")
            for sp in sch_posts:
                st.info(f"**{sp['day']}** | Scheduled for: `{sp['date']} {sp['time']}` | Status: **{sp['status']}**")

    # ==================== INSPIRATION LIBRARY TAB ====================
    with tab_library:
        st.subheader("High-Performing Inspiration Posts")
        st.caption(
            "Add copy templates that capture your target writing style. "
            "Our vector database uses these examples to align generated plans with your voice."
        )

        posts = load_inspiration_posts()

        # Add New Post Panel
        with st.expander("➕ Add New Style Reference", expanded=False):
            new_text = st.text_area("Post copy text")
            new_likes = st.number_input("Likes Count", min_value=0, value=100)
            if st.button("Add Post to Database"):
                if new_text.strip():
                    posts.append({"text": new_text.strip(), "likes": new_likes})
                    save_inspiration_posts(posts)
                    st.success("Style reference added successfully! Embeddings cache invalidated.")
                    st.rerun()
                else:
                    st.error("Post text cannot be empty.")

        # Show Existing Posts
        if posts:
            st.markdown("---")
            for idx, p in enumerate(posts):
                col_text, col_actions = st.columns([0.8, 0.2])
                with col_text:
                    st.markdown(
                        f"""
                        <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 8px;">
                            <p style="white-space: pre-wrap; font-size: 0.95em; color: #e2e8f0; margin-bottom: 0;">{p['text']}</p>
                            <span style="font-size: 0.8em; color: #38bdf8; font-weight: bold;">👍 {p.get('likes', 0)} likes</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_actions:
                    # Edit & Delete options
                    if st.button("🗑️ Delete", key=f"del_{idx}"):
                        posts.pop(idx)
                        save_inspiration_posts(posts)
                        st.success("Post deleted! Cache updated.")
                        st.rerun()
        else:
            st.info("No style references loaded. Add posts to populate your custom writing profile.")


if __name__ == "__main__":
    main()
