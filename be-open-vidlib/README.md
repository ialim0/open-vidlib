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
    reindex.py          Rebuild bundled transcript chunks and embeddings
    seed.py             Idempotent seed: videos, transcripts, embeddings, flashcards
    seed_data/          JSON transcript files and flashcard banks
  models/               SQLAlchemy ORM models
  schemas/              Pydantic v2 I/O schemas (one file per feature area)
  services/
    ingest_service.py   Caption chunking and mistral-embed batch embedding
    search_service.py   Hybrid pgvector + lexical retrieval with RRF and fallback
    rag_qa_service.py   Grounded Q&A with evidence selection and citations
    translation_service.py  Speech-optimised translation
    tts_service.py      Voxtral TTS audio generation
    dubbing_service.py  Orchestrates translation + TTS → AudioDub records
    agent_router.py     Mistral tool calling — routes intent to the right service
    video_service.py    Video CRUD helpers
  main.py               App factory (CORS, static files, lifespan)
tests/                  pytest suite
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

## Search and AI pipeline

### 1 — Ingestion (`POST /api/v1/videos/{id}/ingest`)

```
captions list  →  clean text and build overlapping sentence-aware windows (420 target / 650 max chars)
               →  batch embed with mistral-embed (1024-dim)
               →  replace the video/language index in video_segments
```

The chunker targets 420 characters, never exceeds 650 characters, preserves timestamps, and overlaps up to two captions so concepts spanning a boundary remain retrievable.

### 2 — Semantic search (`POST /api/v1/videos/{id}/search`)

```
query string  →  embed with mistral-embed (when configured)
              →  retrieve vector candidates from pgvector and lexical candidates with IDF/TF scoring
              →  reciprocal-rank fusion → near-duplicate reduction → timestamped results
```

Falls back to deterministic embeddings and in-memory cosine scoring when Mistral or pgvector is unavailable. Lexical matching remains available for exact terms.

### 3 — RAG Q&A (`POST /api/v1/videos/{id}/ask`)

```
question + recent question context  →  top-8 fused chunks
          →  remove duplicate evidence and cap the context window
          →  strict grounded prompt: answer only from transcript and cite [MM:SS]
          →  mistral-large-latest (low temperature)
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

## Rebuilding the bundled search index

Run this after changing chunking, embedding, or retrieval behavior:

```bash
# from the repository root
docker compose exec api python -m app.db.reindex
```

The command replaces the indexed segments for the four bundled videos while preserving video metadata and the database volume. With `MISTRAL_API_KEY`, it creates real `mistral-embed` vectors; without a key it creates deterministic development vectors, so lexical retrieval still works but semantic quality is limited.

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

The test suite is designed to run against an in-memory SQLite database without a Mistral key or PostgreSQL instance. Embedding and TTS services provide deterministic fallbacks for local development and tests.

---

## Code style

- Python: `black` (88-char line length), `ruff` for lint
- Type hints on all public functions
- No `print()` — use the module-level `logger`
- Keep service files focused: one concern per file
