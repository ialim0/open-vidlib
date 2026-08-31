# Reproducing the agent comparison

## Requirements

- Docker Engine 24+ with Compose v2
- Python 3.10+ only for the standard-library evaluation client
- An LLM & Embedding API key:
  - **Mistral AI (Default):** `MISTRAL_API_KEY` (models: `mistral-small-latest`, `mistral-embed`, voice: `voxtral-mini-tts-2603`)
  - **Google Gemini (Optional Alternative):** `GEMINI_API_KEY` (models: `gemini-2.5-flash`, embeddings: `gemini-embedding-2`)
  - **OpenAI (Optional Alternative):** `OPENAI_API_KEY` (models: `gpt-4o-mini`, embeddings: `text-embedding-3-small`)
  - **Ollama / Custom OpenAI-compatible:** `LLM_PROVIDER=custom`, `LLM_BASE_URL=...`
- No additional service: PostgreSQL + pgvector is included in Compose

## Clean checkout

```bash
git clone https://github.com/ialim0/open-vidlib.git
cd open-vidlib
cp .env.example .env
```

Set `MISTRAL_API_KEY` in `.env`; do not commit it. Optional controls are `AGENT_MAX_STEPS` (default and enforced value: 6) and `AGENT_MEMORY_TURNS` (default: 4).

Host port mappings are fully configurable via environment variables (`POSTGRES_PORT`, `API_PORT`, `WEB_PORT`). If your local port 5432 is already bound by another PostgreSQL instance, set `POSTGRES_PORT=55432` in `.env` (or pass `POSTGRES_PORT=55432 docker compose up`). In this test environment, host port `55432` is used for Postgres (`0.0.0.0:55432->5432/tcp`), while internal container-to-container networking remains unchanged.

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/api/v1/health
```

On first startup the database seeds `video-0` (gravity), `video-2` (pyramid engineering), and `video-3` (Pythagoras). Wait for the API health response before evaluating.

## Run each implementation

All requests use the same endpoint, video, payload, database, and tool services with `?mode=baseline`, `?mode=loop`, or `?mode=orchestrated`:

```bash
# 1. Baseline (single-shot legacy router)
curl -sS -X POST 'http://localhost:8000/api/v1/videos/video-0/agent-chat?mode=baseline' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Find where Newton is introduced, then explain his connection to gravity.","session_id":"demo-baseline"}'

# 2. Agent Loop (multi-step tool loop with verification & retry)
curl -sS -X POST 'http://localhost:8000/api/v1/videos/video-0/agent-chat?mode=loop' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Find where Newton is introduced, then explain his connection to gravity.","session_id":"demo-loop"}'

# 3. Question Decomposition Orchestrator (sub-question dispatch & composite verification)
curl -sS -X POST 'http://localhost:8000/api/v1/videos/video-0/agent-chat?mode=orchestrated' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Find where Newton is introduced, then explain his connection to gravity.","session_id":"demo-orch"}'
```

The baseline reports `mode: "baseline"` and makes at most one tool call. The loop reports `mode: "loop"`, `tool_call_count`, `verified`, `degraded`, and a `trajectory_id`. The orchestrator reports `mode: "orchestrated"`, decomposes multi-part queries, dispatches sub-questions through the loop, synthesizes results, and preserves sub-trajectories. Each request writes JSON logs to `be-open-vidlib/trajectories/<trajectory_id>.json`.

## Run the fixed evaluation

```bash
python3 eval/run_eval.py
```

The script evaluates the 10 fixed cases across modes, preserves sessions across the setup/follow-up pair, prints a comparison Markdown table, and writes `eval/results.md`. A correct citation must match the start time of evidence returned in that same response. Expected healthy output has successful requests, nonzero tool-call counts, and `degraded fallback 0/10`.

If the key is absent, invalid, rate-limited, or cannot access the configured model, the API deliberately falls back instead of returning a hallucination or 500. Those runs report `degraded: true`, record a `model_error` trajectory event, and must not be presented as live multi-step-model evidence.

## Tests and cleanup

```bash
docker compose exec api pytest -q tests/test_agent_chat_loop.py
docker compose down
```

`docker compose down` keeps seeded database and trajectory files. Use `docker compose down -v` only when intentionally deleting the database volume.
