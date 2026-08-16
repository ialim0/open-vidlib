# be-open-vidlib — Open VidLib API

FastAPI backend for the Open VidLib video platform.  
Handles video metadata, transcripts, flashcards, and all Mistral AI features.

---

## Layout

```
app/
  api/v1/endpoints/     One file per resource group
  core/
    config.py           All settings loaded from env / .env
    database.py         SQLAlchemy engine and session factory
    mistral_client.py   Lazy singleton — returns None if no key set
    voice_presets.py    Language → Voxtral voice ID mapping
  db/
    init_db.py          Table creation + seed trigger
    seed.py             Idempotent seed: videos, transcripts, embeddings, flashcards
    seed_data/          JSON transcript files and flashcard banks
  models/               SQLAlchemy ORM models
  schemas/              Pydantic v2 I/O schemas (one file per feature area)
  services/
    ingest_service.py   Caption chunking and mistral-embed batch embedding
    search_service.py   pgvector cosine similarity search with Python fallback
    rag_qa_service.py   Grounded Q&A via mistral-large-latest
    translation_service.py  Speech-optimised translation
    tts_service.py      Voxtral TTS audio generation
    dubbing_service.py  Orchestrates translation + TTS → AudioDub records
    agent_router.py     Mistral tool calling — routes intent to the right service
    video_service.py    Video CRUD helpers
  main.py               App factory (CORS, static files, lifespan)
tests/                  pytest suite (17 tests, no external services required)
```

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env   # then fill in DATABASE_URL and MISTRAL_API_KEY
uvicorn app.main:app --reload
```

The app needs a running PostgreSQL instance with the pgvector extension.  
The easiest way is `docker compose up db` from the project root.

---

## Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `DATABASE_URL` | yes | — | PostgreSQL connection string |
| `MISTRAL_API_KEY` | no | `""` | Without this, AI features return deterministic fallbacks |
| `MISTRAL_EMBED_MODEL` | no | `mistral-embed` | |
| `MISTRAL_LLM_MODEL` | no | `mistral-large-latest` | |
| `MISTRAL_TTS_MODEL` | no | `voxtral-mini-tts-2603` | |
| `CORS_ORIGINS` | no | `http://localhost:3000` | Comma-separated |

---

## How the Mistral pipeline works

### 1 — Ingestion (`POST /api/v1/videos/{id}/ingest`)

```
captions list  →  chunk by ~500 chars preserving timestamps
               →  batch embed with mistral-embed (1024-dim)
               →  upsert into video_segments table (pgvector column)
```

The chunker tries to end chunks at sentence boundaries before the 500-char limit.

### 2 — Semantic search (`POST /api/v1/videos/{id}/search`)

```
query string  →  embed with mistral-embed
              →  pgvector: SELECT ... ORDER BY embedding <=> $query_vec LIMIT k
              →  return [{text, start_time, end_time, similarity}, ...]
```

Falls back to in-memory cosine math when running against SQLite (tests).

### 3 — RAG Q&A (`POST /api/v1/videos/{id}/ask`)

```
question  →  top-4 chunks from semantic search
          →  system prompt: answer using only the context, cite [MM:SS]
          →  mistral-large-latest
          →  {answer, sources, video_id}
```

Conversation history is persisted in the `qa_sessions` table.

### 4 — Dubbing (`POST /api/v1/videos/{id}/dub`)

```
video segments  →  translate each with mistral-large (spoken-optimised prompt)
                →  voxtral-mini-tts for each translated chunk
                →  write mp3 to static/dubs/{video_id}/{lang}/
                →  upsert AudioDub records
```

Dubbed tracks are served as static files at `/static/dubs/...`.

### 5 — Agent router (`POST /api/v1/videos/{id}/agent-chat`)

Three Mistral tools are registered: `search_video`, `ask_question`, `translate_dub`.  
The model picks one (or none for general chat). The router then calls the right service.  
Falls back to keyword heuristics when no API key is present.

---

## Database models

| Table | Purpose |
|---|---|
| `videos` | Video metadata (id, title, category, YouTube URL, …) |
| `transcripts` | Full text + word-level JSON (`{word, start, end}[]`) |
| `flashcards` | MCQ questions per video per language |
| `video_chat_messages` | Conversation history for the basic chat endpoint |
| `video_segments` | Chunked transcript text + `vector(1024)` embedding |
| `audio_dubs` | Path to generated mp3, start/end timestamps, language |
| `qa_sessions` | Full message history for RAG Q&A sessions |

---

## Tests

```bash
PYTHONPATH=. pytest -v tests/
```

All 17 tests run against an in-memory SQLite database — no Mistral key or
PostgreSQL instance required. The embedding and TTS services use deterministic
fallbacks during testing.

---

## Code style

- Python: `black` (88-char line length), `ruff` for lint
- Type hints on all public functions
- No `print()` — use the module-level `logger`
- Keep service files focused: one concern per file
