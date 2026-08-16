# fe-gandalab — GandaLab Web

Next.js 14 (App Router) frontend for GandaLab.

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
  page.tsx                  Landing page — video library grid
  library/[id]/             Video detail page
    page.tsx                Server component (fetches video data)
    resource-page-client.tsx  Client shell (player, chat, toolbar)

components/
  video-player-with-transcript.tsx   YouTube IFrame + word-level captions + semantic search tab
  coumba-chat.tsx           AI chat panel (search cards, Q&A citations, dub controls)
  flashcard-quiz.tsx        MCQ quiz component

lib/
  api/videos.ts             All API calls — typed, with graceful fallbacks
  i18n/                     Translation strings (EN, FR, WO, FF, BM)
  utils.ts                  YouTube URL helpers etc.
```

---

## Key decisions

**Graceful degradation** — every API call in `lib/api/videos.ts` catches errors and returns a sensible fallback (static seed data or an empty array). The UI never crashes because the backend is unavailable.

**No AI logic in the frontend** — the frontend is just a consumer of the REST API. All Mistral calls happen in the backend. The frontend does not know which model is being used.

**Timestamp links** — the Coumba chat component parses `[MM:SS]` patterns in AI responses and renders them as clickable buttons that seek the YouTube player. This is handled entirely client-side via `useImperativeHandle` on the player ref.

---

## Type checking

```bash
npx tsc --noEmit
```
