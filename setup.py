"""
Repository setup and initialization script.

Run:
    python setup.py

This script:
1. Validates the generated job-application dataset.
2. Validates that the knowledge base contains the required documents.
3. Creates required data directories.
4. Builds both ChromaDB collections:
       - fixed_size_collection
       - sentence_based_collection
5. Prints a final setup summary.

The script is intentionally idempotent: running it again is safe.
"""

from __future__ import annotations

import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent

KNOWLEDGE_BASE = ROOT / "knowledge_base"
DATA_DIR = ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
CHECKPOINT_DB = DATA_DIR / "checkpoints.sqlite"


# ---------------------------------------------------------------------------
# Required knowledge-base documents
# ---------------------------------------------------------------------------

REQUIRED_DOCUMENTS = {
    "job_application_eligibility.txt",
    "interview_scheduling.txt",
    "offer_negotiation.txt",
    "background_verification_process.txt",
    "notice_period.txt",
    "referral_bonus.txt",
    "internal_transfer.txt",
    "probation_period.txt",
    "remote_work.txt",
    "diversity_hiring.txt",
    "exit_interview.txt",
    "applicant_data_retention.txt",
}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def ensure_directories() -> None:
    """Create directories required by the application."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    print("[OK] Required data directories exist.")


# ---------------------------------------------------------------------------
# Dataset validation
# ---------------------------------------------------------------------------

def validate_dataset() -> None:
    """Validate the deterministic job-application dataset."""

    from dataset import JOB_APPLICATIONS, validate_applications

    print("[DATASET] Validating job applications...")

    counts = validate_applications(JOB_APPLICATIONS)

    total = len(JOB_APPLICATIONS)
    priority_count = counts["flagged_priority_review"]
    priority_percentage = (priority_count / total) * 100

    print(f"[OK] Total applications: {total}")
    print(
        f"[OK] Priority-review applications: "
        f"{priority_count}/{total} ({priority_percentage:.2f}%)"
    )

    print("[OK] Category counts:")
    for category, count in counts["category"].items():
        print(f"     - {category}: {count}")

    print("[OK] Status counts:")
    for status, count in counts["status"].items():
        print(f"     - {status}: {count}")


# ---------------------------------------------------------------------------
# Knowledge-base validation
# ---------------------------------------------------------------------------

def validate_knowledge_base() -> None:
    """Check that all required knowledge-base documents are present."""

    print("[KNOWLEDGE BASE] Checking required documents...")

    if not KNOWLEDGE_BASE.exists():
        raise FileNotFoundError(
            f"Knowledge-base directory not found: {KNOWLEDGE_BASE}"
        )

    actual_documents = {
        path.name
        for path in KNOWLEDGE_BASE.glob("*.txt")
    }

    missing = REQUIRED_DOCUMENTS - actual_documents

    if missing:
        print("[ERROR] Missing required knowledge-base documents:")
        for filename in sorted(missing):
            print(f"       - {filename}")

        raise RuntimeError(
            "Knowledge-base validation failed."
        )

    print(
        f"[OK] Found {len(actual_documents)} knowledge-base text files."
    )

    print("[OK] All 12 required topics are present.")


# ---------------------------------------------------------------------------
# Chroma initialization
# ---------------------------------------------------------------------------

def build_collections() -> None:
    """
    Build both Chroma collections using the project's existing RAG pipeline.

    Existing Chroma data is removed first so setup always produces a clean,
    deterministic index from the current knowledge base.
    """

    print("[RAG] Preparing ChromaDB collections...")

    # Import only after basic filesystem validation.
    from rag.loader import load_documents
    from rag.chunking import (
        fixed_size_chunks,
        sentence_based_chunks,
    )
    from rag.embeddings import EmbeddingModel
    from rag.vector_store import VectorStore

    documents = load_documents(str(KNOWLEDGE_BASE))

    if not documents:
        raise RuntimeError(
            "No knowledge-base documents were loaded."
        )

    print(f"[OK] Loaded {len(documents)} documents.")

    # ------------------------------------------------------------------
    # Start from a clean vector database.
    # ------------------------------------------------------------------

    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    print("[OK] Existing Chroma database cleared.")

    # ------------------------------------------------------------------
    # Chunk documents using both strategies.
    # ------------------------------------------------------------------

    fixed_chunks = fixed_size_chunks(documents)
    sentence_chunks = sentence_based_chunks(
        documents,
        sentences_per_chunk=2,
    )

    print(f"[OK] Fixed-size chunks: {len(fixed_chunks)}")
    print(f"[OK] Sentence-based chunks: {len(sentence_chunks)}")

    # ------------------------------------------------------------------
    # Initialize embedding model and vector store.
    # ------------------------------------------------------------------

    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model)

    # ------------------------------------------------------------------
    # Create fixed-size collection.
    # ------------------------------------------------------------------

    fixed_collection = vector_store.create_collection(
        "fixed_size_collection"
    )

    vector_store.add_chunks(
        fixed_collection,
        fixed_chunks,
    )

    print(
        "[OK] Created fixed_size_collection "
        f"({len(fixed_chunks)} chunks)."
    )

    # ------------------------------------------------------------------
    # Create sentence-based collection.
    # ------------------------------------------------------------------

    sentence_collection = vector_store.create_collection(
        "sentence_based_collection"
    )

    vector_store.add_chunks(
        sentence_collection,
        sentence_chunks,
    )

    print(
        "[OK] Created sentence_based_collection "
        f"({len(sentence_chunks)} chunks)."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print_header("NAUKRI AI SUPPORT AGENT — REPOSITORY SETUP")

    print(f"Project root: {ROOT}")

    # 1. Filesystem
    print_header("1. INITIALIZING DIRECTORIES")
    ensure_directories()

    # 2. Dataset
    print_header("2. VALIDATING DATASET")
    validate_dataset()

    # 3. Knowledge base
    print_header("3. VALIDATING KNOWLEDGE BASE")
    validate_knowledge_base()

    # 4. RAG
    print_header("4. BUILDING RAG INDEXES")
    build_collections()

    # 5. Final summary
    print_header("SETUP COMPLETE")

    print("[READY] Dataset validated")
    print("[READY] Knowledge base validated")
    print("[READY] fixed_size_collection created")
    print("[READY] sentence_based_collection created")
    print("[READY] ChromaDB initialized")
    print()
    print("Next recommended commands:")
    print()
    print("  python run.py")
    print("  python scripts/demo.py")
    print()
    print("FastAPI docs:")
    print("  http://127.0.0.1:8000/docs")
    print()


if __name__ == "__main__":
    main()