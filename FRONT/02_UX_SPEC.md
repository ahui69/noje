# ETAP 2 — PRODUCT IA + UX SPEC (MRD Frontend)

## Architektura informacji
- `/login` — ekran logowania tokenem Bearer (AUTH_TOKEN).
- `/app` — shell z top-barem, sidebar (sesje), content i prawy panel statusu.
- `/app/chat/:id?` — główny ekran czatu z historią, streamingiem SSE, uploadami.
- `/app/settings` — konfiguracja tokenu, API base, preferencje stream/drafty.
- `/app/admin` — opcjonalne, niezaimplementowane (wymaga backendu admina, obecnie poza zakresem).

## Layout w stylu ChatGPT/Grok
- Sidebar: lista sesji (tytuł, liczba wiadomości), przycisk "Nowy czat", odświeżenie listy co 15 s.
- Main: lista wiadomości z markdown + highlight, streaming delta, kopiowanie wiadomości.
- Composer: textarea z auto-height, wysyłka Enter, przycisk stop stream, chipy uploadów.
- Right panel (toggle w kodzie możliwy przez CSS, domyślnie widoczny): status `/health`, audio (TTS/STT), debug API base.

## UX czatu
- Ostatnia wiadomość użytkownika edytowalna jako draft (persist w Zustand), wysyłka Enter bez Shift.
- Regenerate: realizowane przez ponowne wysłanie wiadomości (bez dedykowanego endpointu regenerate).
- Stop streaming: AbortController przerywa SSE `fetch`.
- Markdown + code copy: `react-markdown` + `rehype-highlight`, przycisk "Kopiuj" na każdym bubble.
- Upload chips: każdy upload dodaje chip z możliwością usunięcia (nie wysyła w body, służy do referencji kontekstowej).
- Error states: alert na błędy SSE/upload, 401 resetuje token i przekierowuje na `/login`.

## System ustawień
- Token storage: localStorage (`mrd-auth`), setToken z poziomu ustawień lub logowania.
- API base: opcjonalne nadpisanie (domyślnie z `VITE_API_BASE`/localhost) w store `settings`.
- Stream toggle: dostępny w store, domyślnie włączony (komponenty przygotowane pod SSE, fallback sync niewykorzystany).
- Drafty: przechowywane per-session w Zustand (`drafts`).
- Audio: status TTS/STT prezentowany w panelu, brak UI odsłuchu/record (wymaga backendowego kontraktu do odtwarzania/uploadu audio).
