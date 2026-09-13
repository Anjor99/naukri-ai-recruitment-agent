"""
End-to-end demonstration of the Naukri AI Support Agent.

Run:

    python scripts/demo.py

The demo covers:
1. Dataset
2. RAG
3. Application-status lookup
4. Conversational memory
5. PII / prompt-injection guardrails
6. Out-of-scope fallback
7. Structured output validation
8. MCP tool
9. Reliability configuration

The demo does not start FastAPI or MCP servers.
Use `python run.py` for the services.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


# Allow execution as:
#     python scripts/demo.py
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def demo_dataset() -> None:
    header("1. DATASET")

    from dataset import JOB_APPLICATIONS

    print(f"Total applications: {len(JOB_APPLICATIONS)}")

    categories = {}

    for record in JOB_APPLICATIONS:
        category = record["category"]
        categories[category] = categories.get(category, 0) + 1

    print("\nCategories:")
    for category, count in categories.items():
        print(f"  {category}: {count}")

    statuses = {}

    for record in JOB_APPLICATIONS:
        status = record["status"]
        statuses[status] = statuses.get(status, 0) + 1

    print("\nStatuses:")
    for status, count in statuses.items():
        print(f"  {status}: {count}")


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------

def demo_rag() -> None:
    header("2. RAG — POLICY QUESTION")

    from rag.embeddings import EmbeddingModel
    from rag.generator import GroundedGenerator
    from rag.vector_store import VectorStore

    query = "What is the interview scheduling process?"

    vector_store = VectorStore(EmbeddingModel())
    collection = vector_store.create_collection(
        "fixed_size_collection"
    )

    generator = GroundedGenerator(vector_store)

    result = generator.generate(
        query=query,
        collection=collection,
        top_k=5,
    )

    print(f"Query: {query}")
    print()
    print("Answer:")
    print(result)


def demo_oos() -> None:
    header("3. RAG — OUT-OF-SCOPE FALLBACK")

    from rag.embeddings import EmbeddingModel
    from rag.generator import GroundedGenerator
    from rag.vector_store import VectorStore

    query = "How do I bake a chocolate cake?"

    vector_store = VectorStore(EmbeddingModel())
    collection = vector_store.create_collection(
        "fixed_size_collection"
    )

    generator = GroundedGenerator(vector_store)

    result = generator.generate(
        query=query,
        collection=collection,
        top_k=5,
    )

    print(f"Query: {query}")
    print()
    print("Result:")
    print(result)


# ---------------------------------------------------------------------------
# Application status
# ---------------------------------------------------------------------------

async def demo_status() -> None:
    header("4. APPLICATION STATUS TOOL")

    from agent.conversation import run_turn

    record_id = "APP-0001"

    query = f"What is the status of application {record_id}?"

    result = await run_turn(
        query,
        conversation_id="demo-status",
    )

    print(f"Query: {query}")
    print()
    print("Agent response:")
    print(result["response"])

    print()
    print(f"Route selected: {result.get('route')}")
    print(f"Record ID: {result.get('record_id')}")


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

async def demo_memory() -> None:
    header("5. CONVERSATIONAL MEMORY")

    from agent.conversation import run_turn

    conversation_id = "demo-memory"

    first_query = "What is the status of APP-0001?"

    first = await run_turn(
        first_query,
        conversation_id=conversation_id,
    )

    print("Turn 1:")
    print(f"  User: {first_query}")
    print(f"  Agent: {first['response']}")

    second_query = "What is its expected salary?"

    second = await run_turn(
        second_query,
        conversation_id=conversation_id,
    )

    print()
    print("Turn 2:")
    print(f"  User: {second_query}")
    print(f"  Agent: {second['response']}")

    print()
    print(f"Conversation ID: {conversation_id}")
    print(
        "Remembered record ID:",
        second.get("record_id"),
    )


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

def demo_guardrails() -> None:
    header("6. GUARDRAILS")

    try:
        from tests.test_guardrails import main as guardrail_test

        guardrail_test()

    except Exception as exc:
        print(
            "[WARNING] Guardrail demonstration could not be "
            f"completed: {exc}"
        )


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------

async def demo_schema() -> None:
    header("7. STRUCTURED OUTPUT VALIDATION")

    from agent.conversation import run_turn

    result = await run_turn(
        "What is the notice period policy?",
        conversation_id="demo-schema",
    )

    print("Response generated successfully.")

    print()
    print("State keys:")
    for key in sorted(result.keys()):
        print(f"  - {key}")

    print()
    print("Response:")
    print(result["response"])

    # If the project exposes a schema validator, use it.
    try:
        from agent.schema import validate_agent_response

        validate_agent_response(result)
        print()
        print("[PASS] Structured response validation succeeded.")

    except ImportError:
        print()
        print(
            "[INFO] Schema validator module was not found; "
            "skipping explicit validator call."
        )


# ---------------------------------------------------------------------------
# MCP
# ---------------------------------------------------------------------------

def demo_mcp() -> None:
    header("8. MCP TOOL")

    print(
        "MCP is demonstrated by the separate mcp_client.py process."
    )
    print()
    print("Start services with:")
    print("  python run.py")
    print()
    print("Then run:")
    print("  python mcp_client.py")


# ---------------------------------------------------------------------------
# Reliability
# ---------------------------------------------------------------------------

def demo_reliability() -> None:
    header("9. RELIABILITY CONFIGURATION")

    from agent.reliability import (
        DEFAULT_GRAPH_TIMEOUT,
        DEFAULT_NODE_TIMEOUT,
        RETRY_BACKOFF_FACTOR,
        RETRY_INITIAL_INTERVAL,
        RETRY_JITTER,
        RETRY_MAX_ATTEMPTS,
        RETRY_MAX_INTERVAL,
    )

    print(f"Per-node timeout:      {DEFAULT_NODE_TIMEOUT}s")
    print(f"Global graph timeout:  {DEFAULT_GRAPH_TIMEOUT}s")
    print()
    print("Retry policy:")
    print(f"  max attempts:        {RETRY_MAX_ATTEMPTS}")
    print(f"  initial interval:    {RETRY_INITIAL_INTERVAL}s")
    print(f"  max interval:        {RETRY_MAX_INTERVAL}s")
    print(f"  backoff factor:      {RETRY_BACKOFF_FACTOR}")
    print(f"  jitter:               {RETRY_JITTER}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=" * 72)
    print("NAUKRI AI SUPPORT AGENT — END-TO-END DEMO")
    print("=" * 72)

    demo_dataset()

    demo_rag()

    demo_oos()

    await demo_status()

    await demo_memory()

    demo_guardrails()

    await demo_schema()

    demo_mcp()

    demo_reliability()

    header("DEMO COMPLETE")

    print("Core agent demonstrations completed.")
    print()
    print("For the live services:")
    print("  python run.py")
    print()
    print("FastAPI Swagger:")
    print("  http://127.0.0.1:8000/docs")
    print()
    print("MCP:")
    print("  http://127.0.0.1:8001/mcp")


if __name__ == "__main__":
    asyncio.run(main())