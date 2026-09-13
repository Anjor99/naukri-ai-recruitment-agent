import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.state import AgentState
from agent.nodes import (
    router_node,
    rag_node,
    status_node,
    field_selector_node,
    response_node,
)
from agent.router import PossibleRoutes


CHECKPOINT_DB = "data/checkpoints.sqlite"


def route_decision(state: AgentState) -> str:
    """Read the route set by router_node and pick the next node."""
    return state["route"]


def build_graph(checkpointer=None, interrupt_before=None):
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("status", status_node)
    graph.add_node("response", response_node)
    graph.add_node("field_selector", field_selector_node)

    # Entry point
    graph.add_edge(START, "router")

    # Conditional branch out of router
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            PossibleRoutes.RAG.value: "rag",
            PossibleRoutes.STATUS.value: "status",
        },
    )

    # Branches
    graph.add_edge("rag", "response")
    graph.add_edge("status", "field_selector")
    graph.add_edge("field_selector", "response")

    # Exit
    graph.add_edge("response", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )


# Persistent SQLite checkpoint store.
_checkpoint_connection = sqlite3.connect(
    CHECKPOINT_DB,
    check_same_thread=False,
)

_checkpointer = SqliteSaver(_checkpoint_connection)

app = build_graph(checkpointer=_checkpointer)