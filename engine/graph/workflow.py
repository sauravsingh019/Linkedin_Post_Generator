from engine.agents.analyst_agent import analyst_agent
from engine.agents.auditor_agent import auditor_agent
from engine.agents.creator_agent import creator_agent
from engine.graph.state import AgentState

try:
    from langgraph.graph import END, StateGraph

    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    END = "END"


class FallbackStateGraph:
    """A lightweight, zero-dependency state machine that behaves like LangGraph's StateGraph.

    Ensures the application works out-of-the-box in environments where pip dependencies
    are not fully installed yet.
    """

    def __init__(self, state_schema):
        self.nodes = {}
        self.edges = []
        self.entry_point = None

    def add_node(self, name, func):
        self.nodes[name] = func

    def add_edge(self, source, target):
        self.edges.append((source, target))

    def set_entry_point(self, name):
        self.entry_point = name

    def compile(self):
        return CompiledFallbackGraph(self)


class CompiledFallbackGraph:

    def __init__(self, graph):
        self.graph = graph

    def invoke(self, state: dict) -> dict:
        current = self.graph.entry_point
        visited = set()

        while current and current != END:
            if current in visited:
                break
            visited.add(current)

            node_func = self.graph.nodes.get(current)
            if node_func:
                state = node_func(state)

            # Resolve next state transition based on registered edges
            next_node = None
            for src, tgt in self.graph.edges:
                if src == current:
                    next_node = tgt
                    break
            current = next_node

        return state


def build_workflow():
    """Builds and compiles the Auditor -> Analyst -> Creator pipeline."""
    if HAS_LANGGRAPH:
        graph = StateGraph(AgentState)
    else:
        graph = FallbackStateGraph(AgentState)

    graph.add_node("auditor", auditor_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("creator", creator_agent)

    graph.set_entry_point("auditor")
    graph.add_edge("auditor", "analyst")
    graph.add_edge("analyst", "creator")
    graph.add_edge("creator", END)

    return graph.compile()
