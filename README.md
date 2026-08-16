# GandaLab

An open-source educational video platform that pairs YouTube lessons with an AI tutor.  
Students can search any concept inside a video, ask questions grounded in the transcript, and listen to the lesson in their own language — all without leaving the page.

---

## Origin

This project was born at the **AIMS Scientific Innovation Hackathon** (African Institute for Mathematical Sciences, Senegal).  
The first version ran entirely in the browser — no backend, no database, all data in JSON files bundled with the frontend.

After the hackathon I spent one weekend adding:
- A proper FastAPI backend with PostgreSQL
- pgvector for semantic search over transcripts
- Mistral AI for RAG Q&A, translation, and Voxtral text-to-speech dubbing

The goal is to make high-quality STEM content navigable and accessible in West African languages (Wolof, Pulaar, Bambara) and beyond.

---

## What it does

| Feature | How |
|---|---|
| **Video library** | Curated YouTube lessons in Science, Technology, Engineering, Mathematics — shown directly on the landing page |
| **Word-level captions** | Click any word in the transcript to jump to that moment in the video |
| **Semantic search** | Type a concept → find the exact timestamps where it appears (`mistral-embed` + pgvector cosine distance) |
| **RAG Q&A** | Ask Coumba (the AI tutor) a question → grounded answer with `[MM:SS]` citations (`mistral-large-latest`) |
| **AI dubbing** | Translate the lesson and generate a voice track in French, Spanish, Wolof, Pulaar, or Bambara (`voxtral-mini-tts`) |
| **Flashcard quiz** | Auto-generated multiple-choice questions from the transcript |

The app is fully usable without a Mistral key — every AI feature degrades gracefully to keyword heuristics or cached seed data.

---

## Architecture

```
fe-gandalab/          Next.js 14 frontend
be-gandalab/          FastAPI backend
  app/
    api/v1/           REST endpoints
    core/             Settings, Mistral client singleton
    db/               SQLAlchemy engine, seed pipeline
    models/           ORM models
    schemas/          Pydantic v2 schemas
    services/         Business logic (one file per concern)
  tests/              pytest suite
docker-compose.yml    PostgreSQL (pgvector) + API + web
```

### Mistral pipeline

```
captions (JSON)  →  chunk ~500 chars  →  mistral-embed (1024-dim)  →  pgvector
                                                                         ↓
user query  →  mistral-embed  →  cosine distance  →  top-k chunks  →  mistral-large  →  answer
                                                                         ↓
                                                    mistral-large (translate)  →  voxtral TTS  →  mp3
```

---

## API endpoints

All routes are prefixed with `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/videos` | List videos (filter by `category`, `search`) |
| `GET` | `/videos/{id}` | Video detail with transcript and flashcards |
| `POST` | `/videos/{id}/ingest` | Chunk captions and embed into pgvector |
| `POST` | `/videos/{id}/search` | Semantic search — returns ranked timestamped segments |
| `POST` | `/videos/{id}/ask` | RAG Q&A — returns answer + source timestamps |
| `POST` | `/videos/{id}/dub` | Generate translated audio track |
| `GET` | `/videos/{id}/dub/{lang}` | Fetch audio track segments for a language |
| `POST` | `/videos/{id}/agent-chat` | Unified chat — Mistral tool calling routes to search / Q&A / dubbing automatically |
| `GET` | `/transcripts/video/{id}` | Raw transcript words with timestamps |
| `GET` | `/flashcards/video/{id}` | Flashcards for a video |

Interactive docs: `http://localhost:8000/api/v1/docs`

---

## Quickstart

### With Docker

```bash
git clone https://github.com/your-username/gandalab.git
cd gandalab

cp .env.example .env
# optional: add MISTRAL_API_KEY=... to .env

docker compose up --build
```

- Frontend → http://localhost:3000  
- API docs → http://localhost:8000/api/v1/docs

### Local development

**Backend**

```bash
cd be-gandalab

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # set DATABASE_URL and MISTRAL_API_KEY
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd fe-gandalab
npm install
npm run dev
```

**Tests**

```bash
cd be-gandalab
PYTHONPATH=. pytest -v tests/
```

---

## Adding a video

To add a video to the library you need two things:

1. **A YouTube URL** for the lesson.
2. **A transcript file** — a JSON array of `{ word, start, end }` objects (from Whisper or any ASR tool).

Place the transcript in `be-gandalab/app/db/seed_data/` following the naming convention in that folder, then run the seed:

```bash
cd be-gandalab
PYTHONPATH=. python -m app.db.seed
```

The seed script chunks the transcript and writes embeddings to pgvector automatically. You can also call the `/ingest` endpoint at runtime.

---

## Contributing

Contributions are very welcome.

Good first issues:
- Add a new video to the seed library
- Add a new supported language to the dubbing voice presets
- Write a test for an untested endpoint
- Improve the caption chunking heuristic in `ingest_service.py`
- Connect the whisper endpoint so users can submit their own YouTube URLs

Please open an issue before starting any large change so we can discuss the approach.

```bash
# fork → clone → create a branch → open a PR
git checkout -b feat/your-change
```

There is no CLA. MIT licence. Code style: `black` + `ruff` for Python, default Next.js ESLint for TypeScript.

---

## Roadmap

- [ ] Self-hosted ASR (Whisper) so users can transcribe any YouTube URL
- [ ] User accounts and saved notes
- [ ] More West African language voice presets
- [ ] Mobile-first PWA shell
- [ ] Community video submissions

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## ⭐ Show interest

If this project is useful to you, or you think this kind of tool matters for education in Africa or anywhere else, please **star the repository**. It helps others find it and motivates continued work.

If you have ideas, open an issue. If you want to get involved, say hello.
