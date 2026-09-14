# Architecture Specification: Lenny Growth Assistant

## 1. High-Level System Component Diagram

```
+-----------------------------------------------------------------------------------+
|                                  BROWSER CLIENT                                   |
|   +-------------------------------------+   +---------------------------------+   |
|   |         React Chat UI (Vite)        |   |     Artifact Viewer (Split)     |   |
|   |  - Session Switcher                 |   |  - React Markdown (Sanitized)   |   |
|   |  - Citation Accordion               |   |  - Sandboxed <iframe srcdoc>    |   |
|   +----------------------------------+--+   +---------------------------------+   |
+--------------------------------------|--------------------------------------------+
                                       | HTTP / REST (JSON)
                                       v
+-----------------------------------------------------------------------------------+
|                                 FASTAPI BACKEND                                   |
|   +-------------------+   +--------------------+   +--------------------------+   |
|   | Sessions & Chat   |   | Ingestion Engine   |   | Agent Intent Router &    |   |
|   | API Router        |   | & Retriever        |   | Ship 30 Essay Skill      |   |
|   +---------+---------+   +---------+----------+   +------------+-------------+   |
|             |                       |                           |                 |
|             +-----------------------+---------------------------+                 |
|                                     |                                             |
|                   +-----------------+-----------------+                           |
|                   |  LLM Provider Layer (Abstraction) |                           |
|                   |  - Anthropic / OpenAI / Ollama    |                           |
|                   |  - Runtime Model Toggle & Failover|                           |
|                   +--------+-----------------+--------+                           |
+----------------------------|-----------------|------------------------------------+
                             |                 |
                +------------+                 +------------+
                v                                           v
+-----------------------------------+       +-----------------------------------+
|      POSTGRESQL + PGVECTOR        |       |        OLLAMA LOCAL RUNTIME       |
|  - sessions / messages / metadata |       |  - llama3.2 / mistral model       |
|  - transcript_chunks (embeddings) |       |  - local embeddings / inference   |
+-----------------------------------+       +-----------------------------------+
```

## 2. Database Schema (SQLAlchemy Models / PostgreSQL DDL)

