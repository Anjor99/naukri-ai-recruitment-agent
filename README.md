# Naukri.com — AI Recruitment & HR Support Agent

An AI-powered recruitment and HR support agent built for the **Naukri.com — Recruitment & HR** capstone track.

The system combines a deterministic job-application dataset, local retrieval-augmented generation (RAG), a LangGraph-orchestrated agent, tool use, conversational memory, structured output validation, input/output guardrails, and a FastAPI + MCP deployment layer with production-grade reliability controls (timeouts, retries, checkpointing).

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Recommended Evaluation Order](#recommended-evaluation-order)
- [Example Queries](#example-queries)
- [Key Design Decisions](#key-design-decisions)
- [Evaluation Artifacts](#evaluation-artifacts)
- [Runtime Data](#runtime-data)
- [Project Status](#project-status)

---

## Features

| Area | Capability |
|---|---|
| Data | Deterministic, seeded job-application dataset (50 records) |
| Retrieval | Local embeddings (`all-MiniLM-L6-v2`) + ChromaDB, two chunking strategies |
| Generation | Grounded generation with similarity-gated "I don't know" fallback |
| Orchestration | LangGraph agent with routing, memory, and checkpointing |
| Tools | Deterministic job-application status tool with escalation scoring |
| Safety | Input guardrails (prompt injection, toxicity, PII masking) and output guardrails (toxicity, groundedness) |
| Output | Schema-validated structured responses |
| Deployment | FastAPI service and MCP server |
| Observability | PII-safe structured JSONL logging |
| Reliability | Node-level timeouts, global graph timeout, exponential-backoff retries |

---

## Project Structure

```text
naukri-ai-support-agent/
│
├── README.md
├── pyproject.toml
├── uv.lock
├── requirements.txt
├── .env.example
├── .gitignore
├── dataset.py
├── setup.py
├── run.py
├── mcp_server.py
├── mcp_client.py
│
├── agent/
│   ├── state.py
│   ├── router.py
│   ├── nodes.py
│   ├── graph.py
│   ├── tools.py
│   ├── helpers.py
│   ├── field_selector.py
│   ├── memory.py
│   ├── conversation.py
│   ├── reliability.py
│   └── api/
│       ├── app.py
│       ├── ask.py
│       ├── document.py
│       ├── models.py
│       └── logging_utils.py
│
├── rag/
│   ├── loader.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── generator.py
│   ├── ingest.py
│   └── cli.py
│
├── knowledge_base/          # 12 HR/recruitment policy documents
├── tests/                   # 13 test modules
├── scripts/
│   └── demo.py
├── evaluation/
│   ├── calibration.md
│   └── chunking_evaluation.md
├── reports/
└── data/
    ├── chroma_db/
    └── checkpoints.sqlite
```

---

## Architecture

```text
                    ┌────────────────────┐
                    │      User / API     │
                    └─────────┬──────────┘
                              │
                              v
                    ┌────────────────────┐
                    │      Guardrails     │
                    │  Input validation   │
                    │   PII masking       │
                    │  Prompt injection   │
                    └─────────┬──────────┘
                              │
                              v
                    ┌────────────────────┐
                    │  LangGraph Router   │
                    └─────────┬──────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 v                         v
        ┌─────────────────┐       ┌──────────────────┐
        │       RAG        │       │ Application Tool │
        │  ChromaDB         │       │ JOB_APPLICATIONS │
        │  Embeddings       │       │ Status lookup     │
        │  Grounding        │       │ Escalation        │
        └────────┬────────┘       └─────────┬────────┘
                 │                          │
                 └────────────┬─────────────┘
                              │
                              v
                    ┌────────────────────┐
                    │  Structured Output   │
                    │ + Output Guardrail   │
                    └─────────┬──────────┘
                              │
                              v
                    ┌────────────────────┐
                    │    API Response      │
                    └────────────────────┘
```

Supporting infrastructure: conversation memory (`memory.json`), SQLite-backed LangGraph checkpointing, an MCP server exposing the status tool, and PII-safe structured logging.

---

## Setup

### Requirements

- Python 3.12+
- Git
- Internet connection (for initial dependency/model downloads)
- Windows, macOS, or Linux

### Option 1 — Using `uv`

```bash
uv sync
uv run python setup.py
```

### Option 2 — Using standard Python + pip

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Variables

```bash
copy .env.example .env
```

The project runs by default in deterministic `MOCK_LLM` mode and requires no external LLM API:

```env
MOCK_LLM=true
```

For optional Groq-based generation:

```env
MOCK_LLM=false
GROQ_API_KEY=your_api_key_here
```

For offline Hugging Face model execution:

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
```

### Initial Project Setup

```bash
python setup.py
```

This script:

- Validates the deterministic application dataset
- Checks that all 12 knowledge-base documents exist
- Creates the ChromaDB storage directory
- Builds the `fixed_size_collection` and `sentence_based_collection`
- Embeds chunks using `all-MiniLM-L6-v2` and stores them persistently

Re-run `setup.py` after a fresh checkout or whenever the local RAG index needs rebuilding.

---

## Running the Application

### Quick Demo

```bash
python scripts/demo.py
```

Exercises dataset generation, RAG retrieval, grounded and out-of-scope responses, application-status lookup, memory, guardrails, structured validation, MCP integration, and reliability configuration.

### Full Application

```bash
python run.py
```

Starts:

- FastAPI → `http://127.0.0.1:8000`
- MCP → `http://127.0.0.1:8001/mcp`

Run components individually:

```bash
python run.py api    # FastAPI only
python run.py mcp    # MCP only
```

Stop with `Ctrl + C`.

### FastAPI Usage

Swagger docs: `http://127.0.0.1:8000/docs`

Endpoints: `GET /health`, `POST /ask`, `POST /add-document`

```json
{
  "query": "What is the notice period policy?",
  "conversation_id": "demo-002"
}
```

### MCP Usage

```bash
python run.py mcp
```

Endpoint: `http://127.0.0.1:8001/mcp`

Exposes `check_job_application_status`, callable with IDs such as `APP-0001`, `APP-0031`.

---

## Testing

Each test is an individually executable module (no combined test runner):

```bash
python -m tests.test_dataset
python -m tests.test_rag
python -m tests.test_chunking
python -m tests.test_tool
python -m tests.test_agent
python -m tests.test_memory
python -m tests.test_schema
python -m tests.test_guardrails
python -m tests.test_api
python -m tests.test_logging
python -m tests.test_rag_triad
python -m tests.test_mcp
python -m tests.test_checkpointing
python -m tests.test_reliability
```

With `uv`, prefix any command with `uv run`, e.g. `uv run python -m tests.test_dataset`.

---

## Recommended Evaluation Order

**1. Install dependencies**

```bash
uv sync
# or
pip install -r requirements.txt
```

**2. Build the RAG collections**

```bash
python setup.py
```

**3. Run the demo**

```bash
python scripts/demo.py
```

**4. Run the tests**

Dataset and RAG:
```bash
python -m tests.test_dataset
python -m tests.test_rag
python -m tests.test_chunking
```

Agent and tools:
```bash
python -m tests.test_tool
python -m tests.test_agent
python -m tests.test_memory
python -m tests.test_schema
```

Guardrails, API, and logging:
```bash
python -m tests.test_guardrails
python -m tests.test_api
python -m tests.test_logging
```

Evaluation, MCP, and reliability:
```bash
python -m tests.test_rag_triad
python -m tests.test_mcp
python -m tests.test_checkpointing
python -m tests.test_reliability
```

---

## Example Queries

**RAG / Policy Questions**
- What is the notice period policy?
- How are interviews scheduled?
- Who is eligible for remote work?
- How does the referral bonus work?

**Application Status**
- What is the status of APP-0001?
- Check application APP-0031

**Follow-up Using Memory**
1. "What is the status of APP-0001?"
2. "What salary did I enter?" — resolved using the remembered application ID.

**Out-of-scope Query**
- "What is the capital of France?" — the grounding threshold prevents an unsupported HR answer.

---

## Key Design Decisions

**Deterministic dataset** — A seeded dataset makes application-status behavior reproducible across runs and tests.

**Local embeddings** — `all-MiniLM-L6-v2` avoids dependency on an external embedding API.

**Grounded generation** — The system refuses to answer when retrieval similarity falls below the calibrated threshold (`0.30`) rather than relying on unrestricted LLM generation. Observed in-scope top-1 similarity ranged 0.4859–0.7930; out-of-scope ranged -0.0160–0.0733.

**Fixed-size-overlap chunking** — Selected over sentence-based chunking for slightly higher Precision@3 (0.467 vs 0.433) while both maintained perfect Recall@3 (1.000).

**Explicit routing** — Queries containing an application ID (e.g. `APP-0001`) are routed directly to the deterministic status tool rather than RAG.

**Persistent conversation state** — Conversation IDs provide continuity across turns and double as LangGraph thread IDs for checkpointing.

**Guardrails before and after generation** — Input validation reduces unsafe or malicious requests; output validation rejects unsupported or unsafe responses.

**PII-safe logging** — Logs retain operational detail (conversation ID, trace ID, event, step, elapsed time, PII detection status) without storing raw sensitive data.

**Reliability controls** — A 5-second node-level timeout on the RAG node, a 30-second global graph timeout, and a retry policy (max 3 attempts, 0.1s initial interval, 2.0x backoff, 0.4s max interval, jitter enabled) protect against slow or transient failures.

---

## Evaluation Artifacts

| File | Contents |
|---|---|
| `evaluation/calibration.md` | Similarity calibration for grounded generation |
| `evaluation/chunking_evaluation.md` | Precision@3 / Recall@3 comparison of chunking strategies |
| `reports/rag_triad_evaluation.json` | Context relevance, groundedness, and answer relevance across all 12 in-scope topics and out-of-scope queries |

---

## Runtime Data

The following are generated locally and should not be committed to Git:

```text
data/chroma_db/
data/checkpoints.sqlite
logs/
memory.json
```

---

## Project Status

| Task | Status |
|---|---|
| 1 — Dataset | Complete |
| 2 — Knowledge Base | Complete |
| 3 — RAG Indexing | Complete |
| 4 — Grounded Generation | Complete |
| 5 — Chunking Evaluation | Complete |
| 6 — Status Tool | Complete |
| 7 — LangGraph Agent | Complete |
| 8 — Conversation Memory | Complete |
| 9 — Structured Output | Complete |
| 10 — Guardrails | Complete |
| 11 — FastAPI Deployment | Complete |
| 12 — PII-safe Logging | Complete |
| 13 — RAG Triad Evaluation | Complete |
| 14 — MCP Integration | Complete |
| 15 — SQLite Checkpointing | Complete |
| 16 — Reliability | Complete |

---

## License

This project was created as part of the **Naukri.com — Recruitment & HR** AI agent capstone project.