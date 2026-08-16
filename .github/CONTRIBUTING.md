# Contributing to GandaLab

Thank you for looking at this. Every contribution matters — a new video, a bug fix, a typo correction.

---

## Getting started

1. Fork the repository and clone your fork.
2. Follow the local development setup in the root [README](../README.md).
3. Create a branch: `git checkout -b fix/your-description` or `feat/your-description`.
4. Make your change.
5. Run the test suite: `cd be-open-vidlib && PYTHONPATH=. pytest -v tests/`.
6. Run the TypeScript check: `cd fe-open-vidlib && npx tsc --noEmit`.
7. Open a pull request.

---

## Good first issues

If you are not sure where to start:

- **Add a video** — add a new YouTube lesson and its transcript file to `be-open-vidlib/app/db/seed_data/`. See the existing files for the format.
- **Add a language** — add a new voice preset in `be-open-vidlib/app/core/voice_presets.py` and a button in `fe-open-vidlib/app/library/[id]/resource-page-client.tsx`.
- **Write a test** — the `tests/` folder always has room for more cases, especially for the Mistral service fallbacks.
- **Fix a bug** — check open issues.

---

## Code style

- Python: `black` + `ruff`. No `print()`, use `logging`.
- TypeScript: default Next.js ESLint config.
- Commit messages: short imperative subject line, e.g. `fix: handle empty transcript in search_service`.

---

## Submitting a video

A video needs:
1. A public YouTube URL.
2. A word-level transcript: a JSON file with the shape `{ "words": [{ "word": "...", "start": 0.0, "end": 0.5 }, ...] }`.

You can generate the transcript with any ASR tool (OpenAI Whisper, faster-whisper, etc.).  
Place the file in `be-open-vidlib/app/db/seed_data/` and follow the naming convention there.

---

## Questions?

Open a GitHub Discussion or an issue. There is no Slack or Discord yet — maybe once the community grows.