### PostgreSQL Extension
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
```

### Table DDL Definitions
```sql
-- User Metadata Table
CREATE TABLE user_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sessions Table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_metadata(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    provider_preference VARCHAR(50) DEFAULT 'anthropic',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Message Metadata Table (Citations & Artifact Tracking)
CREATE TABLE message_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID UNIQUE NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    citations JSONB DEFAULT '[]'::jsonb, -- Array of {episode_title, timestamp, chunk_id, score}
    artifact JSONB DEFAULT NULL,         -- {type: 'markdown'|'html', title: text, content: text}
    provider_used VARCHAR(50),
    model_used VARCHAR(100),
    latency_ms INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transcript Chunks & Vector Store Table
CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    episode_id VARCHAR(100) NOT NULL,
    episode_title VARCHAR(255) NOT NULL,
    episode_url VARCHAR(500),
    guest_name VARCHAR(255),
    timestamp_start VARCHAR(50),
    timestamp_end VARCHAR(50),
    content TEXT NOT NULL,
    embedding vector(1536), -- Vector size matching selected embedding model
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW Vector Index for fast cosine similarity search
CREATE INDEX idx_transcript_chunks_embedding ON transcript_chunks 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

## 3. API Endpoints & Standard Error Envelope

### Standard Error Response Envelope
Every non-2xx API error returns a unified error envelope format:
```json
{
  "error": {
    "code": "PROVIDER_UNAVAILABLE",
    "message": "The configured Anthropic API key is missing or invalid.",
    "detail": "Failed to authenticate with provider anthropic. OLLAMA_FALLBACK is enabled, falling back to Ollama.",
    "timestamp": "2026-09-14T22:53:10Z"
  }
}
```

### Route Summary
| Route | Method | Request Body | Response Body | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | GET | None | `HealthCheckResponse` | Returns detailed status of DB, LLM Provider, and Ollama. |
| `/sessions` | POST | `SessionCreateRequest` | `SessionResponse` | Create a new chat session. |
| `/sessions` | GET | None | `List[SessionResponse]` | List all chat sessions. |
| `/sessions/{id}` | GET | None | `SessionResponse` | Get session details. |
| `/sessions/{id}` | DELETE | None | `{"status": "deleted"}` | Delete session and associated messages. |
| `/sessions/{id}/messages` | GET | None | `List[MessageResponse]` | Fetch all messages and metadata for a session. |
| `/sessions/{id}/messages` | POST | `MessageCreateRequest` | `MessageResponse` | Post user message, triggers RAG/Agent flow & returns assistant message. |
| `/sessions/{id}/essay` | POST | `EssayGenerateRequest` | `MessageResponse` | Explicit trigger to generate a Ship 30 for 30 essay artifact. |

## 4. Ingestion & Retrieval Pipeline

```
Raw Transcripts (.txt / .json / .vtt)
              │
              ▼
   Chunking Processor (Semantic Paragraph Split, 500 words, 50 word overlap)
              │
              ▼
   Metadata Attacher (Episode Title, Guest, Timestamp Start/End, Episode URL)
              │
              ▼
   Embedding Engine (Local sentence-transformers / Ollama nomic-embed-text / OpenAI)
              │
              ▼
   Idempotent Indexing in PostgreSQL `transcript_chunks` (SHA256 Content Hash Check)
              │
              ▼
   RAG Vector Query (Top-k Cosine Similarity via pgvector HNSW Index)
```

## 5. Agent Intent Routing & Skill Pipeline

When a user submits a message to `POST /sessions/{id}/messages`:
1. **Intent Classification:** The system evaluates user input via lightweight regex / keyword pattern matching or LLM routing:
   - **`GROUNDED_QA` (Default):** Standard grounded retrieval & citation generator.
   - **`SHIP30_ESSAY`:** User asks to "write an essay", "create a Ship 30 essay", or posts to `/sessions/{id}/essay`.
   - **`CREATE_ARTIFACT`:** User explicitly requests HTML/CSS code sandbox or standalone Markdown document artifact.
2. **Skill Execution:**
   - For `GROUNDED_QA`: Fetches top-$k=4$ chunks $\rightarrow$ generates answer with citations.
   - For `SHIP30_ESSAY`: Runs `Ship30EssaySkill` system prompt $\rightarrow$ consumes grounded context $\rightarrow$ outputs formatted ~1,250 word Markdown essay marked as an `artifact`.

## 6. Model Toggle & Resilience Strategy

- **Configuration:** Driven by environment variables (`LLM_PROVIDER`, `LLM_MODEL`, `OLLAMA_HOST`, `OLLAMA_FALLBACK`).
- **Supported Providers:**
  - `anthropic`: `AnthropicProvider` (Claude 3.5 Sonnet / Haiku).
  - `openai`: `OpenAIProvider` (GPT-4o / GPT-4o-mini).
  - `ollama`: `OllamaProvider` (llama3.2 / mistral / qwen2.5).
- **Fallback Logic:** Implemented in `backend/app/llm/factory.py`. If primary provider (e.g. `anthropic`) fails due to timeout, rate limit, or invalid API key, `generate_with_fallback()` logs structured error warnings and transparently falls back to `OllamaProvider` if `OLLAMA_FALLBACK=true`.
- **UI Config Exposure:** Exposed via `GET /config` and `GET /health` endpoints so the frontend displays active execution mode in real time.


## 7. Security: Artifact Isolation & HTML Sandboxing

### Threat Model
Generated HTML artifacts could contain malicious inline scripts, attempt cookie theft, access `localStorage`, or make forged network requests to the backend API (`same-origin`).

### Mitigation Strategy
1. **Sanitization:** All HTML content is sanitized on the client using `DOMPurify` before insertion.
2. **Iframe Sandboxing:** Rendered in an `<iframe>` with strict sandbox flags:
   ```html
   <iframe sandbox="allow-scripts" srcdoc="..."></iframe>
   ```
   - **`allow-same-origin` is EXCLUDED:** Ensures the iframe runs in a unique `null` origin, completely preventing access to `window.parent`, cookies, `localStorage`, `sessionStorage`, or same-origin API requests.
   - **`allow-forms` is EXCLUDED:** Prevents unauthorized form submissions.
   - **CSP Header:** Synthetic Content Security Policy injected inside `srcdoc`:
     `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';">`

## 8. Deployment Topology (Docker Compose)

The full application stack is orchestrated via `docker-compose.yml`:
- **`db`:** PostgreSQL 16 with `pgvector/pgvector:pg16` extension pre-enabled.
- **`ollama`:** Ollama service running `llama3.2` model.
- **`backend`:** FastAPI application exposed on port `8000`. Wait-for healthcheck dependency on `db` and `ollama`.
- **`frontend`:** React (Vite) production server exposed on port `3000`.
