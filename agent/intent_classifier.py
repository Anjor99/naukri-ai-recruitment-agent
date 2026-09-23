from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from rag.embeddings import EmbeddingModel


class QueryIntent(Enum):
    """High-level semantic intent of a user query."""

    STATUS = "status"
    RAG = "rag"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IntentClassification:
    """Semantic classification result."""

    intent: QueryIntent
    confidence: float
    margin: float
    status_similarity: float
    rag_similarity: float


# Queries representing requests about a specific application record.
STATUS_EXAMPLES = (
    "What is the status of my application?",
    "Tell me about my application.",
    "What is happening with my application?",
    "What is the current state of my application?",
    "What is the progress of my application?",
    "How long has my application been pending?",
    "How many days since my application was created?",
    "How old is my application?",
    "What salary did I enter for my application?",
    "What is the expected salary in my application?",
    "Is my application flagged for review?",
    "Has my application been flagged?",
    "Should my application be escalated?",
    "Does my application need escalation?",
    "Give me the details of my application.",
    "Give me all available information about my application.",
    "What information do you have about my application?",
    "Tell me everything about my application.",
    "What is the applicant name?",
    "What is the applicant's information?",
    "Give me all the details",
    "Give me all the details of my application",
    "Give me all the details for my application",
    "Give me all the application details",
    "Give me all the application details for my application",
    "Show me all the details",
    "Show me all my application details",
    "Tell me everything about my application",
    "Give me everything about my application",
    "Show me everything about my application",
)


# Queries representing general recruitment / HR knowledge.
RAG_EXAMPLES = (
    "What is the interview process?",
    "How does interview scheduling work?",
    "What is the background verification process?",
    "How does background verification work?",
    "What is the notice period policy?",
    "What is the remote work policy?",
    "What are the eligibility requirements?",
    "Who is eligible to apply?",
    "How does the referral bonus work?",
    "What is the referral bonus policy?",
    "What is the probation period?",
    "How does offer negotiation work?",
    "What are the offer negotiation rules?",
    "What are the diversity hiring guidelines?",
    "How does the hiring process work?",
    "What are the stages of recruitment?",
    "How do I apply for a job?",
    "What is the policy for applicant data retention?",
    "How long is applicant data retained?",
)


class IntentClassifier:
    """
    Semantic classifier for high-level agent routing.

    STATUS:
        The user is asking about a particular application record,
        including fields that may or may not exist in the dataset.

    RAG:
        The user is asking about general HR/recruitment knowledge.

    UNKNOWN:
        The semantic evidence is too weak or ambiguous to confidently
        classify the query.
    """

    DEFAULT_MIN_CONFIDENCE = 0.50
    DEFAULT_MIN_MARGIN = 0.05

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        min_margin: float = DEFAULT_MIN_MARGIN,
    ) -> None:
        self.embedding_model = embedding_model or EmbeddingModel()

        self.min_confidence = min_confidence
        self.min_margin = min_margin

        # Embed prototypes once during initialization.
        self._status_embeddings = self._normalize(
            self.embedding_model.embed_texts(
                list(STATUS_EXAMPLES)
            )
        )

        self._rag_embeddings = self._normalize(
            self.embedding_model.embed_texts(
                list(RAG_EXAMPLES)
            )
        )

    @staticmethod
    def _normalize(embeddings: np.ndarray) -> np.ndarray:
        """
        L2-normalize embeddings so dot product gives cosine similarity.
        """
        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        norms = np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True,
        )

        return embeddings / np.maximum(norms, 1e-12)

    def _similarity_to_prototypes(
        self,
        query_embedding: np.ndarray,
        prototypes: np.ndarray,
    ) -> float:
        """
        Return the strongest cosine similarity between the query
        and any prototype in an intent group.
        """
        similarities = query_embedding @ prototypes.T

        return float(np.max(similarities))

    def classify(
        self,
        query: str,
        remembered_record_id: str | None = None,
    ) -> IntentClassification:
        """
        Classify a query using semantic similarity.

        remembered_record_id provides conversational context for
        follow-up questions about an already identified application.
        """

        query = query.strip()

        if not query:
            return IntentClassification(
                intent=QueryIntent.UNKNOWN,
                confidence=0.0,
                margin=0.0,
                status_similarity=0.0,
                rag_similarity=0.0,
            )

        # Embed only the current query.
        query_embedding = self.embedding_model.embed_text(query)

        query_embedding = self._normalize(query_embedding)[0]

        status_similarity = self._similarity_to_prototypes(
            query_embedding,
            self._status_embeddings,
        )

        rag_similarity = self._similarity_to_prototypes(
            query_embedding,
            self._rag_embeddings,
        )

        confidence = max(
            status_similarity,
            rag_similarity,
        )

        margin = abs(
            status_similarity - rag_similarity
        )

        # ---------------------------------------------------------
        # Confidence check
        # ---------------------------------------------------------
        if confidence < self.min_confidence:
            intent = QueryIntent.UNKNOWN

        # ---------------------------------------------------------
        # Ambiguity check
        # ---------------------------------------------------------
        elif margin < self.min_margin:
            intent = QueryIntent.UNKNOWN

        # ---------------------------------------------------------
        # Normal semantic classification
        # ---------------------------------------------------------
        elif status_similarity > rag_similarity:
            intent = QueryIntent.STATUS

        else:
            intent = QueryIntent.RAG

        # ---------------------------------------------------------
        # Conversational context
        # ---------------------------------------------------------
        #
        # If an application is already remembered and the query
        # semantically resembles an application-specific question,
        # STATUS gets additional contextual support.
        #
        # We deliberately do NOT let remembered_record_id override
        # a clearly general RAG query.
        #
        if (
            remembered_record_id
            and status_similarity > rag_similarity
            and confidence >= self.min_confidence
        ):
            intent = QueryIntent.STATUS

        return IntentClassification(
            intent=intent,
            confidence=confidence,
            margin=margin,
            status_similarity=status_similarity,
            rag_similarity=rag_similarity,
        )