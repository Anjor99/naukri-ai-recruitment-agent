from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

import numpy as np

from rag.embeddings import EmbeddingModel


class ApplicationField(Enum):
    """Fields available from the application/status tool."""

    STATUS = "status"
    EXPECTED_SALARY = "expected_salary_inr"
    DAYS_SINCE_CREATED = "days_since_created"
    FLAGGED_PRIORITY_REVIEW = "flagged_priority_review"
    ESCALATION = "escalation"


ALL_APPLICATION_FIELDS = [
    ApplicationField.STATUS.value,
    ApplicationField.EXPECTED_SALARY.value,
    ApplicationField.DAYS_SINCE_CREATED.value,
    ApplicationField.FLAGGED_PRIORITY_REVIEW.value,
    ApplicationField.ESCALATION.value,
]


@dataclass(frozen=True)
class FieldMatch:
    """A successfully matched supported application field."""

    field: ApplicationField
    confidence: float
    clause: str


@dataclass(frozen=True)
class UnsupportedFieldRequest:
    """A query clause that does not map to a supported field."""

    clause: str
    confidence: float


@dataclass(frozen=True)
class FieldSelection:
    """
    Complete result of field extraction.

    requested_fields:
        Supported application fields explicitly requested.

    unsupported_fields:
        Query clauses that do not map to a supported field.

    details_requested:
        True when the user asks for all application details.
    """

    requested_fields: list[FieldMatch]
    unsupported_fields: list[UnsupportedFieldRequest]
    details_requested: bool = False


# ---------------------------------------------------------------------------
# Application record ID pattern
# ---------------------------------------------------------------------------

