# ETAP 1 — API CONTRACT DISCOVERY (MRD FastAPI)

## 1. Jak zbierano kontrakt
- Uruchomiono runtime dump (`python audit_runtime_routes.py`) i zapisano do `FRONT/runtime_routes.txt`, co potwierdziło 32 załadowane routery i 192 publiczne trasy (0 chronionych).【F:FRONT/runtime_routes.txt†L3-L345】
- W kodzie zweryfikowano kluczowe modele i odpowiedzi dla frontu: chat (stream + non-stream) w `assistant_simple.py` oraz pełny moduł plików w `files_endpoint.py`.【F:assistant_simple.py†L203-L520】【F:files_endpoint.py†L15-L217】
- OpenAPI jest generowane automatycznie przez FastAPI (brak dedykowanego eksportu w repo), ale runtime dump ujawnia pełną listę tras; brak wymuszonego uwierzytelnienia dla większości z nich (domyślnie publiczne).【F:FRONT/runtime_routes.txt†L147-L345】

## 2. Trasy istotne dla frontu (do produkcyjnego UI)

| Flow | Metoda | Ścieżka | Auth | Request (kluczowe pola) | Odpowiedź / Stream |
|---|---|---|---|---|---|
| Chat non-stream | POST | `/api/chat/assistant` | Bearer opcjonalny (sprawdza `AUTH_TOKEN`, brak = public) | `message` lub `messages[]`, `user_id`, opcj. `session_id`, `system_prompt`, `temperature`, `max_tokens`, `use_history` | JSON: `answer`, `session_id`, `ts`, `metadata{model,base_url,history_used}`【F:assistant_simple.py†L205-L283】【F:FRONT/runtime_routes.txt†L152-L156】
| Chat stream (SSE) | POST | `/api/chat/assistant/stream` | Bearer opcjonalny | Body jak wyżej; strumień SSE z eventami `meta{session_id,model}`, wieloma `delta` (tokeny), opcj. `error`, końcowym `done{ok:true}`; ping `: ping` co ~500ms【F:assistant_simple.py†L288-L520】
| Chat legacy | POST | `/api/chat/assistant` (drugi router) | Brak realnego auth | Alternatywna implementacja (legacy cognitive); kontrakt podobny, brak SSE detali — ryzyko duplikatu ścieżki【F:FRONT/runtime_routes.txt†L154-L156】
| STT | POST | `/api/stt/transcribe` | Brak auth | Multipart audio; zwraca transkrypcję (brak schematu w kodzie do UI → potrzebne doprecyzowanie)【F:FRONT/runtime_routes.txt†L157】
| TTS | POST | `/api/tts/speak` | Brak auth | Tekst + głos; zwraca audio/URL (kontrakt w kodzie do doprecyzowania przed UI)【F:FRONT/runtime_routes.txt†L160】
| Files upload | POST | `/api/files/upload` | Wymaga `Authorization: Bearer <AUTH_TOKEN>`; default `changeme` jeśli ENV nieustawione | multipart `file` | JSON: `{ok, file_id, filename, size, path, analysis{type,mime,metadata,extracted_text}}`【F:files_endpoint.py†L170-L217】【F:FRONT/runtime_routes.txt†L167-L175】
| Files upload (base64) | POST | `/api/files/upload/base64` | Bearer | `{filename, content(base64), mime_type?}` | JSON jak wyżej (bez `path`)【F:files_endpoint.py†L219-L261】
| Files list | GET | `/api/files/list` | Bearer | — | `{ok, files:[{file_id,id,name,path,size,...}], count}`【F:files_endpoint.py†L262-L309】【F:FRONT/runtime_routes.txt†L169-L173】
| Files download | GET | `/api/files/download?file_id=` | Bearer | query `file_id` | Plik jako `FileResponse` (octet-stream)【F:files_endpoint.py†L310-L333】
| Files analyze | POST | `/api/files/analyze` | Bearer | `{file_id, extract_text?, analyze_content?}` | `{ok, analysis{...}}` z opcjonalnym LLM podsumowaniem【F:files_endpoint.py†L335-L382】
| Files delete | POST | `/api/files/delete` | Bearer | `{file_id}` | `{ok, deleted}` lub 404【F:files_endpoint.py†L384-L405】
| Files stats | GET | `/api/files/stats` | Bearer | — | `{ok, total_files, total_size_mb, upload_dir, by_extension}`【F:files_endpoint.py†L407-L432】
| Suggestions (core) | POST | `/api/suggestions/generate` | Brak auth | `{message,context?...}` → generuje sugestie; schemat do potwierdzenia【F:FRONT/runtime_routes.txt†L162-L165】【F:FRONT/runtime_routes.txt†L300-L304】
| Memory (core) | POST | `/api/memory/add` / `/search` | Brak auth | różne pola (teksty, metadane) – brak kontraktu pod UI, wymaga doprecyzowania | JSON status【F:FRONT/runtime_routes.txt†L259-L266】
| Health | GET | `/health` | Public | Spójny payload: `{status, version, ts, env{...}, metrics?}`【F:FRONT/runtime_routes.txt†L151】【F:health_payload.py†L13-L35】
| Metrics | GET | `/metrics` | Public | Prometheus text/exposition【F:FRONT/runtime_routes.txt†L179-L181】

