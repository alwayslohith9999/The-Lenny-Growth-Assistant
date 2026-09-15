# System Architecture: Lenny Growth Assistant

Comprehensive technical architecture specification detailing system topology, component interactions, data models, resilience patterns, and security guarantees.

---

## 1. High-Level Architecture (C4 Container Diagram)

```mermaid
graph TD
    Client["User Browser (React 18 SPA)"]
    
    subgraph Frontend ["Frontend Container (Port 3000)"]
        UI["React SPA (Vite + Nginx)"]
        MD["ReactMarkdown + GFM Engine"]
        Viewer["Secure Artifact Viewer (Sandboxed iframe)"]
    end
    
    subgraph Backend ["Backend Container (Port 8000)"]
        API["FastAPI 0.110+ Application"]
        MW["Middlewares: RequestID, Structured Logs, CORS"]
        Router["Routers: Health, Sessions, Messages"]
        RAG["RAGService (Vector + Keyword Search)"]
        Skill["Ship30EssaySkill Engine"]
        LLM["LLMService (Tiered Provider Factory)"]
    end
    
    subgraph Storage ["Persistence & External Services"]
        PG[("PostgreSQL 16 + pgvector")]
        SQLite[("SQLite Local / In-Memory Fallback")]
        Ollama["Local Ollama Runtime (Port 11434)"]
        Cloud["Cloud Providers (Anthropic / OpenAI)"]
    end
    
    Client -->|HTTP / JSON| UI
    UI -->|REST API Requests| API
    API --> MW
    MW --> Router
    Router --> RAG
    Router --> Skill
    Skill --> LLM
    RAG --> LLM
    
    Router -->|ORM / SQL| PG
    Router -.->|Zero-Config Fallback| SQLite
    LLM -->|Primary Cloud API| Cloud
    LLM -.->|Local Secondary| Ollama
    LLM -.->|Offline Tertiary| Backend
```

---

## 2. Component Directory Structure

```
oogway/
├── backend/
│   ├── app/
│   │   ├── routers/          # Modular API route controllers
│   │   │   ├── health.py     # System health and runtime config
│   │   │   ├── sessions.py   # Conversation session CRUD
│   │   │   └── messages.py   # Grounded RAG & essay generation
│   │   ├── services/         # Business logic layer
│   │   │   ├── rag_service.py # Vector embedding & hybrid retrieval
│   │   │   └── llm_service.py # LLM execution with timing telemetry
│   │   ├── skills/           # Agentic writing & analysis skills
│   │   │   ├── base.py       # Abstract BaseSkill interface
│   │   │   └── ship30_essay.py # Ship 30 for 30 essay generator
│   │   ├── llm/              # Tiered LLM provider abstraction
│   │   │   ├── base.py       # BaseLLMProvider interface
│   │   │   ├── anthropic.py  # Anthropic Claude 3.5 Sonnet client
│   │   │   ├── openai.py     # OpenAI GPT-4o client
│   │   │   ├── ollama.py     # Ollama local runtime client
│   │   │   └── factory.py    # Tiered fallback factory & offline synthesizer
│   │   ├── middleware/       # ASGI request processing
│   │   │   └── request_id.py # X-Request-ID & security headers
│   │   ├── config.py         # Pydantic BaseSettings environment config
│   │   ├── database.py       # SQLAlchemy engine & session factory
│   │   ├── errors.py         # Standardized error envelope handlers
│   │   ├── models.py         # SQLAlchemy ORM database models
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   └── main.py           # FastAPI application entrypoint & lifespan
│   ├── Dockerfile            # Multi-stage hardened Python container
│   └── requirements.txt      # Pinned production dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   │   ├── ChatWindow.jsx    # Chat feed, markdown rendering, citations
│   │   │   ├── Sidebar.jsx       # Session navigation & mobile drawer
│   │   │   ├── ArtifactViewer.jsx # Dual-mode split pane viewer
│   │   │   ├── ToastProvider.jsx # Toast notification context
│   │   │   └── ErrorBoundary.jsx # React crash prevention boundary
│   │   ├── api.js            # Typed API client with structured error handling
│   │   ├── App.jsx           # Root layout and application state orchestrator
│   │   ├── index.css         # Responsive styling & WCAG AA design system
│   │   └── main.jsx          # React DOM mounting entry point
│   ├── nginx.conf            # Production Nginx SPA configuration
│   └── Dockerfile            # Multi-stage Node build -> Nginx runtime
├── ingestion/
│   ├── chunker.py            # Transcript segmentation & token overlap
│   ├── embedder.py           # Deterministic L2-normalized vector encoder
│   ├── retriever.py          # Vector + keyword search helper
│   ├── ingest.py             # Batch transcript ingestion pipeline
│   └── transcripts/          # Curated source transcript files
├── tests/                    # Comprehensive automated test suite
│   ├── conftest.py           # In-memory SQLite fixtures & seed data
│   ├── test_sessions.py      # Session CRUD tests
│   ├── test_messages.py      # Conversational RAG & citation tests
│   ├── test_essay.py         # Ship 30 essay skill generation tests
│   ├── test_retriever.py     # Vector math & determinism tests
│   ├── test_llm_providers.py # Provider routing & fallback tests
│   ├── test_error_handling.py # Schema validation & security header tests
│   └── test_ingestion.py     # Ingestion & chunking primitive tests
├── docker-compose.yml        # Multi-container orchestration topology
└── run.bat                   # Zero-dependency Windows local launch script
```

