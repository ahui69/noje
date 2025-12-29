# ETAP 3 — TECH ARCHITECTURE FRONT

## Stack
- React 18 + Vite + TypeScript, Tailwind 3, react-router v6.
- TanStack Query do cache API, Zustand do auth/settings/draftów.
- Rendering markdown: `react-markdown` + `remark-gfm` + `rehype-highlight`.

## Typy i kontrakt
- Ręczne typy w `src/api/types.ts` na bazie realnych endpointów (chat, sessions, files, health, TTS/STT).
- SSE event `{event, data}` zgodny z backendem `/api/chat/assistant/stream` (meta/delta/error/done).

## Warstwa API
- `src/api/client.ts` — fetch + Authorization Bearer (token ze store), obsługa 401 reset tokenu.
- `src/api/sse.ts` — `fetch` + `ReadableStream` parser SSE, AbortController do stop stream.
- Upload plików przez `fetch` z FormData do `/api/files/upload` (Bearer wymagany przez backend).

## Storage
- Token, settings: Zustand + `persist` (localStorage klucze `mrd-auth`, `mrd-settings`).
- Drafty wiadomości i aktywna sesja: Zustand `useSessionStore`.
- React Query cache dla sesji (`sessions`, `session/:id`), health/tts/stt.

## Routing
- `/login` -> `/app` guarduje tokenem.
- `/app` shell + nested `/chat/:id?` i `/settings`.

## Observability i błędy
- Alert na błędy sieci; 401 czyści token.
- Streaming parse errors logowane w konsoli (nie blokują UI).
