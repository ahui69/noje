# 🔬 AUDYT MRD - BEZWZGLĘDNY RAPORT WDROŻENIOWY

**Data:** 26 grudnia 2025  
**Wersja projektu:** 5.0.0  
**Typ:** Pełny audyt techniczny + plan refaktoru

---

## 📋 SPIS TREŚCI

1. [Mapa projektu + EntryPoint Truth](#1-mapa-projektu--entrypoint-truth)
2. [Mix routerów / frameworków + Plan unifikacji](#2-mix-routerów--frameworków--plan-unifikacji)
3. [Lista endpointów + Konflikty + Dead routes](#3-lista-endpointów--konflikty--dead-routes)
4. [Kontrakt API – Frontend](#4-kontrakt-api--frontend)
5. [Importy / Braki / Cykle / Async-Blocking](#5-importy--braki--cykle--async-blocking)
6. [Konfiguracja / ENV](#6-konfiguracja--env)
7. [Porządki ze starymi plikami (Safe Cleanup)](#7-porządki-ze-starymi-plikami-safe-cleanup)
8. [Middleware / Auth / Observability / Timeouty](#8-middleware--auth--observability--timeouty)
9. [Plan naprawy – Checklista P0/P1/P2](#9-plan-naprawy--checklista-p0p1p2)
10. [Frontend specyfikacja](#10-frontend-specyfikacja)
11. [BOOST – Opcjonalne ulepszenia](#11-boost--opcjonalne-ulepszenia)

---

## 1. MAPA PROJEKTU + ENTRYPOINT TRUTH

### 1.1 Struktura katalogów

```
mrd/
├── app.py                    # ⭐ GŁÓWNY ENTRYPOINT (root)
├── routers.py                # Router admin/debug
├── openai_compat.py          # OpenAI-compatible /v1/* endpoints
├── assistant_simple.py       # Chat commercial (prosty)
├── stt_endpoint.py           # Speech-to-Text
├── tts_endpoint.py           # Text-to-Speech
├── suggestions_endpoint.py   # Proaktywne sugestie
├── internal_endpoint.py      # Internal UI helpers
├── files_endpoint.py         # Upload/analiza plików
├── writing_endpoint.py       # Pisanie kreatywne
├── psyche_endpoint.py        # Psychika AI
├── travel_endpoint.py        # Travel/Maps
├── research_endpoint.py      # Web research
├── prometheus_endpoint.py    # Metryki (root-level)
├── programista_endpoint.py   # Executor kodu
├── requirements.txt
├── start.sh                  # Start script (Linux/macOS)
├── start_api.sh              # Prosty start API
│
├── core/                     # ⚙️ CORE MODULES
│   ├── __init__.py
│   ├── app.py               # ALTERNATYWNY entrypoint (NIE UŻYWAĆ!)
│   ├── config.py            # Konfiguracja centralna
│   ├── auth.py              # Autoryzacja
│   ├── llm.py               # LLM calls
│   ├── memory.py            # Unified Memory System (2373 linii)
│   ├── hierarchical_memory.py # L1-L4 memory
│   ├── helpers.py           # Utilities
│   ├── metrics.py           # Prometheus metrics
│   ├── research.py          # Web research/autonauka
│   ├── writing.py           # Moduł pisania
│   ├── advanced_psychology.py
│   ├── advanced_cognitive_engine.py
│   ├── cognitive_engine.py  # Orchestrator
│   ├── tools_registry.py    # 121 tools jako OpenAI functions
│   ├── intent_dispatcher.py
│   ├── self_reflection.py
│   ├── executor.py          # Programista class
│   │
│   ├── assistant_endpoint.py    # Chat advanced [core]
│   ├── memory_endpoint.py       # Memory API
│   ├── cognitive_endpoint.py    # Cognitive API
│   ├── negocjator_endpoint.py   # AI Negocjator
│   ├── reflection_endpoint.py   # Self-reflection
│   ├── legal_office_endpoint.py # Pisma urzędowe
│   ├── hybrid_search_endpoint.py # Hybrid search
│   ├── batch_endpoint.py        # Batch processing
│   ├── prometheus_endpoint.py   # Metrics [core]
│   └── ...
│
├── data/                     # Dane sesji
├── scripts/                  # Skrypty pomocnicze
├── tests/                    # Testy
├── tools/                    # Narzędzia deweloperskie
└── patch_*.py                # Skrypty patchowe (legacy)
```

### 1.2 ENTRYPOINT TRUTH

| Aspekt                | Decyzja                                                  |
| --------------------- | -------------------------------------------------------- |
| **GŁÓWNY ENTRYPOINT** | `mrd/app.py` (ROOT)                                      |
| **NIE UŻYWAĆ**        | `mrd/core/app.py` (duplikat, rozbieżne routery)          |
| **Komenda DEV**       | `uvicorn app:app --reload --host 0.0.0.0 --port 8080`    |
| **Komenda PROD**      | `uvicorn app:app --host 0.0.0.0 --port 8080 --workers 4` |
| **PYTHONPATH**        | `export PYTHONPATH=/path/to/mrd:$PYTHONPATH`             |

### 1.3 Wymagane przed startem

| Wymóg            | Status        | Naprawa                          |
| ---------------- | ------------- | -------------------------------- |
| Folder `static/` | ❌ BRAK       | Utworzyć: `mkdir static`         |
| Plik `.env`      | ⚠️ Opcjonalny | Skopiować z `.env.example`       |
| `LLM_API_KEY`    | ⚠️ WYMAGANY   | Ustawić w `.env`                 |
| Redis            | ⚠️ Opcjonalny | Działa bez, ale wolniejsze cache |

---

## 2. MIX ROUTERÓW / FRAMEWORKÓW + PLAN UNIFIKACJI

### 2.1 Wykryte wzorce routingu

| Mechanizm                      | Pliki                                               | Jak działa                   | Ryzyko     | Decyzja                         |
| ------------------------------ | --------------------------------------------------- | ---------------------------- | ---------- | ------------------------------- |
| `FastAPI()` + `APIRouter`      | Wszystkie                                           | Standard FastAPI             | ✅ Niskie  | ZACHOWAĆ                        |
| Dynamiczny import + try/except | `app.py`                                            | `importlib.import_module()`  | ⚠️ Średnie | ZACHOWAĆ (graceful degradation) |
| Podwójny prefix `/api/api/`    | Auto-aliasy w `app.py`                              | Workaround na błędne prefixy | ⚠️ Średnie | NAPRAWIĆ (usunąć duplikaty)     |
| Fallbacki w endpointach        | `suggestions_endpoint.py`, `core/batch_endpoint.py` | try/except na importy        | ⚠️ Średnie | ZACHOWAĆ (ale logować)          |

### 2.2 Konflikty prefixów

| Router                          | Prefix                          | Problem               |
| ------------------------------- | ------------------------------- | --------------------- |
| `prometheus_endpoint.py` (root) | brak (`router = APIRouter()`)   | Brak prefixu!         |
| `prometheus_endpoint.py` (core) | Dodawany jako `/api/prometheus` | Konflikt z root-level |
| `core/app.py`                   | Importuje z root bez prefixów   | Duplikacja            |

### 2.3 DECYZJA DOCELOWA

```
Jeden standard: FastAPI + APIRouter
Jeden entrypoint: mrd/app.py
Wszystkie routery z prefiksem: /api/{domena}
```

**Plan migracji:**

1. Użyć wyłącznie `mrd/app.py` jako entrypoint
2. Usunąć `core/app.py` z produkcji (przenieść do `_legacy/`)
3. Dodać prefix do `prometheus_endpoint.py` (root)
4. Usunąć mechanizm auto-alias `/api/api/`

---

## 3. LISTA ENDPOINTÓW + KONFLIKTY + DEAD ROUTES

### 3.1 Aktywne endpointy (z `app.py`)

| Moduł                         | Prefix             | Metody                                                                                                                                                                                   | Auth       | Typ         |
| ----------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------- |
| `openai_compat`               | `/v1`              | GET `/models`, POST `/chat/completions`                                                                                                                                                  | Bearer     | JSON/Stream |
| `assistant_simple`            | `/api/chat`        | POST `/assistant`, POST `/assistant/stream`                                                                                                                                              | Bearer     | JSON/SSE    |
| `stt_endpoint`                | `/api/stt`         | POST `/transcribe`, GET `/providers`                                                                                                                                                     | -          | JSON        |
| `tts_endpoint`                | `/api/tts`         | GET `/voices`, POST `/speak`, GET `/status`                                                                                                                                              | -          | JSON/Audio  |
| `suggestions_endpoint`        | `/api/suggestions` | POST `/generate`, POST `/inject`, GET `/stats`, POST `/analyze`                                                                                                                          | Bearer     | JSON        |
| `internal_endpoint`           | `/api/internal`    | GET `/ui_token`                                                                                                                                                                          | Local/Flag | JSON        |
| `files_endpoint`              | `/api/files`       | POST `/upload`, POST `/upload64`, POST `/analyze`, DELETE `/delete`, GET `/list`, GET `/download/{id}`                                                                                   | Bearer     | JSON/File   |
| `routers`                     | `/api/routers`     | GET `/status`, GET `/health`, GET `/list`, GET `/metrics`, GET `/config`, GET `/endpoints/summary`, GET `/debug/info`, POST `/cache/clear`, GET `/version`, GET `/experimental/features` | Bearer     | JSON        |
| **CORE:**                     |                    |                                                                                                                                                                                          |            |             |
| `core.assistant_endpoint`     | `/api/chat`        | POST `/assistant`, POST `/assistant/stream`, POST `/auto`                                                                                                                                | Bearer     | JSON/SSE    |
| `core.memory_endpoint`        | `/api/memory`      | POST `/add`, POST `/search`, GET `/export`, POST `/import`, GET `/status`, POST `/optimize`                                                                                              | Tenant     | JSON        |
| `core.cognitive_endpoint`     | `/api/cognitive`   | POST `/reflect`, GET `/reflection/summary`, POST `/proactive`, GET `/psychology`, POST `/psychology/update`                                                                              | Bearer     | JSON        |
| `core.negocjator_endpoint`    | `/api/negocjator`  | POST `/analiza`, POST `/propozycja`, POST `/ocena`, POST `/kalkulator`                                                                                                                   | Bearer     | JSON        |
| `core.reflection_endpoint`    | `/api/reflection`  | POST `/reflect`, POST `/adaptive-reflect`, GET `/history`, GET `/stats`                                                                                                                  | Bearer     | JSON        |
| `core.legal_office_endpoint`  | `/api/legal`       | POST `/analyze`, POST `/generate`, GET `/templates`, POST `/ocr`                                                                                                                         | Bearer     | JSON        |
| `core.hybrid_search_endpoint` | `/api/search`      | POST `/hybrid`, GET `/status`                                                                                                                                                            | Bearer     | JSON        |
| `core.batch_endpoint`         | `/api/batch`       | POST `/process`, GET `/status/{id}`, GET `/list`, DELETE `/{id}`                                                                                                                         | Bearer     | JSON        |
| `core.prometheus_endpoint`    | `/api/prometheus`  | GET `/metrics`, GET `/health`, GET `/stats`                                                                                                                                              | -          | Text/JSON   |

### 3.2 Konflikty ścieżek

| Ścieżka                      | Konflikt                                              | Problem                   | Naprawa                                           |
| ---------------------------- | ----------------------------------------------------- | ------------------------- | ------------------------------------------------- |
| `/api/chat/assistant`        | `assistant_simple.py` vs `core/assistant_endpoint.py` | ⚠️ OBA ładowane do app.py | Zachować oba (różne funkcje) - prosty vs advanced |
| `/api/chat/assistant/stream` | jw.                                                   | jw.                       | jw.                                               |
| `/health`                    | `app.py` vs `routers.py`                              | Duplikat                  | Zachować tylko w `app.py`                         |
| `/api/prometheus/*`          | `prometheus_endpoint.py` root vs core                 | Duplikat                  | Usunąć root-level, użyć tylko core                |

### 3.3 Dead Routes / Orphan Modules

| Plik                               | Status       | Powód                                      | Decyzja                          |
| ---------------------------------- | ------------ | ------------------------------------------ | -------------------------------- |
| `core/app.py`                      | ❌ ORPHAN    | Nie jest importowany przez główny `app.py` | → `_legacy/`                     |
| `writer_pro.py`                    | ❌ ORPHAN    | Nie jest ładowany do żadnego routera       | → `_legacy/` lub dodać do app.py |
| `autonauka_pro.py`                 | ❌ ORPHAN    | Nie jest importowany                       | → `_legacy/`                     |
| `sports_news_pro.py`               | ❌ ORPHAN    | Nie jest importowany                       | → `_legacy/`                     |
| `hybrid_search_endpoint.py` (root) | ⚠️ RE-EXPORT | Tylko re-eksportuje z core                 | Usunąć, używać core              |
| `research.py` (root)               | ❌ ORPHAN    | Duplikat `core/research.py`                | → `_legacy/`                     |
| `hierarchical_memory.py` (root)    | ❌ ORPHAN    | Duplikat `core/hierarchical_memory.py`     | → `_legacy/`                     |
| `nlp_endpoint.py`                  | ❌ ORPHAN    | Nie jest ładowany                          | Dodać do app.py lub `_legacy/`   |
| `patch_*.py` (27 plików)           | ⚠️ UTILITY   | Skrypty jednorazowe                        | → `_archive/`                    |
| `fix_*.py` (6 plików)              | ⚠️ UTILITY   | Skrypty naprawcze                          | → `_archive/`                    |
| `tools_*.py` (8 plików)            | ⚠️ UTILITY   | Skrypty patchowe                           | → `_archive/`                    |

### 3.4 Brakujące moduły (ImportError)

| Import                   | Gdzie używany            | Problem                            | Naprawa                         |
| ------------------------ | ------------------------ | ---------------------------------- | ------------------------------- |
| `captcha_endpoint`       | `core/app.py`            | ❌ NIE ISTNIEJE                    | Usunąć import lub stworzyć stub |
| `admin_endpoint`         | `core/app.py`            | ✅ Istnieje w `core/`              | Poprawić ścieżkę importu        |
| `monolit` / `monolit.py` | `files_endpoint.py`      | ❌ NIE ISTNIEJE                    | Usunąć import lub stworzyć stub |
| `cache_get`, `cache_put` | `core/research.py`       | ❌ NIE ISTNIEJĄ w `core/memory.py` | **P0: DODAĆ FUNKCJE**           |
| `middleware`             | `core/admin_endpoint.py` | ❌ NIE ISTNIEJE                    | Stworzyć stub lub usunąć        |
| `travel_search`          | `core/research.py`       | ⚠️ Zdefiniowane w tym samym pliku  | OK                              |

---

## 4. KONTRAKT API – FRONTEND

### 4.1 Standard odpowiedzi SUCCESS

```json
{
  "ok": true,
  "answer": "...", // lub "text", "content", "data"
  "sources": [], // opcjonalne
  "metadata": {
    "model": "...",
    "session_id": "...",
    "ts": 1703612800.123
  }
}
```

### 4.2 Standard odpowiedzi ERROR

```json
{
  "ok": false,
  "detail": "Error message",
  "error": "ErrorType", // opcjonalne
  "status_code": 500
}
```

### 4.3 Standard AUTH

| Metoda       | Header              | Wartość               |
| ------------ | ------------------- | --------------------- |
| Bearer Token | `Authorization`     | `Bearer {AUTH_TOKEN}` |
| Fallback     | Query param `token` | `?token={AUTH_TOKEN}` |

### 4.4 Streaming (SSE)

**Format chunków:**

```
data: {"event": "meta", "data": {"session_id": "...", "ts": 1703612800}}

data: {"event": "delta", "data": "token text..."}

data: {"event": "done", "data": {"ok": true}}

```

**Keepalive:**

```
: ping

```

**Nagłówki:**

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

### 4.5 OpenAPI

| Aspect            | Status                                    |
| ----------------- | ----------------------------------------- |
| `/docs`           | ✅ Działa                                 |
| `/redoc`          | ✅ Działa                                 |
| `/openapi.json`   | ✅ Generuje się                           |
| Schema validation | ⚠️ Niektóre endpointy bez Pydantic models |

---

## 5. IMPORTY / BRAKI / CYKLE / ASYNC-BLOCKING

### 5.1 P0: KRYTYCZNE BRAKUJĄCE FUNKCJE

| Funkcja                 | Gdzie brakuje    | Używana przez                                  | Naprawa                 |
| ----------------------- | ---------------- | ---------------------------------------------- | ----------------------- |
| `cache_get(key, ttl)`   | `core/memory.py` | `core/research.py` (linie 793, 844, 914, 1113) | **DODAĆ IMPLEMENTACJĘ** |
| `cache_put(key, value)` | `core/memory.py` | `core/research.py`                             | **DODAĆ IMPLEMENTACJĘ** |

**Implementacja do dodania w `core/memory.py`:**

```python
# === CACHE FUNCTIONS ===
_MEMORY_CACHE: Dict[str, Tuple[Any, float]] = {}

def cache_get(key: str, ttl: float = 3600) -> Optional[Any]:
    """Get value from in-memory cache if not expired"""
    if key in _MEMORY_CACHE:
        value, timestamp = _MEMORY_CACHE[key]
        if time.time() - timestamp < ttl:
            return value
        del _MEMORY_CACHE[key]
    return None

def cache_put(key: str, value: Any) -> None:
    """Put value in in-memory cache"""
    _MEMORY_CACHE[key] = (value, time.time())
```

### 5.2 Potencjalne cykle importów

| Łańcuch                                                          | Ryzyko     | Mitygacja                    |
| ---------------------------------------------------------------- | ---------- | ---------------------------- |
| `cognitive_engine` → `memory` → `hierarchical_memory` → `memory` | ⚠️ Średnie | Lazy imports już zastosowane |
| `app.py` → `routers.py` → `app.py`                               | ✅ Niskie  | Import wewnątrz funkcji      |

### 5.3 Blokujące I/O w async

| Plik              | Linia                            | Problem                       | Naprawa                                      |
| ----------------- | -------------------------------- | ----------------------------- | -------------------------------------------- |
| `core/helpers.py` | `http_get()`, `http_post_json()` | Używa `urllib.request` (sync) | Zamienić na `httpx.AsyncClient`              |
| `core/memory.py`  | `sqlite3.connect()`              | Sync SQLite                   | OK dla małych operacji, rozważyć `aiosqlite` |
| `core/writing.py` | `call_llm()`                     | Sync wersja LLM               | Używać `await call_llm_async()`              |

### 5.4 Brakujące paczki (requirements.txt)

| Paczka              | Używana gdzie              | Status                                             |
| ------------------- | -------------------------- | -------------------------------------------------- |
| `redis`             | `core/redis_middleware.py` | ⚠️ Opcjonalna (graceful fallback)                  |
| `prometheus_client` | `core/metrics.py`          | ⚠️ Opcjonalna (graceful fallback)                  |
| `jose`              | `core/admin_endpoint.py`   | ⚠️ W requirements jako `python-jose[cryptography]` |

---

## 6. KONFIGURACJA / ENV

### 6.1 Tabela zmiennych ENV

| Zmienna               | Gdzie używana                   | Required | Default                               | Co bez niej                  |
| --------------------- | ------------------------------- | -------- | ------------------------------------- | ---------------------------- |
| `AUTH_TOKEN`          | Wszystkie endpointy             | ⚠️       | `ssjjMijaja6969`                      | Działa ale INSECURE          |
| `LLM_API_KEY`         | `core/llm.py`, `core/config.py` | ✅ TAK   | brak                                  | App nie działa               |
| `LLM_BASE_URL`        | `core/config.py`                | ❌       | `https://api.deepinfra.com/v1/openai` | OK                           |
| `LLM_MODEL`           | `core/config.py`                | ❌       | `Qwen/Qwen3-Next-80B-A3B-Instruct`    | OK                           |
| `MEM_DB`              | `core/config.py`                | ❌       | `{WORKSPACE}/mem.db`                  | OK                           |
| `WORKSPACE`           | `core/config.py`                | ❌       | Katalog `core/`                       | OK                           |
| `ELEVENLABS_API_KEY`  | `tts_endpoint.py`               | ⚠️       | brak                                  | TTS nie działa               |
| `ELEVENLABS_VOICE_ID` | `tts_endpoint.py`               | ⚠️       | brak                                  | TTS nie działa               |
| `SERPAPI_KEY`         | `core/research.py`              | ⚠️       | brak                                  | Tylko DDG/Wiki               |
| `FIRECRAWL_API_KEY`   | `core/research.py`              | ⚠️       | brak                                  | Fallback scraping            |
| `OTM_API_KEY`         | `core/research.py`              | ⚠️       | brak                                  | Travel ograniczone           |
| `OPENAI_API_KEY`      | `stt_endpoint.py`               | ⚠️       | brak                                  | STT: Groq/DeepInfra fallback |
| `GROQ_API_KEY`        | `stt_endpoint.py`               | ⚠️       | brak                                  | STT: inne fallbacki          |
| `JWT_SECRET`          | `core/admin_endpoint.py`        | ⚠️       | brak                                  | JWT auth wyłączone           |
| `REDIS_URL`           | `core/redis_middleware.py`      | ⚠️       | brak                                  | In-memory cache              |
| `UI_EXPOSE_TOKEN`     | `internal_endpoint.py`          | ❌       | `0`                                   | Token tylko dla localhost    |

### 6.2 Docelowy `.env.example`

```bash
# === REQUIRED ===
LLM_API_KEY=your_deepinfra_or_openai_key_here
AUTH_TOKEN=your_secure_random_token_here

# === LLM Configuration ===
LLM_BASE_URL=https://api.deepinfra.com/v1/openai
LLM_MODEL=Qwen/Qwen3-Next-80B-A3B-Instruct
LLM_TIMEOUT=45
LLM_RETRIES=3

# === TTS (ElevenLabs) ===
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# === STT ===
OPENAI_API_KEY=
GROQ_API_KEY=

# === Web Research ===
SERPAPI_KEY=
FIRECRAWL_API_KEY=
OTM_API_KEY=

# === Database ===
MEM_DB=./mem.db
WORKSPACE=.

# === Optional ===
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=
LOG_LEVEL=INFO
UI_EXPOSE_TOKEN=0
```

---

## 7. PORZĄDKI ZE STARYMI PLIKAMI (SAFE CLEANUP)

### 7.1 Klasyfikacja plików

#### ACTIVE (na pewno używane)

| Plik                      | Dowód użycia                         |
| ------------------------- | ------------------------------------ |
| `app.py`                  | Entrypoint                           |
| `openai_compat.py`        | Importowany w `app.py` L13           |
| `assistant_simple.py`     | Ładowany dynamicznie w `app.py` L109 |
| `stt_endpoint.py`         | Ładowany dynamicznie w `app.py` L110 |
| `tts_endpoint.py`         | Ładowany dynamicznie w `app.py` L111 |
| `suggestions_endpoint.py` | Ładowany dynamicznie w `app.py` L112 |
| `internal_endpoint.py`    | Ładowany dynamicznie w `app.py` L113 |
| `files_endpoint.py`       | Ładowany dynamicznie w `app.py` L114 |
| `routers.py`              | Ładowany dynamicznie w `app.py` L115 |
| `writing_endpoint.py`     | Potencjalnie przez core/app.py       |
| `psyche_endpoint.py`      | Potencjalnie przez core/app.py       |
| `travel_endpoint.py`      | Potencjalnie przez core/app.py       |
| `research_endpoint.py`    | Potencjalnie przez core/app.py       |
| `programista_endpoint.py` | Potencjalnie przez core/app.py       |
| `prometheus_endpoint.py`  | Potencjalnie przez core/app.py       |
| `core/*`                  | Importowane przez endpointy          |

#### ORPHAN (brak ścieżki importu)

| Plik                               | Uzasadnienie                         | Decyzja                 |
| ---------------------------------- | ------------------------------------ | ----------------------- |
| `core/app.py`                      | Alternatywny entrypoint, nie używany | → `_legacy/core_app.py` |
| `writer_pro.py`                    | Brak importu nigdzie                 | → `_legacy/`            |
| `autonauka_pro.py`                 | Brak importu nigdzie                 | → `_legacy/`            |
| `sports_news_pro.py`               | Brak importu nigdzie                 | → `_legacy/`            |
| `research.py` (root)               | Duplikat `core/research.py`          | → `_legacy/`            |
| `hierarchical_memory.py` (root)    | Duplikat `core/`                     | → `_legacy/`            |
| `hybrid_search_endpoint.py` (root) | Tylko re-export                      | Usunąć                  |
| `nlp_endpoint.py`                  | Brak importu                         | → `_legacy/` lub dodać  |
| `proactive_suggestions.py`         | Używa core.advanced_proactive        | → `_legacy/`            |
| `example.py`                       | Demo                                 | → `examples/`           |
| `test_web_learn.py`                | Test                                 | → `tests/`              |

#### UTILITY/ARCHIVE

| Plik              | Typ                | Decyzja               |
| ----------------- | ------------------ | --------------------- |
| `patch_*.py` (27) | Jednorazowe patche | → `_archive/patches/` |
| `fix_*.py` (6)    | Naprawy            | → `_archive/fixes/`   |
| `tools_*.py` (8)  | Patche             | → `_archive/tools/`   |
| `*.bak.*` (15+)   | Backupy            | → `_archive/backups/` |
| `deploy.py`       | Deployment         | Zachować              |

### 7.2 Procedura bezpiecznego przeniesienia

```bash
# 1. Utwórz katalogi archiwalne
mkdir -p _legacy _archive/patches _archive/fixes _archive/tools _archive/backups

# 2. Przenieś orphan files
mv core/app.py _legacy/core_app.py
mv writer_pro.py _legacy/
mv autonauka_pro.py _legacy/
mv sports_news_pro.py _legacy/
mv research.py _legacy/research_root.py
mv hierarchical_memory.py _legacy/hierarchical_memory_root.py
mv nlp_endpoint.py _legacy/
mv proactive_suggestions.py _legacy/
mv example.py examples/

# 3. Przenieś patche i fixy
mv patch_*.py _archive/patches/
mv fix_*.py _archive/fixes/
mv tools_*.py _archive/tools/
mv *.bak.* _archive/backups/

# 4. Usuń re-exporty
rm hybrid_search_endpoint.py  # tylko re-export z core
```

### 7.3 BRAKUJĄCE RZECZY - NIE MASKOWANE

| Brak                     | Gdzie importowane        | Pełnoprawna implementacja        |
| ------------------------ | ------------------------ | -------------------------------- |
| `cache_get`, `cache_put` | `core/research.py`       | Patrz sekcja 5.1                 |
| `captcha_endpoint`       | `core/app.py`            | Nie potrzebne - usunąć import    |
| `monolit`                | `files_endpoint.py`      | Stub lub usunąć bloki try/except |
| `middleware` (caches)    | `core/admin_endpoint.py` | Już ma fallback                  |

---

## 8. MIDDLEWARE / AUTH / OBSERVABILITY / TIMEOUTY

### 8.1 Middleware (kolejność w app.py)

| Middleware        | Pozycja        | Status                                    |
| ----------------- | -------------- | ----------------------------------------- |
| CORS              | 1              | ✅ Skonfigurowane (`allow_origins=["*"]`) |
| Prometheus        | 2 (opcjonalne) | ⚠️ Tylko w `core/app.py`                  |
| Exception handler | Ostatni        | ✅ Global handler                         |

**Brakujące:**

- Request ID middleware (dla logów)
- Timing middleware (poza Prometheus)
- GZip compression

### 8.2 Auth - analiza

| Endpoint              | Metoda auth                | Spójność |
| --------------------- | -------------------------- | -------- |
| `/v1/*`               | Bearer + `_require_auth()` | ✅       |
| `/api/chat/*`         | Bearer + `_auth_ok()`      | ✅       |
| `/api/files/*`        | Bearer + `_auth()`         | ✅       |
| `/api/stt/*`          | ❌ BRAK AUTH               | ⚠️ Dodać |
| `/api/tts/*`          | ❌ BRAK AUTH               | ⚠️ Dodać |
| `/api/routers/health` | ❌ BRAK (celowo)           | ✅       |
| `/health`             | ❌ BRAK (celowo)           | ✅       |

### 8.3 Timeouty - external calls

| Call           | Gdzie              | Timeout | Retry        | Naprawa           |
| -------------- | ------------------ | ------- | ------------ | ----------------- |
| LLM API        | `core/llm.py`      | 45s     | 3x + backoff | ✅ OK             |
| DDG search     | `core/research.py` | 45s     | ❌           | Dodać retry       |
| SERPAPI        | `core/research.py` | 45s     | ❌           | Dodać retry       |
| Firecrawl      | `core/research.py` | 45s     | ❌           | Dodać retry       |
| ElevenLabs TTS | `tts_endpoint.py`  | 120s    | ❌           | OK (długie audio) |
| OpenAI Whisper | `stt_endpoint.py`  | 60s     | ❌           | Dodać retry       |

### 8.4 Logging

| Aspekt                   | Status               | Naprawa               |
| ------------------------ | -------------------- | --------------------- |
| Request ID               | ❌ BRAK              | Dodać middleware      |
| Structured logs          | ⚠️ Częściowo (print) | Zamienić na `logging` |
| Log levels               | ⚠️ Tylko w config    | Użyć w praktyce       |
| Request/response logging | ❌ BRAK              | Dodać dla debug       |

---

## 9. PLAN NAPRAWY – CHECKLISTA P0/P1/P2

### 9.1 P0: BLOKUJĄCE START (KRYTYCZNE)

| #    | Plik             | Zmiana                              | Sprawdzenie                                       |
| ---- | ---------------- | ----------------------------------- | ------------------------------------------------- |
| P0.1 | -                | `mkdir static`                      | App startuje bez błędu                            |
| P0.2 | `core/memory.py` | Dodać `cache_get()` i `cache_put()` | `from core.memory import cache_get, cache_put` OK |
| P0.3 | `.env`           | Ustawić `LLM_API_KEY`               | `/health` zwraca `LLM_API_KEY_set: true`          |

**Implementacja P0.2:**

```python
# Dodać na końcu core/memory.py (przed __all__)

# === IN-MEMORY CACHE ===
_MEMORY_CACHE: Dict[str, Tuple[Any, float]] = {}

def cache_get(key: str, ttl: float = 3600) -> Optional[Any]:
    """Get value from in-memory cache if not expired"""
    if key in _MEMORY_CACHE:
        value, timestamp = _MEMORY_CACHE[key]
        if time.time() - timestamp < ttl:
            return value
        del _MEMORY_CACHE[key]
    return None

def cache_put(key: str, value: Any) -> None:
    """Put value in in-memory cache with current timestamp"""
    _MEMORY_CACHE[key] = (value, time.time())

# Dodać do __all__:
# "cache_get", "cache_put"
```

### 9.2 P1: BLOKUJĄCE KLUCZOWE FUNKCJE

| #    | Plik                            | Zmiana                           | Sprawdzenie       |
| ---- | ------------------------------- | -------------------------------- | ----------------- |
| P1.1 | `files_endpoint.py`             | Usunąć/stubować import `monolit` | Upload działa     |
| P1.2 | `stt_endpoint.py`               | Dodać auth dependency            | STT wymaga tokena |
| P1.3 | `tts_endpoint.py`               | Dodać auth dependency            | TTS wymaga tokena |
| P1.4 | `core/app.py`                   | Usunąć import `captcha_endpoint` | -                 |
| P1.5 | `prometheus_endpoint.py` (root) | Dodać prefix `/api/prometheus`   | Brak konfliktu    |

**Implementacja P1.1 (files_endpoint.py):**

```python
# Zamienić:
import monolit as M
if hasattr(M, 'files_save'):
    M.files_save([...])

# Na:
# Usunąć cały blok - files_save nie jest krytyczne
```

### 9.3 P2: PORZĄDKI I TECH DEBT

| #    | Opis                                 | Pliki               | Sprawdzenie                 |
| ---- | ------------------------------------ | ------------------- | --------------------------- |
| P2.1 | Przenieść orphan files do `_legacy/` | 10+ plików          | Folder `_legacy/` istnieje  |
| P2.2 | Przenieść patche do `_archive/`      | 40+ plików          | Folder `_archive/` istnieje |
| P2.3 | Usunąć duplikat `core/app.py`        | 1 plik              | Plik w `_legacy/`           |
| P2.4 | Dodać `.env.example`                 | Nowy plik           | Plik istnieje               |
| P2.5 | Ujednolicić nazewnictwo auth         | Wszystkie endpointy | `_auth()` wszędzie          |
| P2.6 | Dodać request_id middleware          | `app.py`            | Logi mają request_id        |
| P2.7 | Zamienić `print()` na `logging`      | Wszystkie           | Structured logs             |

### 9.4 Definition of Done

```bash
# 1. Start bez błędów
cd /path/to/mrd
python -c "import app; print('OK')"

# 2. Uvicorn startuje
uvicorn app:app --host 0.0.0.0 --port 8080

# 3. Health check
curl http://localhost:8080/health
# → {"status": "healthy", "version": "5.0.0", ...}

# 4. Docs działają
curl http://localhost:8080/docs
# → HTML strona

# 5. OpenAPI schema
curl http://localhost:8080/openapi.json | jq '.info.title'
# → "Mordzix AI"

# 6. Chat działa (z tokenem)
curl -X POST http://localhost:8080/api/chat/assistant \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_id": "test"}'
# → {"answer": "...", ...}

# 7. Stream działa
curl -X POST http://localhost:8080/api/chat/assistant/stream \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_id": "test"}'
# → SSE events

# 8. Router status
curl http://localhost:8080/api/routers/status \
  -H "Authorization: Bearer $AUTH_TOKEN"
# → {"loaded": [...], "failed": []}
```

---

## 10. FRONTEND SPECYFIKACJA

### 10.1 UX jak ChatGPT/Grok

| Element         | Opis                                                               |
| --------------- | ------------------------------------------------------------------ |
| **Sidebar**     | Historia czatów, tworzenie nowego, usuwanie, edycja tytułu         |
| **Main chat**   | Streaming tokenów, markdown render, code blocks z syntax highlight |
| **Input**       | Textarea auto-resize, Shift+Enter dla newline, Enter send          |
| **Attachments** | Drag & drop, preview, progress bar                                 |
| **Citations**   | Linki do źródeł jeśli research                                     |
| **Copy button** | Na każdej odpowiedzi AI                                            |
| **Regenerate**  | Ponowne wygenerowanie odpowiedzi                                   |
| **Edit**        | Edycja poprzedniej wiadomości user                                 |

### 10.2 Sessions

| Aspekt            | Implementacja                                      |
| ----------------- | -------------------------------------------------- |
| **Local storage** | `localStorage` dla draft, history list             |
| **Server sync**   | `session_id` w każdym requeście                    |
| **Autosave**      | Co 5s draft, po każdej odpowiedzi history          |
| **Restore**       | Przy ładowaniu strony sprawdź local + fetch server |

### 10.3 Upload flow

```
1. User wybiera pliki (drag & drop lub button)
2. Walidacja (typ, rozmiar)
3. Preview (obrazy, nazwy plików)
4. Upload queue z progress bars
5. Po sukcesie: attachment ID w wiadomości
6. Retry button przy błędzie
```

### 10.4 Streaming states

| State       | UI                                |
| ----------- | --------------------------------- |
| `idle`      | Input aktywny, czeka na wiadomość |
| `sending`   | Spinner, input disabled           |
| `streaming` | Tokeny pojawiają się, stop button |
| `complete`  | Pełna odpowiedź, input aktywny    |
| `error`     | Error message, retry button       |

### 10.5 Tech stack

| Warstwa    | Technologia                       |
| ---------- | --------------------------------- |
| Framework  | React 18+                         |
| Build      | Vite                              |
| Language   | TypeScript                        |
| Styling    | Tailwind CSS                      |
| State      | Zustand                           |
| API client | Fetch + custom wrapper            |
| SSE        | EventSource lub custom            |
| Markdown   | react-markdown + rehype-highlight |
| Icons      | Lucide React                      |

### 10.6 Komponenty

```
src/
├── components/
│   ├── Chat/
│   │   ├── ChatContainer.tsx
│   │   ├── MessageList.tsx
│   │   ├── Message.tsx
│   │   ├── UserMessage.tsx
│   │   ├── AssistantMessage.tsx
│   │   ├── StreamingMessage.tsx
│   │   ├── InputArea.tsx
│   │   └── AttachmentPreview.tsx
│   ├── Sidebar/
│   │   ├── Sidebar.tsx
│   │   ├── ConversationList.tsx
│   │   ├── ConversationItem.tsx
│   │   └── NewChatButton.tsx
│   ├── Common/
│   │   ├── Button.tsx
│   │   ├── Spinner.tsx
│   │   ├── CodeBlock.tsx
│   │   └── MarkdownRenderer.tsx
│   └── Layout/
│       ├── AppLayout.tsx
│       └── Header.tsx
├── hooks/
│   ├── useChat.ts
│   ├── useStream.ts
│   ├── useAuth.ts
│   └── useLocalStorage.ts
├── stores/
│   ├── chatStore.ts
│   └── authStore.ts
├── api/
│   ├── client.ts
│   ├── chat.ts
│   └── files.ts
└── types/
    └── index.ts
```

### 10.7 Wymagania backendu pod frontend

| Wymaganie     | Endpoint                          | Status     |
| ------------- | --------------------------------- | ---------- |
| Lista sesji   | `GET /api/sessions`               | ❌ BRAKUJE |
| Pobierz sesję | `GET /api/sessions/{id}`          | ❌ BRAKUJE |
| Usuń sesję    | `DELETE /api/sessions/{id}`       | ❌ BRAKUJE |
| Zmień tytuł   | `PATCH /api/sessions/{id}`        | ❌ BRAKUJE |
| Chat sync     | `POST /api/chat/assistant`        | ✅         |
| Chat stream   | `POST /api/chat/assistant/stream` | ✅         |
| Upload file   | `POST /api/files/upload`          | ✅         |
| List files    | `GET /api/files/list`             | ✅         |
| Delete file   | `DELETE /api/files/{id}`          | ✅         |
| UI token      | `GET /api/internal/ui_token`      | ✅         |

**Do dodania:**

```python
# sessions_endpoint.py

@router.get("/api/sessions")
async def list_sessions(user_id: str, limit: int = 50):
    """Lista sesji użytkownika z tytułami"""

@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Pełna historia sesji"""

@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Usuń sesję"""

@router.patch("/api/sessions/{session_id}")
async def update_session(session_id: str, title: str = None):
    """Zmień tytuł sesji"""
```

---

## 11. BOOST – OPCJONALNE ULEPSZENIA

### 11.1 Performance

| Co                 | Gdzie                    | Po co              | Jak sprawdzić                      |
| ------------------ | ------------------------ | ------------------ | ---------------------------------- |
| Redis cache        | `core/memory.py`         | Szybsze cache      | Response time < 50ms dla cache hit |
| Connection pooling | `core/llm.py`            | Mniej TCP overhead | Mniejsze latency                   |
| Async SQLite       | `core/memory.py`         | Non-blocking DB    | Lepsze p99                         |
| Batch LLM calls    | `core/batch_endpoint.py` | Throughput         | Requests/sec                       |

### 11.2 Reliability

| Co                 | Gdzie         | Po co      | Jak sprawdzić        |
| ------------------ | ------------- | ---------- | -------------------- |
| Circuit breaker    | LLM/API calls | Failover   | Graceful degradation |
| Health checks      | `/health`     | Monitoring | Uptime               |
| Structured logging | Wszystkie     | Debug      | Log aggregation      |
| Request tracing    | Middleware    | Debug      | Correlation ID       |

### 11.3 Security

| Co               | Gdzie                   | Po co                | Jak sprawdzić        |
| ---------------- | ----------------------- | -------------------- | -------------------- |
| Rate limiting    | Middleware              | DDoS protection      | 429 po przekroczeniu |
| Input validation | Endpointy               | Injection prevention | Pydantic errors      |
| HTTPS            | Deployment              | Encryption           | SSL cert             |
| JWT rotation     | `/api/admin/jwt/rotate` | Key security         | Rotate co 24h        |

### 11.4 DX (Developer Experience)

| Co         | Gdzie     | Po co        | Jak sprawdzić    |
| ---------- | --------- | ------------ | ---------------- |
| Hot reload | Uvicorn   | Szybki dev   | `--reload` flag  |
| Type hints | Wszystkie | IDE support  | mypy passes      |
| Docstrings | Endpointy | OpenAPI docs | `/docs` complete |
| Tests      | `tests/`  | Regression   | pytest passes    |

---

## APPENDIX A: SZYBKA NAPRAWA (5 MINUT)

```bash
# 1. Utwórz brakujący folder
mkdir -p static

# 2. Utwórz .env
cat > .env << 'EOF'
LLM_API_KEY=your_key_here
AUTH_TOKEN=your_secure_token_here
LLM_BASE_URL=https://api.deepinfra.com/v1/openai
LLM_MODEL=Qwen/Qwen3-Next-80B-A3B-Instruct
EOF

# 3. Dodaj cache functions do core/memory.py
# (patrz sekcja 9.1 P0.2)

# 4. Test
python -c "import app; print('OK')"
uvicorn app:app --port 8080
```

---

## APPENDIX B: GRAF IMPORTÓW (GŁÓWNE MODUŁY)

```
app.py
├── openai_compat.router
├── assistant_simple.router
│   └── [standalone - own LLM client]
├── stt_endpoint.router
├── tts_endpoint.router
├── suggestions_endpoint.router
│   └── core.advanced_proactive (fallback)
├── internal_endpoint.router
├── files_endpoint.router
│   └── [monolit - MISSING]
├── routers.router
│   ├── core.config.AUTH_TOKEN
│   ├── core.auth.auth_dependency
│   ├── core.memory._db, psy_get
│   └── system_stats
│
├── core.assistant_endpoint.router
│   ├── core.cognitive_engine
│   │   ├── core.config
│   │   ├── core.llm
│   │   ├── core.memory.memory_manager
│   │   ├── core.hierarchical_memory
│   │   ├── core.advanced_cognitive_engine
│   │   └── core.research (FAIL: cache_get)
│   └── core.memory
│
├── core.memory_endpoint.router
│   └── core.memory_store
│
├── core.cognitive_endpoint.router
│   └── core.self_reflection
│
├── core.negocjator_endpoint.router
├── core.reflection_endpoint.router
├── core.legal_office_endpoint.router
├── core.hybrid_search_endpoint.router
├── core.batch_endpoint.router
└── core.prometheus_endpoint.router
```

---

**Koniec raportu audytu.**

_Wygenerowano: 26 grudnia 2025_
_Autor: GitHub Copilot (Claude Opus 4.5)_
