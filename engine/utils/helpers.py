import base64
import html
import json
from pathlib import Path
import streamlit as st


def render_linkedin_feed_preview(post: dict, name: str, headline: str, media_b64: str = "") -> None:
    """Renders a beautiful, high-fidelity mock-up of a LinkedIn Feed Share card."""
    initials = "LP"  # LinkedIn Preview
    
    media_html = ""
    if media_b64:
        media_html = f"""
        <div style="margin-top: 12px; border-radius: 8px; overflow: hidden; border: 1px solid #2f353a; background-color: #0d1117; display: flex; justify-content: center; align-items: center; max-height: 240px;">
            <img src="{media_b64}" style="max-width: 100%; max-height: 240px; object-fit: contain; display: block;" />
        </div>
        """
        
    compiled_body = f"{post.get('hook', '')}\n\n{post.get('post', '')}\n\n{post.get('cta', '')}\n\n{' '.join(post.get('hashtags', []))}"
    
    html_code = f"""<style>
.hide-scrollbar::-webkit-scrollbar {{
    display: none !important;
}}
.hide-scrollbar {{
    -ms-overflow-style: none !important;
    scrollbar-width: none !important;
}}
</style>
<div class="hide-scrollbar" style="background-color: #1d2226; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); padding: 22px; font-family: -apple-system, system-ui, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 650px; max-height: 550px; overflow-y: auto; margin: 10px auto; box-shadow: 0 20px 40px rgba(0,0,0,0.5), 0 0 20px rgba(99, 102, 241, 0.15); transform: perspective(1000px) rotateX(1deg); transition: transform 0.3s ease, box-shadow 0.3s ease;" onmouseover="this.style.transform='perspective(1000px) rotateX(0deg) translateY(-2px)';" onmouseout="this.style.transform='perspective(1000px) rotateX(1deg)';">
  <!-- Profile Header -->
  <div style="display: flex; align-items: center; margin-bottom: 12px;">
    <div style="width: 48px; height: 48px; border-radius: 50%; background-color: #0077b5; color: #ffffff; font-weight: bold; display: flex; align-items: center; justify-content: center; font-size: 1.1em; margin-right: 12px; border: 2px solid rgba(255,255,255,0.1);">
      {initials}
    </div>
    <div>
      <div style="font-weight: 600; color: #ffffff; font-size: 0.95em;">LinkedIn Preview</div>
      <div style="font-size: 0.8em; color: #94a3b8; line-height: 1.3;">{headline} • 1st</div>
      <div style="font-size: 0.75em; color: #64748b; display: flex; align-items: center; margin-top: 2px;">
        Now • 🌐
      </div>
    </div>
  </div>
  <!-- Feed Copy -->
  <div style="color: #e2e8f0; font-size: 0.92em; line-height: 1.5; white-space: pre-wrap; margin-bottom: 12px;">{compiled_body}</div>
  <!-- Uploaded/Generated Media -->
  {media_html}
  <!-- Feed Actions -->
  <hr style="border: 0; border-top: 1px solid #2f353a; margin: 12px 0 8px 0;">
  <div style="display: flex; justify-content: space-around; color: #94a3b8; font-size: 0.85em; font-weight: 600;">
    <span style="cursor: pointer;">👍 Like</span>
    <span style="cursor: pointer;">💬 Comment</span>
    <span style="cursor: pointer;">🔁 Repost</span>
    <span style="cursor: pointer;">✉️ Send</span>
  </div>
</div>"""
    st.markdown(html_code, unsafe_allow_html=True)


if hasattr(st, "dialog"):
    @st.dialog("LinkedIn Preview", width="large")
    def show_preview_dialog(post: dict, name: str, headline: str, media_b64: str = ""):
        render_linkedin_feed_preview(post, name, headline, media_b64)
else:
    def show_preview_dialog(post: dict, name: str, headline: str, media_b64: str = ""):
        st.warning("Your Streamlit version doesn't support popups natively. Showing preview inline:")
        render_linkedin_feed_preview(post, name, headline, media_b64)