## 3. Kluczowe "core flows" obecnie możliwe/niekompletne
- **Sesje + historia**: Backend zapisuje sesje i wiadomości w SQLite w `assistant_simple`; dodano pełne endpointy listowania/pobierania/tytułowania/usuwania sesji, zabezpieczone Bearer tokenem. UI może ładować historię i sidebar z danych `/api/chat/sessions*`.【F:assistant_simple.py†L70-L211】【F:assistant_simple.py†L299-L370】
- **Chat (non-stream + SSE)**: Dostępne i działające (wymagają `LLM_API_KEY`, `LLM_MODEL`). Stream w formacie SSE z eventami `meta/delta/error/done`.【F:assistant_simple.py†L288-L520】
- **Upload + analiza plików**: Pełny cykl upload/list/analyze/delete dostępny, z wymuszonym Bearer tokenem (domyślnie `changeme` → konieczna produkcyjna wartość).【F:files_endpoint.py†L17-L217】【F:FRONT/runtime_routes.txt†L167-L175】
- **Audio (STT/TTS)**: Trasy istnieją, ale brak jasnego kontraktu odpowiedzi w kodzie → wymagana specyfikacja przed implementacją UI audio.【F:FRONT/runtime_routes.txt†L157-L161】
- **Sugestie/Memory/Research**: Bogaty zestaw tras, brak auth, brak dedykowanego kontraktu pod UI; obecnie poza zakresem minimalnego komercyjnego frontu, dopóki nie zostaną spięte z UX.
- **Status/health/metrics**: `/health` i `/metrics` dostępne publicznie; payload zdrowia ujednolicony w `health_payload.py` (status, wersja, env, metryki).【F:health_payload.py†L13-L35】【F:FRONT/runtime_routes.txt†L151-L181】

## 4. Braki blokujące komercyjny front i proponowane uzupełnienia

| Luka | Co brakuje | Gdzie dodać | Proponowany kontrakt (request/response) |
|---|---|---|---|
| Zarządzanie sesjami | Brak listowania i pobierania historii (front nie zbuduje sidebaru). | `assistant_simple.py` (router `/api/chat`) | 
**GET `/api/chat/sessions`** → `{sessions:[{id, user_id, created_at, updated_at, messages:int}]}` (sort desc). 
**GET `/api/chat/sessions/{session_id}`** → `{session_id, user_id, messages:[{role,content,ts}]}` (ostatnie N=200). 
Logika: wykorzystać istniejące tabele `sessions`/`messages` z `_db()`. Zabezpieczyć `AUTH_TOKEN` jak w innych handlerach (401 gdy brak lub zły token). 

| Usuwanie/rename sesji | Brak endpointu do cleanup/zmiany tytułu w UI | `assistant_simple.py` | 
**POST `/api/chat/sessions/{session_id}/delete`** → `{ok:true}` usuwa sesję i powiązane wiadomości. 
**POST `/api/chat/sessions/{session_id}/title`** body `{title}` zapisuje tytuł w nowej kolumnie (dodać w schemacie) lub osobnej tabeli `session_meta(session_id,title)`. 

| Autoryzacja spójna | 192 trasy publiczne (0 chronionych) → brak realnego bezpieczeństwa | `app.py` + poszczególne routery (min. `assistant_simple`, `files_endpoint`, `stt_endpoint`, `tts_endpoint`) | 
Dodać globalny dependency wymuszający `Authorization: Bearer <token>` dla tras używanych przez front produkcyjny (chat, file, audio, suggestions, memory). Przykład: w `app.py` dodać dependency do `include_router` lub w routerach lokalny `Depends(_auth)` (jak w `files_endpoint`).

| Chat stream kompatybilny z frontem | Eventy są `meta/delta/done`, brak `chunk` typu text/plain fallback | `assistant_simple.py` | Utrzymać SSE (EventSource). Upewnić się, że `delta` zawsze string (już normalize) i `done` zawsze na końcu. Dodać opcjonalny `event: "error"` z `code`/`message` dla spójnego UI (teraz string). 

| Audio TTS/STT kontrakt | Brak udokumentowanego schema (w kodzie brak) | `stt_endpoint.py`, `tts_endpoint.py` | Uzupełnić Pydantic modele: 
- STT: POST `/api/stt/transcribe` multipart `file` → `{text, lang?, duration?}`. 
- TTS: POST `/api/tts/speak` JSON `{text, voice?, speed?}` → `{url}` lub `audio_base64`. 

| Token pomocniczy UI | `/api/internal/ui_token` istnieje, ale bez auth | `internal_endpoint.py` | Wymusić Bearer + ograniczyć do debug; front produkcyjny powinien korzystać z przekazanego tokena, nie z endpointu publicznego.

## 5. Wnioski dla frontu (co jest stabilne na dziś)
- **Stabilne**: `/api/chat/assistant` (sync), `/api/chat/assistant/stream` (SSE), zestaw `/api/files/*`, `/health`, `/metrics`. Wymagają poprawnej konfiguracji ENV: `LLM_API_KEY`, `LLM_MODEL`, `AUTH_TOKEN`, `UPLOAD_DIR`.【F:assistant_simple.py†L205-L520】【F:files_endpoint.py†L15-L217】【F:FRONT/runtime_routes.txt†L151-L175】
- **Do uzupełnienia przed kodowaniem UI**: sesje/historia, auth globalny, jasny kontrakt STT/TTS, ewentualne doprecyzowanie pól sugestii/memory.

STOP — czy akceptujesz i czy przechodzę dalej?
