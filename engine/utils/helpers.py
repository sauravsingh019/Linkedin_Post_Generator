import json

import streamlit as st


def count_words(text):
    return len([word for word in text.split() if word.strip()])


def target_word_range(target):
    tolerance = max(20, int(target * 0.15))
    return max(40, target - tolerance), target + tolerance


def render_overview_metrics(plan):
    post_count = len(plan["posts"])
    hashtag_count = sum(len(post.get("hashtags", [])) for post in plan["posts"])
    avg_hashtags = round(hashtag_count / post_count, 1) if post_count else 0

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Posts", post_count)
    metric_2.metric("Avg hashtags", avg_hashtags)
    metric_3.metric("Summary", "Ready")

    if plan.get("summary"):
        st.caption(plan["summary"])


def render_post_card(post, target_words=None):
    with st.container():
        st.markdown(f"### {post['day']}")
        st.caption(post.get("angle", ""))

        meta = []
        if target_words:
            words = count_words(post.get("post", ""))
            minimum, maximum = target_word_range(target_words)
            status = "Within range" if minimum <= words <= maximum else "Out of range"
            meta.append(f"{words} words")
            meta.append(status)
        if meta:
            st.caption(" | ".join(meta))

        if post.get("hook"):
            st.markdown(f"**Hook**  \n{post['hook']}")

        st.markdown(post["post"])

        if post.get("cta"):
            st.markdown(f"**CTA**  \n{post['cta']}")

        hashtags = " ".join(post.get("hashtags", []))
        if hashtags:
            st.code(hashtags, language="text")

        st.divider()


def render_calendar_preview(plan, target_words):
    st.subheader("Calendar preview")
    columns = st.columns(len(plan["posts"])) if plan.get("posts") else []
    minimum, maximum = target_word_range(target_words)

    for column, post in zip(columns, plan["posts"]):
        with column:
            st.markdown(f"**{post['day']}**")
            st.caption(post.get("angle", ""))
            preview = post.get("hook") or post.get("post", "")
            st.write(preview[:140] + ("..." if len(preview) > 140 else ""))
            words = count_words(post.get("post", ""))
            status = "OK" if minimum <= words <= maximum else "Check"
            st.caption(f"{words} words | {status}")


def render_live_preview(profile, settings):
    st.subheader("Live preview")
    minimum, maximum = target_word_range(settings["post_length"])
    requested_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][: settings["posts_per_week"]]

    st.caption(
        f"Target: {settings['posts_per_week']} posts | {minimum}-{maximum} words each | "
        f"{settings['hashtag_count']} hashtags | Emoji level {settings['emoji_level']}/5"
    )

    with st.container():
        st.markdown("**Strategy snapshot**")
        st.markdown(f"- **Niche:** {profile['expertise'] or 'Your niche will appear here'}")
        st.markdown(f"- **Audience:** {profile['audience'] or 'Your target audience will appear here'}")
        st.markdown(f"- **Tone:** {profile['tone']}")
        st.markdown(f"- **Goal:** {profile['goal'] or 'Your content goal will appear here'}")

        themes = profile["themes"] or ["Your weekly themes will appear here"]
        st.markdown("**Themes**")
        for theme in themes[:5]:
            st.markdown(f"- {theme}")

    st.markdown("**Planned publishing days**")
    st.code(" | ".join(requested_days), language="text")


def plan_to_markdown(plan):
    blocks = [f"# Weekly LinkedIn Plan\n\n{plan.get('summary', '').strip()}\n"]
    for post in plan["posts"]:
        hashtags = " ".join(post.get("hashtags", []))
        blocks.append(
            "\n".join(
                [
                    f"## {post['day']}",
                    f"Angle: {post.get('angle', '')}",
                    f"Hook: {post.get('hook', '')}",
                    "",
                    post["post"],
                    "",
                    f"CTA: {post.get('cta', '')}",
                    hashtags,
                ]
            )
        )
    return "\n\n".join(blocks).strip()


def build_download_bundle(plan):
    return plan_to_markdown(plan), json.dumps(plan, indent=2, ensure_ascii=False)
