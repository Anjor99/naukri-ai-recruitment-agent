from __future__ import annotations

from enum import Enum
import re

from agent.intent_classifier import (
    IntentClassifier,
    QueryIntent,
)


class PossibleRoutes(Enum):
    """Routes supported by the LangGraph agent."""

    RAG = "rag"
    STATUS = "status"
    UNKNOWN = "unknown"


_RECORD_ID_PATTERN = re.compile(
    r"\bapp-\d{4}\b",
    re.IGNORECASE,
)


# Loaded once when the application starts.
# The SentenceTransformer model is therefore reused across requests.
_classifier = IntentClassifier()


def route_query(
    query: str,
    remembered_record_id: str | None = None,
) -> PossibleRoutes:
    
    # ---------------------------------------------------------
    # 1. Explicit application ID
    # ---------------------------------------------------------

    if _RECORD_ID_PATTERN.search(query):
        return PossibleRoutes.STATUS
    
    # ---------------------------------------------------------
    # 2. Semantic Classification
    # ---------------------------------------------------------
    result = _classifier.classify(
        query=query,
        remembered_record_id=remembered_record_id,
    )

    return PossibleRoutes(result.intent.value)