# Technical Implementation Plan: Groww Mutual Fund FAQ Assistant

**Document Version:** 1.0.0  
**Target Architecture:** [docs/architecture.md](file:///c:/Users/mishr/OneDrive/Desktop/AI%20Projects/Groww/docs/architecture.md)  
**Product Specification:** [PRD.md](file:///c:/Users/mishr/OneDrive/Desktop/AI%20Projects/Groww/PRD.md) | [ProblemStatement.md](file:///c:/Users/mishr/OneDrive/Desktop/AI%20Projects/Groww/ProblemStatement.md)  
**Scope Boundary:** 5 Groww Scheme Web Pages (HTML-only; Strictly No PDFs)

---

## Executive Implementation Overview

This document outlines the step-by-step technical roadmap for building the **Groww Mutual Fund Facts-Only FAQ Assistant**. To ensure modularity, high quality, and systematic execution, the implementation is broken down into **6 discrete phases**.

### Phase Summary & Execution Roadmap

```mermaid
gantt
    title System Implementation Phases
    dateFormat  YYYY-MM-DD
    section Core Infrastructure
    Phase 1: Environment Setup & Project Foundation      :p1, 2026-08-12, 1d
    section Data Pipeline
    Phase 2: Ingestion & HTML Web Scraping Engine       :p2, after p1, 2d
    Phase 3: Chunking & Vector DB Indexing              :p3, after p2, 2d
    section RAG & Safety Engine
    Phase 4: Intent Classifier, Hybrid Search & Refusal :p4, after p3, 2d
    Phase 5: Grounded LLM Generator & Output Guardrails  :p5, after p4, 2d
    section Delivery & Validation
    Phase 6: API Layer, Web UI & Automated Evaluation   :p6, after p5, 2d
```

---

## Progress Checklist

- [x] **Phase 1:** Project Setup, Dependencies & Configuration
- [x] **Phase 2:** HTML Scraper & Extractor Pipeline (5 Groww URLs)
- [x] **Phase 3:** Element-Aware Chunking & Vector DB Indexing
- [x] **Phase 4:** Intent Classifier, Hybrid Retrieval & Refusal Engine
- [x] **Phase 5:** Grounded LLM Generator & Output Validation Guardrails
- [x] **Phase 6:** FastAPI Endpoints, React Web UI & Automated Evaluation Test Suite

---

## Phase 1: Environment Setup, Configuration & Project Structure

### Objective
Initialize the project repository, set up Python and Node.js environments, define project constants (including allowed Groww URLs and guardrail parameters), and configure the folder hierarchy.

### Folder Structure to Initialize
```text
groww-mf-faq/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── scraper.py
│   │   │   ├── parser.py
│   │   │   ├── chunker.py
│   │   │   └── scheduler.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── intent.py
│   │   │   ├── retriever.py
│   │   │   ├── generator.py
│   │   │   └── validator.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logger.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── raw/          # Raw HTML pages
│   ├── processed/    # Extracted JSON structures
│   └── vector_db/    # Persistent ChromaDB store
├── evaluation/
│   ├── test_dataset.json
│   └── eval.py
├── docs/
│   └── architecture.md
├── PRD.md
├── ProblemStatement.md
└── implementation.md
```

### Detailed Deliverables

1. **Python Dependencies (`backend/requirements.txt`):**
   ```text
   fastapi>=0.110.0
   uvicorn>=0.28.0
   httpx>=0.27.0
   beautifulsoup4>=4.12.3
   playwright>=1.42.0
   apscheduler>=3.10.4
   chromadb>=0.4.24
   sentence-transformers>=2.6.0
   openai>=1.14.0
   pydantic>=2.6.0
   pydantic-settings>=2.2.0
   pytest>=8.1.0
   python-dotenv>=1.0.1
   ```

2. **System Configuration (`backend/app/config.py`):**
   - Define strict allowed URL list (5 HDFC mutual fund URLs on Groww)
   - Define ingestion schedule: `INGESTION_CRON_SCHEDULE = "15 9 * * *"` (Daily at 9:15 AM IST)
   - Define embedding model: `EMBEDDING_MODEL_NAME = "BAAI/bge-large-en-v1.5"` (1024-dimensional dense vectors)
   - Define local vector store: `VECTOR_STORE_PATH = "data/vector_db"` (Chroma DB Local Store via `chromadb.PersistentClient`)
   - Set max response sentence limit: `3`
   - Require exact citation count: `1`
   - Set fallback text: `"I couldn't verify this information from the available official sources."`

### Verification Criteria
- [x] Python virtual environment activates with all dependencies installed.
- [x] `python -c "import app.config as cfg; print(len(cfg.ALLOWED_URLS))"` outputs `5`.

---

## Phase 2: Ingestion & HTML Extraction Pipeline (Scraper + Parser)

### Objective
Build an automated ingestion module to fetch web pages for the 5 Groww URLs, sanitize HTML content, extract key financial facts (Expense Ratio, Exit Load, Minimum SIP, Benchmark, Riskometer, NAV), and save structured records locally.

### Detailed Deliverables

1. **Async Web Scraper (`backend/app/ingestion/scraper.py`):**
   - Implement dynamic HTML fetching using `httpx` or `playwright` (to execute JS rendering on Groww).
   - Save raw HTML snapshots to `data/raw/<scheme_slug>.html`.

2. **DOM Parser & Metadata Extractor (`backend/app/ingestion/parser.py`):**
   - Strip navigation headers, footers, scripts, styles, and marketing popups.
   - Extract key-value key metrics from Groww web cards (`scheme_name`, `expense_ratio`, `exit_load`, `min_sip_amount`, `benchmark`, `riskometer`, `last_updated_date`).
   - Save extracted structured data to `data/processed/<scheme_slug>.json`.

3. **Daily Automated Ingestion Scheduler (`backend/app/ingestion/scheduler.py`):**
   - Configure `APScheduler` `AsyncIOScheduler` to trigger the scraper, parser, chunker, and vector store updater automatically **daily at 9:15 AM IST** (`cron: 15 9 * * *`).
   - Provide manual execution trigger method `run_ingestion_now()` for API calls and CLI.

### Verification Criteria
- [x] Running `python -m app.ingestion.scraper` downloads 5 HTML files to `data/raw/`.
- [x] Running `python -m app.ingestion.parser` produces 5 validated JSON files in `data/processed/` containing non-empty `expense_ratio`, `exit_load`, `benchmark`, and `min_sip`.
- [x] Triggering `scheduler.start()` correctly schedules next execution at `09:15 AM` daily.

---

## Phase 3: Semantic + Element-Aware Chunking & Vector DB Indexing

### Objective
Segment extracted scheme data into semantic key-value and tabular chunks, attach rich metadata schemas, generate dense vector embeddings, and index them into a persistent ChromaDB vector store.

### Detailed Deliverables

1. **Element-Aware Chunker (`backend/app/ingestion/chunker.py`):**
   - Create atomic chunks for single facts (e.g., Exit Load section, Expense Ratio card).
   - Attach mandatory metadata attributes to each chunk:
     - `chunk_id`
     - `scheme_name`
     - `scheme_slug`
     - `source_url` (must be one of the 5 allowed URLs)
     - `fact_type` (e.g., `exit_load`, `expense_ratio`, `benchmark`, `min_sip`, `riskometer`)
     - `effective_date` / `last_crawled`

2. **Vector DB Manager (`backend/app/rag/vector_store.py`):**
   - Initialize **Chroma DB Local Store** (`chromadb.PersistentClient(path="data/vector_db")`) with collection `groww_mf_chunks`.
   - Embed chunks using `sentence-transformers` model **`BAAI/bge-large-en-v1.5`** (1024-dimensional dense vectors).
   - Create helper methods for upserting and filtered metadata query search.

3. **Ingestion CLI Script (`scripts/ingest.py`):**
   - Executable command to trigger scraping, parsing, chunking, and vector indexing in a single command.

### Verification Criteria
- [x] Running `python scripts/ingest.py` populates `data/vector_db/` with all generated chunks.
- [x] Querying vector DB for `scheme_slug == "hdfc-defence-fund-direct-growth"` returns only chunks originating from `https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth`.

---

## Phase 4: Intent Classifier, Hybrid Search & Refusal Engine

### Objective
Construct the query pre-processing layer to classify user intent (Factual, Advisory, Performance, Out-of-Scope), execute hybrid vector search with metadata filtering for factual queries, and generate deterministic refusal responses for advisory requests.

### Detailed Deliverables

1. **Intent Classifier (`backend/app/rag/intent.py`):**
   - Classify queries into four categories using keyword rules + LLM classification:
     - `FACTUAL`: Expense ratio, exit load, benchmark, riskometer, min SIP, lock-in.
     - `ADVISORY`: "Should I buy?", "Which fund is best?", "Is this good for 5 years?", "Should I switch?".
     - `PERFORMANCE`: "Predict returns", "How much will 10k grow?".
     - `UNSUPPORTED`: Non-indexed funds (e.g., SBI, ICICI) or personal tax advice.

2. **Hybrid Retriever (`backend/app/rag/retriever.py`):**
   - Extract target scheme entity from query (e.g., "HDFC Mid Cap" -> `hdfc-mid-cap-fund-direct-growth`).
   - Pre-filter vector search by `scheme_slug`.
   - Execute similarity search; apply a strict distance score threshold (e.g., cosine similarity ≥ 0.75).

3. **Deterministic Refusal Engine (`backend/app/rag/refusal.py`):**
   - Return standard refusal message for advisory queries with a citation to the relevant scheme page.

### Verification Criteria
- [x] Query `"Should I invest in HDFC Small Cap?"` is classified as `ADVISORY` and immediately returns refusal text.
- [x] Query `"What is the benchmark of HDFC Defence Fund?"` is classified as `FACTUAL` and retrieves context with confidence > 0.8.

---

## Phase 5: Grounded LLM Generator & Output Validation Guardrails

### Objective
Implement the RAG generation pipeline using strict system prompts to prevent hallucination, followed by an automated 5-check Output Validation Guardrail to enforce sentence limits, citation rules, and date footers.

### Detailed Deliverables

1. **Grounded Answer Generator (`backend/app/rag/generator.py`):**
   - Prompt LLM with retrieved context only.
   - Enforce constraints: max 3 sentences, exactly 1 source link, date footer `"Last updated from sources: <date>"`.

2. **Output Validator (`backend/app/rag/validator.py`):**
   - Implement `validate_response()` verifying:
     1. `sentence_count <= 3`
     2. `citation_count == 1`
     3. `citation_url in ALLOWED_URLS`
     4. Footer `"Last updated from sources:"` present
     5. No advisory language present
   - If validation fails, return fallback message: `"I couldn't verify this information from the available official sources."`

### Verification Criteria
- [x] Unit test passes verifying that any generated response exceeding 3 sentences triggers automatic fallback replacement.
- [x] Unit test passes verifying that any response containing a URL outside the 5 allowed Groww URLs is rejected.

---

## Phase 6: FastAPI Backend, React Web UI & Automated Evaluation

### Objective
Expose the system via FastAPI endpoints, build a sleek React/Vite web chat UI with visible "Facts-Only" disclaimers, and run an automated evaluation test suite over 75 test cases.

### Detailed Deliverables

1. **FastAPI Endpoints (`backend/app/main.py`):**
   - `POST /api/v1/chat`: Main query endpoint returning JSON answer, source URL, date, and intent.
   - `GET /api/v1/health`: Health check endpoint.
   - `POST /api/v1/ingest`: Admin trigger to re-run ingestion pipeline.

2. **React Web Application (`frontend/`):**
   - Clean chat interface with welcome message, persistent disclaimer banner (`"Facts-only. No investment advice."`), three sample prompt buttons, source citation links, and date footers.

3. **Automated Evaluation Suite (`evaluation/eval.py` & `evaluation/test_dataset.json`):**
   - Run 75 benchmark queries:
     - 50 Factual Queries
     - 15 Advisory Refusal Queries
     - 10 Edge Cases
   - Assert targets:
     - Factual Accuracy ≥ 95%
     - Citation Validity ≥ 98%
     - Refusal Accuracy ≥ 98%
     - Constraint Compliance ≥ 99%

### Verification Criteria
- [x] `pytest evaluation/eval.py` completes with all SLA targets passing.
- [x] Frontend runs via `npm run dev` and communicates seamlessly with FastAPI backend.
