---
title: Naukri AI Support Agent
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Naukri.com — AI Recruitment & HR Support Agent

An AI-powered recruitment and HR support agent built for the **Naukri.com — Recruitment & HR** capstone track.

The system combines a deterministic job-application dataset, local retrieval-augmented generation (RAG), a LangGraph-orchestrated agent, tool use, conversational memory, structured output validation, input/output guardrails, a FastAPI + MCP deployment layer with production-grade reliability controls (timeouts, retries, checkpointing), and a browser-based chat + live agent-graph UI.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Web UI](#web-ui)
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
| Web UI | Responsive chat interface with a live, branch-aware LangGraph topology view |
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
├── static/                  # Browser UI served by FastAPI (chat + agent graph)
│   ├── index.html
│   ├── css/
│   │   ├── main.css         # Shell layout, topbar, view-switcher tabs, responsive rules
│   │   ├── sidebar.css       # Knowledge-base / application sidebar (off-canvas on mobile)
│   │   ├── chat.css          # Chat panel, message bubbles, input area
│   │   └── graph.css         # Agent graph panel: layered nodes + SVG edge overlay
│   └── js/
│       ├── api.js            # Thin fetch wrapper for /ask, /health, /knowledge-base, /application, /graph
│       ├── app.js             # Bootstraps the page: chat, sidebar drawer, view tabs, health check
│       ├── application.js      # Application-ID lookup panel in the sidebar
│       ├── chat.js             # Message rendering, conversation state, /ask requests
│       ├── graph.js            # Renders /graph as a layered DAG with SVG edges (not a flat list)
│       └── knowledge-base.js    # Populates the sidebar's knowledge-base list from /knowledge-base
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
                    │  Web UI (browser)   │
                    │  Chat + Agent Graph  │
                    └─────────┬──────────┘
                              │
                              v
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

Supporting infrastructure: conversation memory (`memory.json`), SQLite-backed LangGraph checkpointing, an MCP server exposing the status tool, PII-safe structured logging, and the `static/` browser UI that talks to the FastAPI endpoints above.

---

## Web UI

The FastAPI service serves a small single-page frontend (`static/`) alongside the API, giving two views of the same running agent:

- **Chat** — the conversational interface: send a query, see the agent's response, the route it took, and (when relevant) the looked-up application record, all against the live `/ask` endpoint.
- **Agent Graph** — a live rendering of the `/graph` endpoint's actual LangGraph topology. Nodes are grouped into rows by their distance from the start node, so branching (e.g. the router fanning out to `rag` / `status` / `unknown`) and merging (e.g. everything converging back into `response`) are drawn as a real DAG with curved SVG edges — not flattened into a single sequential column. Conditional edges (the router's branches) are shown dashed and accent-colored.

Only one of these two panels is shown at a time, switched via the **Chat / Agent Graph** tabs above the workspace, so the layout stays uncluttered and scroll-free instead of squeezing both into a split-screen.

The sidebar (knowledge-base list and application lookup) is always available. On narrower screens it collapses into an off-canvas drawer, opened with the topbar's menu button, so the chat or graph view still gets the full width of the screen instead of being squeezed by a fixed-width sidebar.

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

Open `http://127.0.0.1:8000` in a browser for the chat + agent-graph web UI. Run components individually:

```bash
python run.py api    # FastAPI only
python run.py mcp    # MCP only
```

Stop with `Ctrl + C`.

### FastAPI Usage

Swagger docs: `http://127.0.0.1:8000/docs`

Endpoints: `GET /health`, `POST /ask`, `POST /add-document`, `GET /knowledge-base`, `GET /application/{record_id}`, `GET /graph`

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

**Graph visualization mirrors the real topology** — The `/graph` endpoint's nodes and edges are rendered as a layered DAG (grouped by distance from the start node) rather than a single sequential list, so the UI's picture of the agent matches how LangGraph actually routes and merges, including conditional branches.

**Single-panel, tab-based workspace** — Chat and Agent Graph are shown one at a time via tabs rather than a permanent split view, and the sidebar becomes an off-canvas drawer on narrow screens, so the UI stays usable and scroll-free on both desktop and mobile.

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
| 17 — Web UI (chat + live agent graph) | Complete |

---

## License

This project was created as part of the **Naukri.com — Recruitment & HR** AI agent capstone project.