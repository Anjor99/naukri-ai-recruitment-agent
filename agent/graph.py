import asyncio

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.state import AgentState
from agent.reliability import GraphTimeoutError
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

    graph.add_node("router", router_node)

    graph.add_node(
        "rag",
        rag_node,
        timeout=5.0,
    )

    graph.add_node("status", status_node)
    graph.add_node("field_selector", field_selector_node)
    graph.add_node("response", response_node)

    graph.add_edge(START, "router")

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            PossibleRoutes.RAG.value: "rag",
            PossibleRoutes.STATUS.value: "status",
        },
    )

    graph.add_edge("rag", "response")
    graph.add_edge("status", "field_selector")
    graph.add_edge("field_selector", "response")

    graph.add_edge("response", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )


async def invoke_with_timeout(
    input_state: AgentState,
    config: dict,
    timeout: float = 30.0,
):
    """Run the complete graph with a global timeout."""

    try:
        async with AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB) as checkpointer:
            graph_app = build_graph(checkpointer=checkpointer)

            return await asyncio.wait_for(
                graph_app.ainvoke(
                    input_state,
                    config=config,
                ),
                timeout=timeout,
            )

    except asyncio.TimeoutError as exc:
        raise GraphTimeoutError(
            f"Graph exceeded global timeout of {timeout:.2f} seconds."
        ) from exc