from __future__ import annotations

import asyncio
import time

from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.reliability import (
    create_retry_policy,
    run_with_graph_timeout,
    GraphTimeoutError,
    RETRY_MAX_ATTEMPTS,
    RETRY_INITIAL_INTERVAL,
    RETRY_MAX_INTERVAL,
    RETRY_JITTER,
)


# ============================================================
# A. RETRY POLICY DEMONSTRATION
# ============================================================

retry_attempts = 0


def simulated_transient_node(state: AgentState) -> dict:
    """
    Simulate a transient failure.

    The first two attempts fail and the third succeeds.
    LangGraph's RetryPolicy handles the retries.
    """

    global retry_attempts

    retry_attempts += 1

    print(f"[RETRY NODE] Attempt {retry_attempts}")

    if retry_attempts < 3:
        print("[RETRY NODE] Simulated transient failure")
        raise RuntimeError("Temporary service failure")

    print("[RETRY NODE] Success")

    return {
        "response": "Transient failure recovered successfully."
    }


def run_retry_demo() -> None:
    global retry_attempts

    retry_attempts = 0

    print("\n" + "=" * 70)
    print("TASK 16 (A): RETRY POLICY")
    print("=" * 70)

    print("Configuration:")
    print(f"  max_attempts     = {RETRY_MAX_ATTEMPTS}")
    print(f"  initial_interval = {RETRY_INITIAL_INTERVAL}s")
    print(f"  max_interval     = {RETRY_MAX_INTERVAL}s")
    print("  backoff_factor   = 2.0")
    print(f"  jitter            = {RETRY_JITTER}")

    graph = StateGraph(AgentState)

    graph.add_node(
        "transient_failure",
        simulated_transient_node,
        retry_policy=create_retry_policy(),
    )

    graph.add_edge(START, "transient_failure")
    graph.add_edge("transient_failure", END)

    app = graph.compile()

    start = time.perf_counter()

    result = app.invoke(
        {
            "query": "retry demonstration",
            "route": "test",
        }
    )

    elapsed = time.perf_counter() - start

    print("\n[RETRY RESULT]")
    print(f"Attempts used: {retry_attempts}")
    print(f"Elapsed time: {elapsed:.3f}s")
    print(f"Response: {result['response']}")

    assert retry_attempts == 3
    assert result["response"] == (
        "Transient failure recovered successfully."
    )

    print(
        "\nPASS: Retry policy recovered after two "
        "transient failures."
    )


# ============================================================
# B. PER-NODE TIMEOUT DEMONSTRATION
# ============================================================

async def simulated_slow_node(state: AgentState) -> dict:
    """
    Simulate an async LangGraph node that takes too long.
    """

    print("[NODE TIMEOUT] Simulated node started")
    print("[NODE TIMEOUT] Simulated operation sleeping for 1.0s")

    await asyncio.sleep(1.0)

    return {
        "response": "This should not be reached."
    }


async def run_node_timeout_demo() -> None:
    print("\n" + "=" * 70)
    print("TASK 16 (B): PER-NODE TIMEOUT")
    print("=" * 70)

    timeout = 0.2

    print(f"Configured node timeout: {timeout}s")
    print("Simulated operation duration: 1.0s")

    graph = StateGraph(AgentState)

    graph.add_node(
        "slow_node",
        simulated_slow_node,
        timeout=timeout,
    )

    graph.add_edge(START, "slow_node")
    graph.add_edge("slow_node", END)

    app = graph.compile()

    start = time.perf_counter()

    try:
        await app.ainvoke(
            {
                "query": "timeout demonstration",
                "route": "test",
            }
        )

        raise AssertionError(
            "Expected NodeTimeoutError was not raised."
        )

    except Exception as exc:
        elapsed = time.perf_counter() - start

        print("\n[NODE TIMEOUT RESULT]")
        print(f"Elapsed time: {elapsed:.3f}s")
        print(f"Error type: {type(exc).__name__}")
        print(f"Error: {exc}")

        assert type(exc).__name__ == "NodeTimeoutError"
        assert elapsed < 1.0

        print(
            "\nPASS: LangGraph per-node timeout fired cleanly "
            "without waiting for the full operation."
        )


# ============================================================
# C. GLOBAL GRAPH TIMEOUT DEMONSTRATION
# ============================================================


async def simulated_slow_graph() -> str:
    """
    Simulate a graph whose total execution exceeds
    the global timeout.
    """

    print("[GLOBAL TIMEOUT] Graph execution started")

    print("[GLOBAL TIMEOUT] Step 1 running...")
    await asyncio.sleep(0.2)

    print("[GLOBAL TIMEOUT] Step 2 running...")
    await asyncio.sleep(0.2)

    print("[GLOBAL TIMEOUT] Step 3 running...")
    await asyncio.sleep(0.2)

    return "Graph completed."


async def run_global_timeout_demo() -> None:
    print("\n" + "=" * 70)
    print("TASK 16 (C): GLOBAL GRAPH TIMEOUT")
    print("=" * 70)

    timeout = 0.5

    print(f"Configured global timeout: {timeout}s")
    print("Simulated total graph duration: ~0.6s")

    start = time.perf_counter()

    try:
        await run_with_graph_timeout(
            simulated_slow_graph,
            timeout=timeout,
        )

        raise AssertionError(
            "Expected GraphTimeoutError was not raised."
        )

    except GraphTimeoutError as exc:
        elapsed = time.perf_counter() - start

        print("\n[GLOBAL TIMEOUT RESULT]")
        print(f"Elapsed time: {elapsed:.3f}s")
        print(f"Error: {exc}")

        assert elapsed < 0.8

        print(
            "\nPASS: Global timeout cancelled "
            "the whole graph run."
        )


# ============================================================
# MAIN
# ============================================================


async def main() -> None:
    run_retry_demo()

    await run_node_timeout_demo()

    await run_global_timeout_demo()

    print("\n" + "=" * 70)
    print("TASK 16 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())