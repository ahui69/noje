# 🔬 AUDYT MRD – STAN NA DZISIAJ

Raport obejmuje cały kod backendu dostępny w repozytorium (folder główny odpowiada historycznemu `mrd/`). Brak fizycznego katalogu `mrd/` – wszystkie moduły leżą w root. Poniżej pełny audyt, plan napraw i spec frontendowa.

## 1) MAPA PROJEKTU + ENTRYPOINT TRUTH

### Drzewo kluczowych plików
- `app.py` – główny serwer FastAPI z dynamicznym ładowaniem routerów (root + core) oraz mountem static. 【F:app.py†L1-L205】
- `openai_compat.py` – zgodność z OpenAI `/v1` (modele, chat/completions, SSE). 【F:openai_compat.py†L1-L86】
- Routery root: `assistant_simple.py`, `stt_endpoint.py`, `tts_endpoint.py`, `suggestions_endpoint.py`, `internal_endpoint.py`, `files_endpoint.py`, `routers.py` (każdy wystawia `router`). 【F:app.py†L112-L139】
- Routery core (opcjonalne): `core/assistant_endpoint.py`, `core/memory_endpoint.py`, `core/cognitive_endpoint.py`, `core/negocjator_endpoint.py`, `core/reflection_endpoint.py`, `core/legal_office_endpoint.py`, `core/hybrid_search_endpoint.py`, `core/batch_endpoint.py`, `core/prometheus_endpoint.py`. 【F:app.py†L140-L166】
- Alternatywny, niespójny entrypoint: `core/app.py` (nie jest włączany, ma własne konfiguracje). 【F:core/app.py†L1-L200】
- Konfiguracja/env: `core/config.py` (ładowanie .env, wartości domyślne, klucze LLM). 【F:core/config.py†L1-L90】
- Middleware/logging: brak centralnego modułu – CORS w `app.py`, dodatkowe w `core/middleware.py` (nieużywane). 【F:app.py†L64-L70】

### Potencjalne entrypointy
- ✅ **EntryPoint Truth (docelowy):** `app.py` → `uvicorn app:app --host 0.0.0.0 --port 8080` (dev z `--reload`). 【F:app.py†L56-L171】
- ⚠️ `core/app.py` – duplikat serwera, inne routery; należy wyłączony w prod. 【F:core/app.py†L1-L200】
- Skrypty startowe: `start.sh`, `start_api.sh` uruchamiają `uvicorn app:app` bez konfigurowania PYTHONPATH (ryzyko, gdy repo w innej ścieżce).

### Co trzeba mieć, by start był bez błędów
- Zmienne środowiskowe: `LLM_API_KEY` obowiązkowa (inaczej error i brak działania). 【F:core/config.py†L32-L45】
- Serwisy zewnętrzne: Redis opcjonalny, ale import `core.memory` próbuje się łączyć podczas importu (brak serwera = startuje z błędami logów). 【F:core/memory.py†L85-L140】
- Katalogi: `logs/` tworzony automatycznie; `static/` wymagany do mountu (jeśli brak – FastAPI rzuci błąd przy starcie). 【F:app.py†L21-L70】
- PYTHONPATH: repo root musi być w ścieżce (dla importów `core.*`).

## 2) MIX ROUTERÓW / FRAMEWORKÓW + PLAN UNIFIKACJI

| Mechanizm | Pliki | Jak działa | Ryzyko | Decyzja docelowa |
| --- | --- | --- | --- | --- |
| `FastAPI()` + `APIRouter` | `app.py`, wszystkie `*_endpoint.py`, `core/*endpoint.py`, `openai_compat.py` | Standardowa rejestracja routerów | Niskie | Zostawić jako standard |
| Dynamiczny import routerów | `app.py` (`importlib.import_module`, bezpieczny fallback) | Ładuje routery z listy, błędy trafiają do `/api/routers/status` | Średnie: błędy ukryte, router może nie być włączony | Ujednolicić: jawny import, brak try/except, logowanie na start |
| Alternatywny serwer | `core/app.py` | Oddzielny FastAPI z inną listą routerów | Wysokie: duplikaty, inna konfiguracja | Wyłączyć, pozostawić jako archiwum/`_legacy` |
| Podwójne prefixy `/api/api` | Alias generator w `app.py` | Dodaje aliasy gdy router ma podwójny prefix | Średnie: maskuje błąd prefixów | Naprawić prefixy w routerach, usunąć aliasowanie |

