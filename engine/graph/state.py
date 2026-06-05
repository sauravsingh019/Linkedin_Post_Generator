from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict):
    user_profile: Dict[str, Any]
    settings: Dict[str, Any]
    reference_posts: List[Dict[str, Any]]
    auditor_insights: str
    analyst_patterns: str
    weekly_plan: Dict[str, Any]
    error: str
    client: Any
    model: str
