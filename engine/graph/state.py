from typing import TypedDict, List, Dict

class AgentState(TypedDict):
    user_profile: Dict
    patterns: List[str]
    insights: str
    weekly_posts: List[str]
    emoji_level: int
    post_length: int
    include_question: bool
    hashtag_count: int
