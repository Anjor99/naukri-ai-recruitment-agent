from agent.graph import (
    build_graph,
)
from agent.nodes import (
    router_node,
    status_node,
    field_selector_node,
    response_node,
    rag_node,
)


THREAD_ID = "task15-demo-001"

CONFIG = {
    "configurable": {
        "thread_id": THREAD_ID,
    }
}


def traced_node(name, node_function):
    """Wrap a node to make execution visible in the demo."""

    def wrapper(state):
        print(f"[EXECUTE] {name}")
        result = node_function(state)
        print(f"[COMPLETE] {name}")
        return result

    return wrapper


def build_demo_graph():
    """
    Build the same application graph with execution tracing
    and an interrupt before field_selector.
    """

    from langgraph.graph import StateGraph, START, END
    from agent.state import AgentState
    from agent.router import PossibleRoutes

    graph = StateGraph(AgentState)

    graph.add_node(
        "router",
        traced_node("router", router_node),
    )
    graph.add_node(
        "rag",
        traced_node("rag", rag_node),
    )
    graph.add_node(
        "status",
        traced_node("status", status_node),
    )
    graph.add_node(
        "field_selector",
        traced_node("field_selector", field_selector_node),
    )
    graph.add_node(
        "response",
        traced_node("response", response_node),
    )

    graph.add_edge(START, "router")

    graph.add_conditional_edges(
        "router",
        lambda state: state["route"],
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
        checkpointer=__import__(
            "agent.graph",
            fromlist=["_checkpointer"],
        )._checkpointer,
        interrupt_before=["field_selector"],
    )


def main():
    print("=" * 70)
    print("TASK 15: SQLITE CHECKPOINTING")
    print("=" * 70)
    print(f"Thread ID: {THREAD_ID}")

    app = build_demo_graph()

    input_state = {
        "query": "What is the status of APP-0001?",
        "conversation_id": THREAD_ID,
        "history": {},
        "record_id": "APP-0001",
    }

    # ---------------------------------------------------------
    # FIRST RUN
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("FIRST RUN")
    print("=" * 70)

    first_state = app.invoke(
        input_state,
        config=CONFIG,
    )

    print("\n[INTERRUPTED]")
    print("Execution stopped before: field_selector")

    # ---------------------------------------------------------
    # CHECKPOINT
    # ---------------------------------------------------------
    checkpoint_state = app.get_state(CONFIG)

    print("\n" + "=" * 70)
    print("CHECKPOINT STATE")
    print("=" * 70)

    print(f"Route: {checkpoint_state.values.get('route')}")
    print(f"Record ID: {checkpoint_state.values.get('record_id')}")
    print(f"Status result: {checkpoint_state.values.get('status_result')}")
    print(f"Next node(s): {checkpoint_state.next}")

    # ---------------------------------------------------------
    # RESUME
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("RESUMING SAME THREAD")
    print("=" * 70)

    print(
        "[CHECKPOINT] Loading saved state "
        f"for thread: {THREAD_ID}"
    )

    final_state = app.invoke(
        None,
        config=CONFIG,
    )

    print("\n" + "=" * 70)
    print("FINAL RUN COMPLETE")
    print("=" * 70)

    print(f"Final response: {final_state.get('response')}")
    print(f"Route: {final_state.get('route')}")
    print(f"Record ID: {final_state.get('record_id')}")

    print("\nCheckpoint demonstration:")
    print("- router executed during FIRST RUN")
    print("- status executed during FIRST RUN")
    print("- execution interrupted before field_selector")
    print("- same thread ID used for RESUME")
    print("- router was NOT executed again")
    print("- status was NOT executed again")
    print("- field_selector executed during RESUME")
    print("- response executed during RESUME")


if __name__ == "__main__":
    main()