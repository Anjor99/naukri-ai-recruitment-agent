from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar, Any

from langgraph.types import RetryPolicy


T = TypeVar("T")


# ============================================================
# RETRY CONFIGURATION
# ============================================================

RETRY_MAX_ATTEMPTS = 3
RETRY_INITIAL_INTERVAL = 0.1
RETRY_MAX_INTERVAL = 0.4
RETRY_BACKOFF_FACTOR = 2.0
RETRY_JITTER = True


def create_retry_policy() -> RetryPolicy:
    """Create the standard retry policy for transient failures."""

    return RetryPolicy(
        initial_interval=RETRY_INITIAL_INTERVAL,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        max_interval=RETRY_MAX_INTERVAL,
        max_attempts=RETRY_MAX_ATTEMPTS,
        jitter=RETRY_JITTER,
        retry_on=RuntimeError,
    )


# ============================================================
# TIMEOUT CONFIGURATION
# ============================================================

DEFAULT_NODE_TIMEOUT = 5.0
DEFAULT_GRAPH_TIMEOUT = 30.0


class GraphTimeoutError(TimeoutError):
    """Raised when the complete graph exceeds its global timeout."""


async def run_with_graph_timeout(
    operation: Callable[[], Awaitable[T]],
    timeout: float = DEFAULT_GRAPH_TIMEOUT,
) -> T:
    """
    Execute the complete graph with a global timeout.

    The timeout applies to the entire graph execution.
    """

    try:
        return await asyncio.wait_for(
            operation(),
            timeout=timeout,
        )
    except asyncio.TimeoutError as exc:
        raise GraphTimeoutError(
            f"Graph exceeded global timeout of {timeout:.2f} seconds."
        ) from exc