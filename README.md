# AI_FLASK_SERVICE

Production-ready (work-in-progress) Flask microservice that exposes APIs for:
- Upload-free (URL-based) document ingestion
- Text chunking + embedding generation + persistence
- Semantic similarity search over stored document embeddings
- Retrieval-Augmented Generation (RAG) chat endpoint
- (Pluggable) Large Language Model (LLM) inference via a GenAI hub / OpenAI compatible proxy
- Programmatic model configuration + deployment (helper utilities)
- Supabase object storage file fetching


---

## Key Features

1. Modular Flask architecture using Blueprints:
   - `/api/documents` – (demo placeholder) returns sample documents.
   - `/api/genai` – token retrieval, document embedding + storage, semantic search.
   - `/api/rag-pipeline` – end‑to‑end Retrieval → Augmentation → Generation chat API.
2. Asynchronous (threaded) background ingestion for remote files (by URL).
3. Chunked document processing with overlap for better embedding recall.
4. Batched embedding computation for efficiency (`get_embeddings_batch`).
5. Vector similarity search backed by (presumably) SAP HANA or similar DB (per naming).
6. Supabase storage integration for downloading protected assets.
7. Utilities for dynamic model configuration and deployment via an external AI API.
8. Environment-driven configuration for portability (Cloud Run / container friendly).
9. Clear layering:
   - API layer (Flask Blueprints)
   - Processing layer (`document_processing`)
   - Embedding + persistence layer (`hana_db_connection`, `embedding`)
   - LLM inference layer (`utils/LLM.py` via GenAI hub proxy)
   - Deployment/config utilities (`model_config.py`, `model_deployment.py`)

---

## High-Level Architecture

```
                +------------------------------+
Client -------> | Flask App (app.py)          |
                |  Registers Blueprints       |
                +---------------+--------------+
                                |
   +----------------------------+-------------------------------+
   |                            |                               |
/api/genai                 /api/rag-pipeline               /api/documents
   |                            |                               |
   |  (Token, Embed, Search)    |  (RAG Chat)                   | (Demo JSON)
   |                            |                               |
   v                            v
+----------------+        +-----------------+
| Document Proc. |        | RAG Pipeline    |
|  Download &    |        | 1. Embed Query  |
|  Chunk Text    |        | 2. Retrieve     |
|  Batch Embed   |        | 3. Augment      |
+--------+-------+        | 4. Generate     |
         |                +--------+--------+
         v                          |
  +-------------+                   v
  | Embeddings  | <--- Similarity Search (DB / Vector Store)
  | (DB/HANA)   |
  +------+------+ 
         ^
         |
  External File Sources (Supabase / URL)
```

---

## API Overview

### 1. Health / Root
GET `/`  
Returns: `"home"` (basic liveness check).

### 2. Documents (Placeholder)
GET `/api/documents/`  
Returns static sample JSON.  
Issues:
- Duplicate route decorators; one has `methods=['']` (invalid) – should be removed or corrected.

### 3. GenAI Hub Blueprint (`/api/genai`)

| Endpoint | Method | Purpose | Request Body (JSON) | Notes |
|----------|--------|---------|----------------------|-------|
| `/token` | POST | Obtain access token | none | Uses `get_access_token()` |
| `/create-store-embedding` | POST | Download file by `file_url`, process, embed, store | `file_url` (str), `username` (str), `doc_type` (str) | Metadata is created but not actually passed into worker thread (bug) |
| `/search-similiar-documents` | POST | Semantic search | `query` (str), `k` (int, opt), `username` (opt) | Several variable / method call bugs (see Issues) |

### 4. RAG Pipeline Blueprint (`/api/rag-pipeline`)
POST `/api/rag-pipeline/chat`  
Request JSON:
```
{
  "query": "What is ...?",
  "k": 3,
  "username": "optional-filter",
  "temperature": 0.1,
  "max_tokens": 500
}
```
Response:
```
{
  "success": true,
  "query": "...",
  "answer": "Generated answer..."
}
```
Flow:
1. Embed user query.
2. Retrieve top-K similar documents.
3. Concatenate text into context.
4. Construct prompt and call LLM (`gpt-4o-mini` via `get_llm_response`).
5. Return generated answer (no source citations yet).

---

## Document Processing & Embeddings

File: `utils/document_processing.py`

