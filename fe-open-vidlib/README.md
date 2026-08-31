# fe-open-vidlib — Open VidLib Web

Next.js 16 (App Router) frontend for Open VidLib.

---

## Setup

```bash
npm install
cp ../.env.example .env.local    # set NEXT_PUBLIC_API_URL
npm run dev
```

Opens at http://localhost:3000.

---

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend base URL |

---

## Layout

```
app/
  page.tsx                       Landing page — video library grid
  about/page.tsx                 Project overview, technology, and roadmap
  library/[id]/                  Video detail page
    page.tsx                     Server component (fetches video data)
    resource-page-client.tsx     Client shell (player, chat, toolbar)

components/
  video-player-with-transcript.tsx   YouTube IFrame + word-level captions + search
  coumba-chat.tsx                    AI chat panel, citations, and dubbing controls
  flashcard-quiz.tsx                 MCQ quiz component

lib/
  api/videos.ts                All API calls — typed, with graceful fallbacks
  i18n/                        Translation strings (EN, FR, WO, FF, BM)
  utils.ts                     YouTube URL helpers and shared utilities

public/                          Brand assets, including the Open VidLib logo.
```

---

## User-facing behavior

- English and French dubbing are supported. The first request generates and caches audio segments plus a timestamp-matched translated caption manifest; later requests reuse both.
- Other language choices are shown as coming soon until their translation and voice presets are implemented.
- When dubbed audio is active, the caption panel switches from the original word-level transcript to the matching translated caption segments.
- Search and Explain Concept fill the chat input so the learner can edit the request before sending it.
- The frontend contains no Mistral credentials or AI orchestration; all retrieval, RAG, translation, and TTS requests go through the API.

## Key decisions

**Graceful degradation** — every API call in `lib/api/videos.ts` catches errors and returns a sensible fallback (static seed data or an empty array). The UI never crashes because the backend is unavailable.

**No AI logic in the frontend** — the frontend is just a consumer of the REST API. All Mistral calls happen in the backend. The frontend does not know which model is being used.

**Timestamp links** — the Coumba chat component parses `[MM:SS]` patterns in AI responses and renders them as clickable buttons that seek the YouTube player. This is handled entirely client-side via `useImperativeHandle` on the player ref.

---

## Type checking

```bash
npx tsc --noEmit
```