def count_words(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def target_word_range(target: int) -> tuple[int, int]:
    tolerance = max(20, int(target * 0.15))
    return max(40, target - tolerance), target + tolerance


def to_unicode_bold(text: str) -> str:
    """Converts standard ASCII characters to mathematical sans-serif bold characters for LinkedIn formatting."""
    result = []
    for char in text:
        if "A" <= char <= "Z":
            result.append(chr(ord(char) - ord("A") + 0x1D5D4))
        elif "a" <= char <= "z":
            result.append(chr(ord(char) - ord("a") + 0x1D5EE))
        elif "0" <= char <= "9":
            result.append(chr(ord(char) - ord("0") + 0x1D7EC))
        else:
            result.append(char)
    return "".join(result)


def to_unicode_italic(text: str) -> str:
    """Converts standard ASCII characters to mathematical sans-serif italic characters for LinkedIn formatting."""
    result = []
    for char in text:
        if "A" <= char <= "Z":
            result.append(chr(ord(char) - ord("A") + 0x1D608))
        elif "a" <= char <= "z":
            result.append(chr(ord(char) - ord("a") + 0x1D622))
        else:
            result.append(char)
    return "".join(result)


def render_copy_button(text: str, button_key: str):
    """Renders a secure, visual HTML/JS button to copy text directly to the clipboard."""
    escaped_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )
    html_code = f"""
    <button id="copy-btn-{button_key}" onclick="copyText()" style="
        background: linear-gradient(135deg, #0077b5 0%, #00a0dc 100%);
        color: white;
        border: none;
        padding: 10px 18px;
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 700;
        width: 100%;
        box-shadow: 0 4px 0px #005a87, 0 8px 15px rgba(0, 119, 181, 0.25);
        transition: all 0.15s ease;
        transform: translateY(0);
    " onmousedown="this.style.transform='translateY(2px)'; this.style.boxShadow='0 1px 0px #005a87, 0 4px 6px rgba(0, 119, 181, 0.15)';" onmouseup="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 0px #005a87, 0 12px 20px rgba(0, 119, 181, 0.4)';" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 0px #005a87, 0 12px 20px rgba(0, 119, 181, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 0px #005a87, 0 8px 15px rgba(0, 119, 181, 0.25)';">
        📋 Copy to Clipboard
    </button>
    <script>
    function copyText() {{
        const text = `{escaped_text}`;
        navigator.clipboard.writeText(text).then(() => {{
            const btn = document.getElementById('copy-btn-{button_key}');
            btn.innerHTML = '✓ Copied to Clipboard!';
            btn.style.background = 'linear-gradient(135deg, #2ea44f 0%, #34d058 100%)';
            btn.style.boxShadow = '0 4px 0px #227a3b, 0 8px 15px rgba(46, 164, 79, 0.25)';
            setTimeout(() => {{
                btn.innerHTML = '📋 Copy to Clipboard';
                btn.style.background = 'linear-gradient(135deg, #0077b5 0%, #00a0dc 100%)';
                btn.style.boxShadow = '0 4px 0px #005a87, 0 8px 15px rgba(0, 119, 181, 0.25)';
            }}, 2000);
        }}).catch(err => {{
            console.error('Failed to copy: ', err);
        }});
    }}
    </script>
    """
    st.components.v1.html(html_code, height=50)


def render_overview_metrics(plan: dict):
    post_count = len(plan.get("posts", []))
    hashtag_count = sum(len(post.get("hashtags", [])) for post in plan.get("posts", []))
    avg_hashtags = round(hashtag_count / post_count, 1) if post_count else 0

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Weekly Posts Scheduled", post_count)
    metric_2.metric("Average Hashtags", avg_hashtags)
    metric_3.metric("Generation Status", "Draft Ready")

    if plan.get("summary"):
        st.info(f"**Strategy Focus:** {plan['summary']}")