---

## 3. Data Architecture & Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    UserMetadata ||--o{ Session : owns
    Session ||--o{ Message : contains
    Message ||--o| MessageMetadata : has
    
    Session {
        string id PK
        string user_id FK
        string title
        string provider_preference
        datetime created_at
        datetime updated_at
    }
    
    Message {
        string id PK
        string session_id FK
        string role
        text content
        datetime created_at
    }
    
    MessageMetadata {
        string id PK
        string message_id FK
        json citations
        json artifact
        string provider_used
        string model_used
        int latency_ms
        int prompt_tokens
        int completion_tokens
    }
    
    TranscriptChunk {
        string id PK
        string episode_id
        string episode_title
        string guest_name
        string timestamp_start
        string timestamp_end
        string episode_url
        text content
        json embedding
        datetime created_at
    }
```

---

## 4. Dual-Mode Storage Strategy

To guarantee both **enterprise production capability** and **instant zero-dependency evaluator onboarding**, the system implements a dual-mode storage pattern:

| Capability | Production Mode (Docker Compose) | Local & Evaluator Mode (`run.bat` / pytest) |
| :--- | :--- | :--- |
| **Engine** | PostgreSQL 16 (`pgvector/pgvector:pg16`) | SQLite (`lenny_growth.db` or `:memory:`) |
| **Connection** | `postgresql://postgres:postgres@postgres:5432/...` | `sqlite:///./lenny_growth.db` |
| **Vector Search** | Deterministic 384-dim embeddings + keyword score | In-memory cosine similarity + keyword overlap |
| **Setup Cost** | Requires Docker daemon | Zero dependencies (pure Python standard lib) |
| **Data Safety** | Docker named volumes (`postgres_data`) | Local file persistence with auto-schema migration |

---

## 5. Tiered LLM Provider Architecture & Fallback Flow

```mermaid
flowchart TD
    Req["Incoming Generation Request"] --> Primary{"Is Primary Provider Configured?<br>(Key valid & network ok)"}
    
    Primary -- Yes --> ExecPrimary["Invoke Anthropic / OpenAI"]
    ExecPrimary -- Success --> ResSuccess["Return 200 OK<br>is_fallback=false"]
    
    Primary -- No / Fails --> Fallback1{"Is Ollama Fallback Enabled<br>& Ollama Service Reachable?"}
    ExecPrimary -- Error/Timeout --> Fallback1
    
    Fallback1 -- Yes --> ExecOllama["Invoke Local Ollama<br>(e.g. llama3.2)"]
    ExecOllama -- Success --> ResOllama["Return 200 OK<br>provider=ollama, is_fallback=true"]
    
    Fallback1 -- No / Fails --> Fallback2["Invoke Offline Grounded Synthesizer"]
    ExecOllama -- Error/Timeout --> Fallback2
    
    Fallback2 --> ResOffline["Return 200 OK<br>provider=offline-grounded-fallback<br>is_fallback=true"]
```

---

## 6. Architectural Decision Records (ADRs)

### ADR-001: Dual-Mode Database Engine (PostgreSQL vs. SQLite Fallback)
- **Context:** Requiring PostgreSQL with pgvector for local evaluation risks reviewer failure if Docker is unavailable.
- **Decision:** Implement automatic connection detection in `app/database.py`. If PostgreSQL cannot be reached within initial connection pre-ping, seamlessly bind to local SQLite.
- **Consequences:** Evaluators can run the entire system via `run.bat` or `pytest` without spinning up database containers.

### ADR-002: Deterministic Hash-Based Dense Embedding Model
- **Context:** External embedding APIs (OpenAI `text-embedding-3-small`) require cloud network connectivity and API credits. Python's default `hash()` is randomized across processes via `PYTHONHASHSEED`.
- **Decision:** Implement a deterministic 384-dimensional feature-hashing embedding using `hashlib.md5` and L2 normalization in `rag_service.py`.
- **Consequences:** 100% deterministic vectors across process boundaries with zero external network dependencies and sub-millisecond encoding speed.

### ADR-003: HTML Artifact Sandboxing via Null Origin
- **Context:** Ship 30 essays or interactive growth prototypes generated in HTML could contain script tags that access application credentials or local storage.
- **Decision:** Render HTML artifacts inside `<iframe sandbox="allow-scripts">` while deliberately omitting `allow-same-origin`.
- **Consequences:** The iframe receives a `null` security origin. The browser sandbox prohibits reading parent DOM cookies, `localStorage`, or issuing authenticated API requests to the host application.

### ADR-004: Modular Router + Service Layer Separation
- **Context:** Initial monolithic `app/main.py` mixed HTTP routing, database transactions, RAG context formatting, and skill execution.
- **Decision:** Refactor into `app/routers/` (HTTP controller), `app/services/` (domain business logic), and `app/skills/` (agentic prompting modules).
- **Consequences:** Code adheres to Single Responsibility Principle, enables isolated unit testing of services, and eliminates all dynamic `sys.path` tampering.