_RECORD_ID_PATTERN = re.compile(
    r"\bapp-\d{4}\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Representative examples for each supported field.
# ---------------------------------------------------------------------------

FIELD_EXAMPLES: dict[ApplicationField, tuple[str, ...]] = {
    ApplicationField.STATUS: (
        "application status",
        "current status of my application",
        "current state of my application",
        "what is happening with my application",
        "where does my application stand",
        "progress of my application",
        "has my application been processed",
        "what is the status",
        "give me the status",
        "tell me my status",
    ),

    ApplicationField.EXPECTED_SALARY: (
        "expected salary",
        "salary I entered in my application",
        "salary I requested",
        "salary expectation I provided",
        "compensation I expected",
        "salary associated with my application",
        "what is my expected salary",
        "give me my expected salary",
    ),

    ApplicationField.DAYS_SINCE_CREATED: (
        "days since my application was created",
        "age of my application",
        "how long ago my application was created",
        "number of days my application has existed",
        "how long my application has been in the system",
        "when my application was created",
        "how many days since my application was created",
        "how old is my application",
    ),

    ApplicationField.FLAGGED_PRIORITY_REVIEW: (
        "whether my application is flagged",
        "whether my application has been flagged for review",
        "priority review flag on my application",
        "whether my application is marked for priority review",
        "whether my application has a priority flag",
        "is my application flagged",
        "is it flagged",
        "has my application been flagged",
    ),

    ApplicationField.ESCALATION: (
        "should my application be escalated",
        "should it be escalated",
        "will my application be escalated",
        "will it be escalated",
        "what is the escalation status",
        "what is my escalation status",
        "is my application going to be escalated",
        "does my application need escalation",
        "does it need escalation",
        "does my application require escalation",
        "does it require escalation",
        "should someone escalate my application",
        "is escalation needed for my application",
        "does my application need urgent review",
        "will this application be escalated",
        "should this application be escalated",
    ),
}


# ---------------------------------------------------------------------------
# "All details" examples
# ---------------------------------------------------------------------------

DETAILS_EXAMPLES = (
    "give me all the details of my application",
    "give me all information about my application",
    "tell me everything available about my application",
    "show me my complete application details",
    "give me all available application information",
    "give all my details",
    "show me complete details",
    "give me all the details",
    "show me all the details",
    "tell me all the details",
    "give me all application details",
    "show me all application details",
    "tell me everything about my application",
    "give me everything about my application",
    "show me everything about my application",
)


class FieldSelector:
    """
    Extract application fields from a STATUS query.

    The selector works in two stages:

    1. Remove application record IDs.
    2. Decompose the remaining query into semantic clauses.
    3. Match each clause against the supported application fields.

    Record IDs identify WHICH application is requested.
    They are not application fields and therefore must not
    participate in field classification.
    """

    DEFAULT_FIELD_THRESHOLD = 0.50
    DEFAULT_DETAILS_THRESHOLD = 0.80

    _SEPARATORS = (
        " and ",
        " also ",
        " as well as ",
        " along with ",
        " plus ",
    )

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        field_threshold: float = DEFAULT_FIELD_THRESHOLD,
        details_threshold: float = DEFAULT_DETAILS_THRESHOLD,
    ) -> None:

        self.embedding_model = embedding_model or EmbeddingModel()

        self.field_threshold = field_threshold
        self.details_threshold = details_threshold

        self._field_embeddings: dict[
            ApplicationField,
            np.ndarray,
        ] = {}

        for field, examples in FIELD_EXAMPLES.items():
            embeddings = self.embedding_model.embed_texts(
                list(examples)
            )

            self._field_embeddings[field] = self._normalize(
                embeddings
            )

        self._details_embeddings = self._normalize(
            self.embedding_model.embed_texts(
                list(DETAILS_EXAMPLES)
            )
        )

    @staticmethod
    def _normalize(
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """L2-normalize embeddings for cosine similarity."""

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

        return embeddings / np.maximum(
            norms,
            1e-12,
        )

    def _best_similarity(
        self,
        query_embedding: np.ndarray,
        prototype_embeddings: np.ndarray,
    ) -> float:
        """Return the strongest cosine similarity to prototypes."""

        similarities = query_embedding @ prototype_embeddings.T

        return float(np.max(similarities))

    def _split_query(
        self,
        query: str,
    ) -> list[str]:
        """
        Split a query into independent semantic clauses.

        Examples:

            "status and expected salary"
            -> ["status", "expected salary"]

            "status of my application"
            -> ["status of my application"]
        """

        query = query.strip()

        if not query:
            return []

        normalized = query

        # Treat punctuation as clause boundaries.
        for punctuation in [",", ";"]:
            normalized = normalized.replace(
                punctuation,
                " and ",
            )

        clauses = [normalized]

        for separator in self._SEPARATORS:
            new_clauses: list[str] = []

            for clause in clauses:
                parts = clause.split(separator)

                for part in parts:
                    cleaned = part.strip()

                    if cleaned:
                        new_clauses.append(cleaned)

            clauses = new_clauses

        return clauses

    def _remove_record_ids(
        self,
        query: str,
    ) -> str:
        """
        Remove application record IDs before field classification.

        Example:

            "Give me all the details for APP-0001"

        becomes:

            "Give me all the details for"
        """

        cleaned = _RECORD_ID_PATTERN.sub(
            "",
            query,
        )

        # Clean up leftover whitespace.
        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

        # Remove dangling prepositions left after ID removal.
        cleaned = re.sub(
            r"\s+(for|of|about|on|regarding)\s*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        return cleaned

    def _is_details_request(
        self,
        query: str,
    ) -> tuple[bool, float]:
        """Detect whether the user is asking for all application details."""

        query_embedding = self.embedding_model.embed_text(query)

        query_embedding = self._normalize(
            query_embedding
        )[0]

        score = self._best_similarity(
            query_embedding,
            self._details_embeddings,
        )

        return (
            score >= self.details_threshold,
            score,
        )

    def _classify_clause(
        self,
        clause: str,
    ) -> FieldMatch | UnsupportedFieldRequest:
        """
        Match one query clause against the supported application schema.

        A clause gets exactly one outcome:

            supported field
            OR
            unsupported request
        """

        query_embedding = self.embedding_model.embed_text(
            clause
        )

        query_embedding = self._normalize(
            query_embedding
        )[0]

        scores: dict[ApplicationField, float] = {}

        for field, embeddings in self._field_embeddings.items():
            scores[field] = self._best_similarity(
                query_embedding,
                embeddings,
            )

        best_field, best_score = max(
            scores.items(),
            key=lambda item: item[1],
        )

        if best_score >= self.field_threshold:
            return FieldMatch(
                field=best_field,
                confidence=best_score,
                clause=clause,
            )

        return UnsupportedFieldRequest(
            clause=clause,
            confidence=best_score,
        )

    def classify(
        self,
        query: str,
    ) -> FieldSelection:
        """Extract all requested supported fields from a query."""

        query = query.strip()

        if not query:
            return FieldSelection(
                requested_fields=[],
                unsupported_fields=[],
            )

        # ---------------------------------------------------------
        # Remove record IDs FIRST.
        #
        # Example:
        # "give me all the details for app-0001"
        #
        # becomes:
        # "give me all the details"
        # ---------------------------------------------------------

        field_query = self._remove_record_ids(query)

        if not field_query:
            return FieldSelection(
                requested_fields=[],
                unsupported_fields=[],
            )

        # ---------------------------------------------------------
        # Decompose query.
        # ---------------------------------------------------------

        clauses = self._split_query(field_query)

        # ---------------------------------------------------------
        # Special case: ALL DETAILS
        #
        # Only allow this when the entire field query is one
        # semantic clause.
        #
        # Therefore:
        #
        # "give me all details"
        # -> all fields
        #
        # But:
        #
        # "give me status and applicant name"
        # -> status + unsupported applicant name
        # ---------------------------------------------------------

        if len(clauses) == 1:

            details_requested, details_score = (
                self._is_details_request(field_query)
            )

            if details_requested:
                return FieldSelection(
                    requested_fields=[
                        FieldMatch(
                            field=ApplicationField(field),
                            confidence=details_score,
                            clause="all application details",
                        )
                        for field in ALL_APPLICATION_FIELDS
                    ],
                    unsupported_fields=[],
                    details_requested=True,
                )

        # ---------------------------------------------------------
        # Classify every clause independently.
        # ---------------------------------------------------------

        requested_fields: list[FieldMatch] = []
        unsupported_fields: list[UnsupportedFieldRequest] = []

        for clause in clauses:

            result = self._classify_clause(
                clause
            )

            if isinstance(result, FieldMatch):
                requested_fields.append(result)

            else:
                unsupported_fields.append(result)

        # ---------------------------------------------------------
        # Remove duplicate fields.
        # ---------------------------------------------------------

        unique_fields: dict[
            ApplicationField,
            FieldMatch,
        ] = {}

        for match in requested_fields:

            existing = unique_fields.get(
                match.field
            )

            if (
                existing is None
                or match.confidence
                > existing.confidence
            ):
                unique_fields[match.field] = match

        requested_fields = list(
            unique_fields.values()
        )

        # ---------------------------------------------------------
        # Sort by confidence.
        # ---------------------------------------------------------

        requested_fields.sort(
            key=lambda match: match.confidence,
            reverse=True,
        )

        return FieldSelection(
            requested_fields=requested_fields,
            unsupported_fields=unsupported_fields,
            details_requested=False,
        )


# ---------------------------------------------------------------------------
# Shared instance.
# ---------------------------------------------------------------------------

_field_selector = FieldSelector()


def select_fields(
    query: str,
) -> list[str]:
    """
    Backwards-compatible helper.

    Returns only supported field names.
    """

    result = _field_selector.classify(
        query
    )

    return [
        match.field.value
        for match in result.requested_fields
    ]