def render_post_card(post: dict, target_words: int = None):
    full_compiled_text = (
        f"{post.get('hook', '')}\n\n"
        f"{post.get('post', '')}\n\n"
        f"{post.get('cta', '')}\n\n"
        f"{' '.join(post.get('hashtags', []))}"
    )

    char_count = len(full_compiled_text)
    word_count = count_words(post.get("post", ""))

    # Progress color calculation
    if char_count < 2500:
        bar_color = "green"
    elif char_count <= 3000:
        bar_color = "orange"
    else:
        bar_color = "red"

    st.markdown(f"### {post['day']}")
    st.caption(f"🎯 **Angle:** {post.get('angle', 'Dynamic value')}")

    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Characters", f"{char_count} / 3,000")
    with col2:
        st.metric("Body Word Count", word_count)
    with col3:
        status = "🟢 Safe" if char_count <= 3000 else "🔴 Over Limit"
        st.metric("LinkedIn Status", status)

    # Character progress bar
    progress_val = min(1.0, char_count / 3000.0)
    st.progress(progress_val)
    if char_count > 3000:
        st.warning("⚠️ This post exceeds the LinkedIn 3,000-character limit and may be truncated.")

    # Post content rendering
    st.markdown(
        f"""
        <div class="startup-post-card">
            <p class="startup-post-hook">{post.get('hook', '')}</p>
            <p class="startup-post-body">{post.get('post', '')}</p>
            <p class="startup-post-cta">{post.get('cta', '')}</p>
            <p class="startup-post-tags">{" ".join(post.get('hashtags', []))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_calendar_preview(plan: dict, target_words: int):
    st.markdown("### 📅 Weekly Content Grid")
    posts = plan.get("posts", [])
    if not posts:
        return

    cols = st.columns(len(posts))
    for col, post in zip(cols, posts):
        with col:
            st.markdown(
                f"""
                <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #334155;">
                    <strong style="color: #38bdf8; font-size: 1.1em;">{post['day']}</strong>
                    <div style="font-size: 0.85em; color: #94a3b8; margin: 4px 0;">{post.get('angle', '')[:20]}...</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            full_txt = f"{post.get('hook', '')}\n\n{post.get('post', '')}\n\n{post.get('cta', '')}\n\n{' '.join(post.get('hashtags', []))}"
            chars = len(full_txt)
            status = "🟢 Safe" if chars <= 3000 else "🔴 Over"
            st.caption(f"{chars} chars | {status}")
            
            # Retrieve display name, headline and media
            display_name = st.session_state.get("linkedin_display_name", "Your Name")
            headline = st.session_state.get("form_expertise", "") or "Professional"
            
            # Compute local image path relative to root
            local_path = Path(__file__).resolve().parent.parent.parent / "data" / f"{post['day'].lower()}_post_image.png"
            media_b64 = ""
            if local_path.exists():
                try:
                    with open(local_path, "rb") as img_f:
                        media_b64 = f"data:image/png;base64,{base64.b64encode(img_f.read()).decode('utf-8')}"
                except Exception:
                    pass
            
            if st.button("👀 LinkedIn Preview", key=f"cal_prev_{post['day']}", use_container_width=True):
                show_preview_dialog(post, display_name, headline, media_b64)


def render_live_preview(profile: dict, settings: dict):
    st.subheader("Strategy Blueprint Preview")
    minimum, maximum = target_word_range(settings["post_length"])

    st.markdown(
        f"""
        **Target Constraints:**
        - **Frequency:** {settings['posts_per_week']} posts/week
        - **Post Length:** {minimum}-{maximum} words ({settings['post_length']} target)
        - **Styling:** {settings['hashtag_count']} hashtags | Emoji level {settings['emoji_level']}/5
        """
    )

    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #0f172a; padding: 15px; border-radius: 10px; border: 1px solid #1e293b;">
                <strong>👤 Profile Context</strong>
                <ul style="margin-top: 8px; margin-bottom: 0;">
                    <li><b>Expertise:</b> {profile['expertise'] or '<i>Not defined</i>'}</li>
                    <li><b>Audience:</b> {profile['audience'] or '<i>Not defined</i>'}</li>
                    <li><b>Tone:</b> {profile['tone']}</li>
                    <li><b>Goal:</b> {profile['goal'] or '<i>Not defined</i>'}</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


def plan_to_markdown(plan: dict) -> str:
    blocks = [f"# Weekly LinkedIn Plan\n\n{plan.get('summary', '').strip()}\n"]
    for post in plan.get("posts", []):
        hashtags = " ".join(post.get("hashtags", []))
        blocks.append(
            "\n".join(
                [
                    f"## {post['day']}",
                    f"*Angle: {post.get('angle', '')}*",
                    "",
                    f"**{post.get('hook', '')}**",
                    "",
                    post.get("post", ""),
                    "",
                    f"*{post.get('cta', '')}*",
                    "",
                    hashtags,
                ]
            )
        )
    return "\n\n".join(blocks).strip()


def build_download_bundle(plan: dict) -> tuple[str, str]:
    return plan_to_markdown(plan), json.dumps(plan, indent=2, ensure_ascii=False)
