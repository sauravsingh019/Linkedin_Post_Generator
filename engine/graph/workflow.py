from langgraph.graph import StateGraph, END
from engine.graph.state import AgentState
from engine.agents.auditor_agent import auditor_agent
from engine.agents.analyst_agent import analyst_agent
from engine.agents.creator_agent import creator_agent

def build_workflow():
    graph = StateGraph(AgentState)

    graph.add_node("auditor", auditor_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("creator", creator_agent)

    graph.set_entry_point("auditor")
    graph.add_edge("auditor", "analyst")
    graph.add_edge("analyst", "creator")
    graph.add_edge("creator", END)   # 🔥 THIS WAS MISSING

    return graph.compile()