Key steps:
1. `process_and_embed_file_from_url(file_url)` orchestrates:
   - Download + extract text (PDF / DOC / DOCX).
   - `split_text_into_chunks` with overlap (default 1000 chars, 200 overlap).
   - `preprocess_text_chunks` (not shown in partial; assumed cleanup).
   - Batch embeddings via `get_embeddings_batch`.
   - Build rows and persist via `batch_insertion_embedding`.
2. Chunk metadata includes `chunk_index`, `chunk_size`, `source_url`.
3. Resilient HTTP downloads with retries (`urllib3 Retry` + `requests` session).
4. Temporary file usage to handle large files efficiently.

(Sections after the visible truncation should be documented similarly if they include PDF/DOCX parsing logic.)

---

## LLM Inference

File: `utils/LLM.py`

- Wrapper around a GenAI hub / OpenAI-like proxy.
- Uses `chat.completions.create` with:
  - System prompt: "You are a helpful assistant."
  - Deterministic generation (`temperature=0.0` in base helper; pipeline overrides conceptually with custom temp).
- Model currently hardcoded in RAG pipeline to `"gpt-4o-mini"`.

---

## Model Configuration & Deployment Utilities

- `utils/model_config.py`: Creates a configuration with a remote AI API (`/v2/lm/configurations`).
- `utils/model_deployment.py`: Deploys a configuration (`/v2/lm/deployments`).
- Likely used in a provisioning workflow (not yet exposed via API endpoints).

---

## External Integrations

| Integration | Purpose | Notes |
|-------------|---------|-------|
| Supabase (`supabase_connection.py`) | Download files from storage bucket | Needs `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
| SAP HANA / Vector DB (`hana_db_connection` placeholder) | Store embeddings & similarity searches | Functions referenced: `insert_embedding`, `batch_insertion_embedding`, `search_similiar_documents`, `get_all_data` |
| OAuth Token (`utils.oauth_token`) | Access token for AI API | Used by `/api/genai/token` |
| GenAI Hub / OpenAI Proxy (`gen_ai_hub.proxy.native.openai`) | LLM & Embeddings | Abstraction layer for multiple models |

---

## Environment Variables

Create a `.env` file (example):

```
# Flask / Server
PORT=5000

# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# AI Platform
AI_API_URL=https://your-ai-api-base
AI_RESOURCE_GROUP=demo

# Auth / Tokens (examples — adapt to your real naming)
GENAI_API_KEY=...
OPENAI_API_KEY=...
OAUTH_CLIENT_ID=...
OAUTH_CLIENT_SECRET=...
OAUTH_TOKEN_URL=...