**Plan unifikacji:**
1. Ustalić jeden `app.py` jako źródło prawdy, przenieść listę routerów do jednego modułu `mrd/bootstrap.py` i importować bez try/except.
2. Dodać pre-flight walidację importów (raise na brakującym module) i log startowy z pełną listą.
3. Wszystkie routery mają mieć `router = APIRouter(prefix="/api/...", tags=[...])` i być włączone explicit w `app.py`.
4. `core/app.py` oznaczyć jako legacy; wyłączyć w start.sh i dokumentacji.

## 3) LISTA ENDPOINTÓW + KONFLIKTY + DEAD ROUTES

### Aktywne (ładowane w `app.py`)
- `/v1/*` z `openai_compat.py` (modele, chat completions, stream). 【F:openai_compat.py†L1-L86】
- Root routery: chat prosty `/api/chat/assistant`, STT `/api/stt/*`, TTS `/api/tts/*`, sugestie `/api/suggestions/*`, internal `/api/internal/ui_token`, pliki `/api/files/*`, admin `/api/routers/*`. 【F:app.py†L112-L139】【F:routers.py†L1-L120】
- Core routery (opcjonalnie): advanced chat `/api/chat/*`, memory `/api/memory/*`, cognitive `/api/cognitive/*`, negocjator `/api/negocjator/*`, reflection `/api/reflection/*`, legal `/api/legal/*`, hybrid search `/api/hybrid/*`, batch `/api/batch/*`, prometheus `/api/prometheus/*`. 【F:app.py†L140-L166】
- Lokalne endpointy: `/health`, `/api/routers/status`, `/api/endpoints/list`. 【F:app.py†L73-L188】

### Dead routes / niewłączone
- Moduły istniejące, ale **nie są na liście** w `app.py`: `travel_endpoint.py`, `writing_endpoint.py`, `programista_endpoint.py`, `psyche_endpoint.py`, `nlp_endpoint.py`, `research_endpoint.py`, `prometheus_endpoint.py` (root wersja), `assistant_endpoint.py` (root), `hybrid_search_endpoint.py` (root). W efekcie funkcje niedostępne mimo kodu. 【F:app.py†L112-L166】
- `core/middleware.py`, `core/redis_middleware.py` – nie podpinane do `app`.
- `core/app.py` – alternatywny serwer, nie używany przez start.sh.

### Konflikty
- Możliwy **podwójny prefix `/api/api`** – kod dodaje aliasy zamiast naprawić źródło. 【F:app.py†L216-L239】
- Duplikacja routerów promethues: root `prometheus_endpoint.py` i `core/prometheus_endpoint.py` z różnymi implementacjami; tylko core wersja potencjalnie ładowana (opcjonalnie), root nigdy.

## 4) KONTRAKT API – STANDARD

- **Odpowiedź sukces:** JSON, brak wspólnego envelope – różne struktury. Zalecenie: `{"ok": true, "data": ...}`; błędy z `{"ok": false, "error": {code, message}}`.
- **Błędy:** część endpointów rzuca `HTTPException` bez kodu błędu dziedzinowego; globalny handler w `app.py` zwraca `detail` + `error`. 【F:app.py†L208-L213】
- **Auth:** token Bearer z `AUTH_TOKEN` (root i openai_compat). `core/config` ustawia domyślny niesekretny token gdy brak ENV. 【F:core/config.py†L20-L35】【F:openai_compat.py†L12-L31】
- **OpenAPI:** powinno generować się z `app`, ale dynamiczne aliasy `/api/api` i niezaładowane routery mogą ukrywać błędy; brak walidacji importów = schema może być niekompletna.
- **Streaming:** SSE w `openai_compat.py` (`data: {json}\n\n`), brak ping/pong i obsługi rozłączenia; brak standaryzacji w innych endpointach. 【F:openai_compat.py†L87-L180】

## 5) IMPORTY / BRAKI / CYKLE / ASYNC-BLOCKING

- **Globalne inicjalizacje**: `core/config.py` ładuje .env i wypisuje błędy na imporcie; `core/memory.py` na imporcie otwiera SQLite/Redis i uruchamia zadania tła – blokuje start i tworzy połączenia nawet gdy router nieużywany. 【F:core/config.py†L10-L45】【F:core/memory.py†L85-L140】
- **Brakujące zależności runtime:** Redis wymagany do cache (błąd połączenia przy imporcie); brak `static/` skutkuje wyjątkiem przy mount. 【F:app.py†L60-L70】
- **Async-blocking:** liczne wywołania blokujące (sqlite3 sync, requests/ httpx bez timeout w części modułów). `openai_compat` ma timeout, ale wiele core modułów używa `requests` synchronnie (np. `core.research`, `travel_endpoint` – potrzeba async/httpx lub `asyncio.to_thread`).
- **Cykle importów:** dynamiczne importy w `app.py` mogą maskować, ale `core` używa wzajemnych importów (np. `core.cognitive_endpoint` -> `core.llm` -> `core.config`). Nie powodują błędu dzięki kolejności, ale utrudniają testy.