# Database (HANA / Vector Store)
HANA_HOST=...
HANA_PORT=...
HANA_USER=...
HANA_PASSWORD=...
HANA_SCHEMA=...
```

(Adjust to the actual variable names used in missing modules.)

---

## Installation & Local Development

Prerequisites:
- Python 3.10+
- (Optional) SAP HANA client / driver libraries installed
- (Optional) Supabase credentials
- (Optional) Proper AI platform access

Steps:
```
git clone https://github.com/kunal-kumar-chaudhary/AI_FLASK_SERVICE.git
cd AI_FLASK_SERVICE

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt  # (Assuming this file exists; create if not)
cp .env.example .env  # populate with real values
python app.py
```

The service listens on `PORT` (defaults to 5000 if unset).

---

## Suggested Directory Structure (Observed / Inferred)

```
AI_FLASK_SERVICE/
├── app.py
├── api/
│   ├── __init__.py
│   ├── document.py
│   ├── genai_hub.py
│   └── RAG_pipeline.py
├── utils/
│   ├── LLM.py
│   ├── document_processing.py
│   ├── supabase_connection.py
│   ├── model_config.py
│   ├── model_deployment.py
│   ├── embedding.py                # (not listed, inferred)
│   ├── hana_db_connection.py       # (not listed, inferred)
│   ├── oauth_token.py              # (not listed, inferred)
│   └── ...
└── requirements.txt (add if missing)
```

---

## Data Flow: RAG Chat Endpoint

1. Client posts query → `/api/rag-pipeline/chat`
2. Embed query → `get_embedding`
3. Retrieve similar documents → `search_similiar_documents`
4. Concatenate retrieved texts → context
5. Build augmented prompt → LLM
6. Generate final response → return JSON

---

## Known Issues / Code Review Notes

| Area | Issue | Recommendation |
|------|-------|----------------|
| `api/document.py` | Duplicate route decorator; `methods=['']` invalid | Remove second decorator or specify proper HTTP methods |
| `api/genai_hub.py` (`search_documents`) | Uses `request.json()` instead of `request.get_json()` | Replace with `request.get_json()` |
| | Variable mismatch: `username_filter` vs `username` when filtering | Standardize variable naming |
| | Calls `search_similiar_documents(query=query, k=k, username=username)` but earlier parameter naming in RAG uses `query_embedding` | Align function signatures (decide on embedding vs raw text) |
| | Spelling: "similiar" | Rename to `search_similar_documents` (function + route) |
| `/create-store-embedding` | Metadata created but not passed into thread (`process_and_embed_file_from_url` accepts only `file_url`) | Extend function signature and pass metadata |
| Threading | Fire-and-forget thread; no error callback | Consider a task queue (Celery / RQ) or logging of failures |
| Embeddings persistence | Embedding stored as `str(embedding_vector)` | Prefer binary / JSON / array columns; ensure consistent decoding for search |
| RAG pipeline | No source citation returned | Return list of chunk IDs / metadata for transparency |
| Security | No auth or rate limiting on endpoints | Add authentication (token / JWT) + throttling |
| Error handling | Generic `except Exception as e` → 500 with string | Standardize error schema & logging |
| Input validation | Limited schema checking | Introduce pydantic / marshmallow models |
| Observability | Minimal logging; no correlation IDs | Add structured logging (JSON) and request IDs |
| Testing | No tests present | Add unit + integration tests (pytest) |
| Config | Scattered `os.getenv` calls | Centralize configuration module |

---

## Extending the Service

Potential enhancements:
1. Add `/api/genai/status` endpoint for background job tracking.
2. Implement source attribution in RAG responses:
   - Return list of `(chunk_index, similarity_score, source_url)`.
3. Add hybrid search (semantic + keyword).
4. Pluggable embedding backends (OpenAI, HuggingFace, Azure).
5. Caching layer (Redis) for repeated queries.
6. Streaming responses for large LLM outputs.
7. Structured prompt templates with variable injection + guardrails.
8. Add retry/backoff and circuit breaker around external API calls.

---

## Example Requests

Create & store embeddings:
```
POST /api/genai/create-store-embedding
Content-Type: application/json

{
  "file_url": "https://your-supabase-url/storage/v1/object/public/docs/sample.pdf",
  "username": "alice",
  "doc_type": "policy"
}
```

RAG chat:
```
POST /api/rag-pipeline/chat
Content-Type: application/json

{
  "query": "Summarize the policy document",
  "k": 4,
  "temperature": 0.2
}
```

---

## Deployment Considerations

| Concern | Recommendation |
|---------|----------------|
| Gunicorn / Production Server | Wrap Flask app with Gunicorn / uvicorn workers (if ASGI migration) |
| Concurrency | Replace raw threads with a task queue for robust scaling |
| Containerization | Provide Dockerfile + multi-stage build |
| Secrets | Use a secret manager (GCP Secret Manager / AWS Secrets Manager) |
| Migrations | If DB schema evolves, adopt Alembic or similar |
| Monitoring | Integrate Prometheus metrics & health checks |

---

## Troubleshooting

| Symptom | Possible Cause | Fix |
|---------|----------------|-----|
| 500 on embedding creation | Missing env vars / DB connection failure | Verify `.env` + DB credentials |
| Empty RAG answers | No documents retrieved / embedding mismatch | Check embedding model consistency |
| Token endpoint failure | OAuth provider unreachable | Validate network + credentials |
| Slow ingestion | Large file + single-threaded processing | Increase worker pool / chunk size tuning |

---

## License

(Choose a license, e.g. MIT, Apache-2.0, add a `LICENSE` file.)

---

## Contributing

1. Fork + branch (`feat/your-feature`)
2. Write tests
3. Open PR with clear description
4. Ensure endpoints follow consistent error schema

---

## Roadmap (Suggested)

- [ ] Fix route & parameter naming inconsistencies
- [ ] Add source citations to RAG responses
- [ ] Introduce authentication & rate limiting
- [ ] Add Dockerfile + CI pipeline
- [ ] Implement retry logic & structured logging
- [ ] Add unit/integration tests
- [ ] Support streaming LLM responses
- [ ] Provide OpenAPI/Swagger spec
- [ ] Implement background job queue
- [ ] Add evaluation harness for RAG quality