## 6) KONFIGURACJA / ENV – JEDNO MIEJSCE

Wyciąg najważniejszych zmiennych (z `core/config.py` + `app.py`):

| Nazwa | Gdzie użyta | Wymagana | Domyślna | Skutek braku |
| --- | --- | --- | --- | --- |
| `LLM_API_KEY` | `core/config.py`, `openai_compat.py` | Tak | brak | błędy startu/401 do LLM 【F:core/config.py†L32-L45】 |
| `LLM_BASE_URL` | `core/config.py`, `openai_compat.py` | Nie | `https://api.deepinfra.com/v1/openai` | kieruje na DeepInfra 【F:openai_compat.py†L10-L31】 |
| `LLM_MODEL` | `core/config.py`, `openai_compat.py` | Nie | `Qwen/Qwen3-Next-80B-A3B-Instruct` | fallback model 【F:core/config.py†L32-L45】 |
| `AUTH_TOKEN` | `core/config.py`, `openai_compat.py`, `routers.py` | Tak (prod) | domyślny hardcoded | brak = otwarty dostęp 【F:core/config.py†L20-L35】 |
| `CORS_ALLOW_ORIGINS` | `app.py` | Nie | `http://localhost:3000` | zła lista = blokada frontu 【F:app.py†L64-L70】 |
| `MEM_DB` | `core/config.py` | Nie | `mem.db` w BASE_DIR | lokalizacja bazy 【F:core/config.py†L23-L30】 |
| `UPLOAD_DIR` | `core/config.py` | Nie | `uploads/` | brak katalogu = błędy zapisu |
| `SERPAPI_KEY`, `FIRECRAWL_API_KEY`, `OTM_API_KEY` | `core/config.py` + moduły research/travel | Tak dla funkcji | pusty | funkcje research/travel nie działają |

**Docelowy moduł configu:** przenieść wszystkie env do jednego `config.py` w root (`mrd/config.py`) zwracanego przez funkcję `load_settings()` (pydantic-settings), bez inicjalizacji serwisów na imporcie. Dodać `.env.example` z listą powyżej (bez sekretów).

## 7) PORZĄDKI / KLASYFIKACJA PLIKÓW

- **ACTIVE:** `app.py`, `openai_compat.py`, routery z listy root (`assistant_simple.py`, `stt_endpoint.py`, `tts_endpoint.py`, `suggestions_endpoint.py`, `internal_endpoint.py`, `files_endpoint.py`, `routers.py`), oraz core routery jeżeli import się uda. Uzasadnienie: bezpośrednio importowane w `app.py`. 【F:app.py†L112-L166】
- **LIKELY ACTIVE:** `core/*` moduły pomocnicze (llm, memory, helpers, tools_registry itp.) – używane przez core routery, część importowana tranzytywnie nawet gdy routery nie są włączone.
- **ORPHAN:** wszystkie routery niewymienione w `app.py` (travel, writing, programista, psyche, nlp, research, prometheus root). Nie ma ścieżki importu z entrypointu. Zalecenie: przenieść do `mrd/_legacy/` po potwierdzeniu braku potrzeby, albo włączyć do `app.py` po weryfikacji kontraktów.

**Import graph (skrót):** `app.py` → dynamiczne importy root routerów → w routerach importy do `core` (np. `suggestions_endpoint` → `core.memory` → Redis/SQLite). Core routery → `core.llm`, `core.config`, `core.memory`, `core.tools_registry` etc.

## 8) MIDDLEWARE / AUTH / OBSERVABILITY / TIMEOUTY

- CORS jedyny aktywny middleware (brak GZip, ProxyHeaders). 【F:app.py†L64-L70】
- Auth: Bearer token (brak refresh/exp), domyślny token hardcoded = luka. 【F:core/config.py†L20-L35】
- Logging/trace: brak request_id; logi startowe tylko printy w `app.py` i `core/memory`.
- Timeouty: `openai_compat` ustawia `httpx.Timeout`; większość core modułów używa sync `requests` bez timeoutów – ryzyko blokady event loop.
- Observability: prometheus core router opcjonalny, ale nie włączany zawsze; brak metrics middleware.

## 9) PLAN NAPRAWY – CHECKLISTA P0/P1/P2

### P0 (blokery startu)
- Naprawić strukturę: utworzyć katalog `mrd/` lub jednoznacznie wskazać root w PYTHONPATH; zaktualizować start.sh by eksportował `PYTHONPATH=$(pwd)`. Weryfikacja: `python -c "import app"` bez błędów.
- Wymusić obecność `LLM_API_KEY`, `AUTH_TOKEN` (bez domyślnych wartości) – walidacja przy starcie, zwrot 500 z jasnym komunikatem. Test: `uvicorn app:app` powinien zakończyć się błędem jeśli brak klucza.
- Usunąć aliasowanie `/api/api`, poprawić prefixy w routerach; usunąć dynamiczny `try/except` – start ma failować na brakujących modułach. Test: `/docs` generuje pełną listę bez duplikatów.

### P1 (funkcjonalne)
- Włączyć wszystkie potrzebne routery (travel, writing, programista, psyche, nlp, research, prometheus root) w `app.py` lub oznaczyć legacy; ujednolicić prefixy `/api/...`. Test: `/api/routers/list` zawiera endpointy, manualny curl działa.
- Przenieść inicjalizacje zasobów (Redis, SQLite) do lazy-init przy pierwszym użyciu routera; dodać timeouty i obsługę braku Redis (feature flag). Test: start bez Redis nie loguje błędów, endpointy pamięci działają na SQLite.
- Uspójnić kontrakt JSON (envelope `ok/data/error`), dodać globalny error handler z kodami domenowymi. Test: curl do różnych endpointów zwraca jednolity format.

### P2 (porządki/tech debt)
- Wyizolować config do `config.py` (pydantic-settings), przygotować `.env.example` z pełną listą zmiennych; usunąć hardcode tokenu. Test: `python -c "from config import settings"` zwraca wartości z env.
- Middleware: dodać `TrustedHostMiddleware`, `GZipMiddleware`, `ProxyHeadersMiddleware`, opcjonalnie `RequestIDMiddleware`. Test: logi zawierają request_id, gzip działa.
- Observability: włączyć prometheus metrics router i health `/health` w root; dodać structured logging.

**Definition of Done:** `uvicorn app:app --reload` startuje bez stacktrace; `/docs` i `/health` zwracają 200; kluczowe endpointy chat/STT/TTS/files działają; brak martwych routerów (albo są w `_legacy` i wyłączone świadomie).

## 10) FRONTEND SPEC (ChatGPT/Grok-level)

- **UX:** lewy sidebar z historią (tytuł nadawany automatycznie po pierwszej odpowiedzi), możliwość przypinania rozmów. Główne okno: markdown z code-blockami, przyciski copy, wskaźnik strumienia (spinner + licznik tokenów). Inline citations jeżeli backend zwraca źródła.
- **Sesje:** lokalna pamięć w IndexedDB + sync z serwerem (endpoint `/api/chat/sessions`). Autosave po każdym tokienie strumienia; odzyskiwanie po refreshu.
- **Upload:** drag&drop + file picker, kolejka z progressem, podgląd (pdf/image/text), retry na błędach 5xx/timeout. Backend wymaga `/api/files/upload` (multipart) + `/api/files/metadata/{id}`.
- **Streaming:** SSE wrapper (`EventSource`) z obsługą reconnect i stanów `connecting/streaming/finished`; UI pokazuje częściowe odpowiedzi w czasie rzeczywistym.
- **Stack:** React + Vite + TypeScript + Tailwind; stan w Zustand; klient API z `fetch` + SSE helper; router UI (React Router) z widokami: Dashboard, Chat, Pliki, Ustawienia.
- **Flow czatu:** wybór sesji → wysłanie wiadomości POST `/v1/chat/completions` (lub `/api/chat/assistant` docelowo) z `stream=true` → odbiór tokenów → zapisywanie w historii → możliwość regeneracji/edycji promptu.
- **Wymagania backendowe:**
  - Spójny format SSE: `data: {"id","created","model","choices":[{"delta":{"content":"..."}}]}` + final `data: [DONE]`.
  - Endpoint do listy rozmów (`GET /api/chat/sessions`), szczegółów (`GET /api/chat/{id}`), tytułowania (`POST /api/chat/{id}/title`).
  - Upload: `/api/files/upload` (multipart), `/api/files/list`, `/api/files/download?id=`, `/api/files/ocr`.
  - Auth: Bearer token w nagłówku, 401 z jasnym komunikatem.

## BOOST (szybkie wzmocnienia)
- Dodanie `/_mgmt/startup` endpointu zwracającego status załadowania routerów i zależności (Redis/SQLite). Łatwe monitorowanie startu.
- Włączenie `uvicorn --proxy-headers --forwarded-allow-ips="*"` dla poprawnej pracy za reverse-proxy.
- Dodanie limitów rozmiaru uploadu (set-body-limit) i walidacji MIME w `files_endpoint.py`.

