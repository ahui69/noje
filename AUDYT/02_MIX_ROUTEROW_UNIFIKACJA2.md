# 02. MIX ROUTERÓW / FRAMEWORKÓW + PLAN UNIFIKACJI

**Data audytu:** 26 grudnia 2025  
**Zakres:** Wszystkie pliki definiujące routery FastAPI w `mrd/**`

---

## 0. ŚRODOWISKO AUDYTU

| Parametr                     | Wartość                                   |
| ---------------------------- | ----------------------------------------- |
| **System**                   | Linux (bash)                              |
| **Katalog roboczy**          | `mrd/`                                    |
| **Entrypoint analizowany**   | `./app.py` (❓ PODEJRZENIE — patrz niżej) |
| **Metoda wykrycia routerów** | `grep -rn "APIRouter" --include="*.py"`   |

### Entrypoint — status weryfikacji

| Plik            | Dowód użycia produkcyjnego                                                                         | Status          |
| --------------- | -------------------------------------------------------------------------------------------------- | --------------- |
| `./app.py`      | **BRAK DOWODU** — brak `Dockerfile`, `docker-compose.yml`, `systemd/*.service`, `start*.sh` w repo | ❓ PODEJRZENIE  |
| `./core/app.py` | Ma `uvicorn.run()` w L:639 ale to fallback                                                         | ⚠️ ALTERNATYWNY |

**Do ustalenia:** Sprawdzić na serwerze produkcyjnym:

```bash
# Jak uruchamiana jest aplikacja?
ps aux | grep -E 'uvicorn|gunicorn|python.*app'
systemctl list-units | grep mrd
docker ps | grep mrd
```

**UWAGA:** Dopóki nie ma dowodu, przyjmujemy `./app.py` jako entrypoint na podstawie:

- Jest w katalogu root (standardowa lokalizacja)
- Ma pełną logikę ładowania routerów (L:82-161)
- Komentarz w kodzie: `# MORDZIX AI PRO - Main Application`

---

## 1. WYKRYTE FRAMEWORKI I WZORCE

### 1.1. Framework główny

| Framework     | Wersja     | Status                                  | Źródło                    |
| ------------- | ---------- | --------------------------------------- | ------------------------- |
| **FastAPI**   | >= 0.115.0 | ✅ Jedyny framework webowy              | `./requirements.txt` L:7  |
| **Starlette** | >= 0.40.0  | ✅ Bazowy (automatycznie przez FastAPI) | `./requirements.txt` L:13 |
| **Pydantic**  | >= 2.9.0   | ✅ Walidacja request/response           | `./requirements.txt` L:10 |
| **uvicorn**   | >= 0.30.0  | ✅ ASGI server                          | `./requirements.txt` L:8  |

**Cytat z `./requirements.txt` L:7-13:**

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
pydantic>=2.9.0
jinja2>=3.1.0
aiofiles>=23.2.0
starlette>=0.40.0
```

**Wniosek:** Brak mieszanki frameworków (nie ma Flask, Django, Bottle itp.). Projekt używa wyłącznie FastAPI.

### 1.2. Wzorce definiowania routerów

| Wzorzec                                     | Ilość | Pliki                                  | Problem                                            |
| ------------------------------------------- | ----- | -------------------------------------- | -------------------------------------------------- |
| `router = APIRouter(prefix="/api/xxx")`     | 28    | Większość endpointów                   | ✅ OK                                              |
| `router = APIRouter()` (bez prefixu)        | 2     | `prometheus_endpoint.py` (root + core) | ⚠️ Prefix dodawany w include_router                |
| `writer_router = APIRouter(...)`            | 1     | `writer_pro.py`                        | ⚠️ Nazwa nie `router` - nie ładowany automatycznie |
| Prefix w routerze + prefix w include_router | 1     | `core/app.py` L:307, L:317             | ❌ Potencjalny `/api/api/`                         |

---

## 2. PEŁNA LISTA ROUTERÓW (35 DEFINICJI)

### 2.1. Routery w ROOT `mrd/` (18 definicji)

| #   | Plik                                                   | Linia | Definicja                                                                       | Prefix             | Tags                  | Status                       |
| --- | ------------------------------------------------------ | ----- | ------------------------------------------------------------------------------- | ------------------ | --------------------- | ---------------------------- |
| 1   | [openai_compat.py](openai_compat.py)                   | 15    | `router = APIRouter(prefix="/v1", tags=["openai_compat"])`                      | `/v1`              | openai_compat         | ✅ Ładowany                  |
| 2   | [assistant_simple.py](assistant_simple.py)             | 203   | `router = APIRouter(prefix="/api/chat", tags=["chat"])`                         | `/api/chat`        | chat                  | ✅ Ładowany                  |
| 3   | [assistant_endpoint.py](assistant_endpoint.py)         | 40    | `router = APIRouter(prefix="/api/chat")`                                        | `/api/chat`        | brak                  | ⚠️ NIEPODPIĘTY (CONFLICT P0) |
| 4   | [stt_endpoint.py](stt_endpoint.py)                     | 15    | `router = APIRouter(prefix="/api/stt", tags=["speech"])`                        | `/api/stt`         | speech                | ✅ Ładowany                  |
| 5   | [tts_endpoint.py](tts_endpoint.py)                     | 17    | `router = APIRouter(prefix="/api/tts", tags=["tts"])`                           | `/api/tts`         | tts                   | ✅ Ładowany                  |
| 6   | [suggestions_endpoint.py](suggestions_endpoint.py)     | 40-42 | `router = APIRouter(prefix="/api/suggestions", tags=["Proactive Suggestions"])` | `/api/suggestions` | Proactive Suggestions | ✅ Ładowany                  |
| 7   | [internal_endpoint.py](internal_endpoint.py)           | 11    | `router = APIRouter(prefix="/api/internal")`                                    | `/api/internal`    | brak                  | ✅ Ładowany                  |
| 8   | [files_endpoint.py](files_endpoint.py)                 | 15    | `router = APIRouter(prefix="/api/files")`                                       | `/api/files`       | brak                  | ✅ Ładowany                  |
| 9   | [routers.py](routers.py)                               | 28-30 | `router = APIRouter(prefix="/api/routers", tags=["routers"])`                   | `/api/routers`     | routers               | ✅ Ładowany                  |
| 10  | [writing_endpoint.py](writing_endpoint.py)             | 26    | `router = APIRouter(prefix="/api/writing")`                                     | `/api/writing`     | brak                  | ⚠️ NIEPODPIĘTY (pkt 07)      |
| 11  | [psyche_endpoint.py](psyche_endpoint.py)               | 26    | `router = APIRouter(prefix="/api/psyche")`                                      | `/api/psyche`      | brak                  | ⚠️ NIEPODPIĘTY (pkt 07)      |
| 12  | [travel_endpoint.py](travel_endpoint.py)               | 18    | `router = APIRouter(prefix="/api/travel")`                                      | `/api/travel`      | brak                  | ⚠️ NIEPODPIĘTY (pkt 07)      |
| 13  | [research_endpoint.py](research_endpoint.py)           | 15    | `router = APIRouter(prefix="/api/research", tags=["research"])`                 | `/api/research`    | research              | ⚠️ NIEPODPIĘTY (pkt 07)      |
| 14  | [programista_endpoint.py](programista_endpoint.py)     | 17    | `router = APIRouter(prefix="/api/code")`                                        | `/api/code`        | brak                  | ⚠️ NIEPODPIĘTY (pkt 07)      |
| 15  | [prometheus_endpoint.py](prometheus_endpoint.py)       | 12    | `router = APIRouter()`                                                          | **BRAK**           | brak                  | ⚠️ NIEPODPIĘTY + bez prefix! |
| 16  | [nlp_endpoint.py](nlp_endpoint.py)                     | 23    | `router = APIRouter(prefix="/api/nlp", tags=["nlp"])`                           | `/api/nlp`         | nlp                   | ⚠️ NIEPODPIĘTY (pkt 07)      |
| 17  | [hybrid_search_endpoint.py](hybrid_search_endpoint.py) | -     | Re-eksport z core                                                               | -                  | -                     | ⚠️ Re-export                 |
| 18  | [writer_pro.py](writer_pro.py)                         | 96-98 | `writer_router = APIRouter(prefix="/api/writer", tags=["writing"])`             | `/api/writer`      | writing               | ⚠️ NIEPODPIĘTY (zła nazwa)   |

### 2.2. Routery w CORE `mrd/core/` (17 definicji)

| #   | Plik                                                        | Linia | Definicja                                                                       | Prefix                | Tags                  | Status                                     |
| --- | ----------------------------------------------------------- | ----- | ------------------------------------------------------------------------------- | --------------------- | --------------------- | ------------------------------------------ |
| 1   | [assistant_endpoint.py](core/assistant_endpoint.py)         | 40    | `router = APIRouter(prefix="/api/chat")`                                        | `/api/chat`           | brak                  | ✅ Ładowany jako "core.assistant_endpoint" |
| 2   | [memory_endpoint.py](core/memory_endpoint.py)               | 9     | `router = APIRouter(prefix="/api/memory", tags=["memory"])`                     | `/api/memory`         | memory                | ✅ Ładowany                                |
| 3   | [cognitive_endpoint.py](core/cognitive_endpoint.py)         | 14    | `router = APIRouter(prefix="/api/cognitive", tags=["cognitive"])`               | `/api/cognitive`      | cognitive             | ✅ Ładowany                                |
| 4   | [negocjator_endpoint.py](core/negocjator_endpoint.py)       | 26    | `router = APIRouter(prefix="/api/negocjator", tags=["AI Negocjator"])`          | `/api/negocjator`     | AI Negocjator         | ✅ Ładowany                                |
| 5   | [reflection_endpoint.py](core/reflection_endpoint.py)       | 21-23 | `router = APIRouter(prefix="/api/reflection", tags=["Self-Reflection"])`        | `/api/reflection`     | Self-Reflection       | ✅ Ładowany                                |
| 6   | [legal_office_endpoint.py](core/legal_office_endpoint.py)   | 49    | `router = APIRouter(prefix="/api/legal", tags=["Legal Office"])`                | `/api/legal`          | Legal Office          | ✅ Ładowany                                |
| 7   | [hybrid_search_endpoint.py](core/hybrid_search_endpoint.py) | 20    | `router = APIRouter(prefix="/api/search", tags=["search"])`                     | `/api/search`         | search                | ✅ Ładowany                                |
| 8   | [batch_endpoint.py](core/batch_endpoint.py)                 | 45-47 | `router = APIRouter(prefix="/api/batch", tags=["batch"])`                       | `/api/batch`          | batch                 | ✅ Ładowany                                |
| 9   | [prometheus_endpoint.py](core/prometheus_endpoint.py)       | 12    | `router = APIRouter()`                                                          | **BRAK**              | brak                  | ✅ Ładowany z prefix w include_router      |
| 10  | [admin_endpoint.py](core/admin_endpoint.py)                 | 24    | `router = APIRouter(prefix="/api/admin")`                                       | `/api/admin`          | brak                  | ⚠️ NIEPODPIĘTY (pkt 07)                    |
| 11  | [hacker_endpoint.py](core/hacker_endpoint.py)               | 26    | `router = APIRouter(prefix="/api/hacker", tags=["AI Hacker Assistant"])`        | `/api/hacker`         | AI Hacker Assistant   | ⚠️ NIEPODPIĘTY (pkt 07)                    |
| 12  | [chat_advanced_endpoint.py](core/chat_advanced_endpoint.py) | 28    | `router = APIRouter(prefix="/core/chat/advanced", tags=["core-chat-advanced"])` | `/core/chat/advanced` | core-chat-advanced    | ⚠️ NIEPODPIĘTY (pkt 07)                    |
| 13  | [auction_endpoint.py](core/auction_endpoint.py)             | 17    | `router = APIRouter(prefix="/api/auction", tags=["AI Auction"])`                | `/api/auction`        | AI Auction            | ⚠️ NIEPODPIĘTY (pkt 07)                    |
| 14  | [research_endpoint.py](core/research_endpoint.py)           | 15    | `router = APIRouter(prefix="/api/research", tags=["research"])`                 | `/api/research`       | research              | ⚠️ NIEPODPIĘTY (CONFLICT P0)               |
| 15  | [psyche_endpoint.py](core/psyche_endpoint.py)               | 26    | `router = APIRouter(prefix="/api/psyche")`                                      | `/api/psyche`         | brak                  | ⚠️ NIEPODPIĘTY (CONFLICT P0)               |
| 16  | [suggestions_endpoint.py](core/suggestions_endpoint.py)     | 23-25 | `router = APIRouter(prefix="/api/suggestions", tags=["Proactive Suggestions"])` | `/api/suggestions`    | Proactive Suggestions | ⚠️ NIEPODPIĘTY (root podpięty)             |

---

## 3. PROBLEMY WYKRYTE

### 3.1. P1: Router bez prefixu - wymaga prefix przy include_router

| Plik                                                       | Problem                           | Linia | Skutek                             | Naprawa                            |
| ---------------------------------------------------------- | --------------------------------- | ----- | ---------------------------------- | ---------------------------------- |
| [prometheus_endpoint.py](prometheus_endpoint.py) (root)    | `router = APIRouter()` bez prefix | L:12  | Endpointy na `/metrics`, `/health` | Dodać `prefix="/api/prometheus"`   |
| [core/prometheus_endpoint.py](core/prometheus_endpoint.py) | `router = APIRouter()` bez prefix | L:12  | Zależny od include_router          | OK jeśli core/app.py dodaje prefix |

**Analiza core/app.py L:317:**

```python
app.include_router(prometheus_endpoint.router, prefix="/api/prometheus", tags=["monitoring"])
```

✅ Core dodaje prefix przy include - poprawne.

**Problem:** Root `prometheus_endpoint.py` NIE jest ładowany przez `app.py`, ale gdyby był - miałby endpointy na `/metrics` zamiast `/api/prometheus/metrics`.

### 3.2. P1: Zła nazwa routera - nie zostanie wykryty przez dynamiczny import

| Plik                           | Problem                                           | Linia | Skutek                                     | Naprawa                              |
| ------------------------------ | ------------------------------------------------- | ----- | ------------------------------------------ | ------------------------------------ |
| [writer_pro.py](writer_pro.py) | `writer_router = APIRouter(...)` zamiast `router` | L:96  | `_try_import_router()` szuka `router` attr | Zmienić na `router = APIRouter(...)` |

**Kod w app.py szukający routera (L:85-87):**

```python
m = importlib.import_module(modname)
r = getattr(m, "router", None)  # <-- szuka "router"
if r is None:
    return None, "no router attr"
```

### 3.3. RYZYKA HIPOTETYCZNE (nieistniejący kod)

| Ryzyko                      | Opis                                                                        | Status                                                       |
| --------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Podwójny prefix `/api/api/` | Jeśli ktoś doda router z prefixem do `include_router()` które też ma prefix | 🟡 HIPOTETYCZNE — workaround istnieje w `./app.py` L:224-255 |

**Workaround w `./app.py` L:224-255:**

```python
def _mrd__auto_alias_double_api_prefix(app):
    # Dodaje aliasy /api/... dla /api/api/...
```

**UWAGA:** `captcha_endpoint` nie istnieje w repo — usunięto z audytu jako nieistniejący.

### 3.4. P2: Brakujące tagi (OpenAPI docs mniej czytelne)

| Plik                                                     | Prefix          | Brak `tags=` | Naprawa                        |
| -------------------------------------------------------- | --------------- | ------------ | ------------------------------ |
| [assistant_endpoint.py](assistant_endpoint.py)           | `/api/chat`     | ✅ brak      | Dodać `tags=["chat"]`          |
| [internal_endpoint.py](internal_endpoint.py)             | `/api/internal` | ✅ brak      | Dodać `tags=["internal"]`      |
| [files_endpoint.py](files_endpoint.py)                   | `/api/files`    | ✅ brak      | Dodać `tags=["files"]`         |
| [writing_endpoint.py](writing_endpoint.py)               | `/api/writing`  | ✅ brak      | Dodać `tags=["writing"]`       |
| [psyche_endpoint.py](psyche_endpoint.py)                 | `/api/psyche`   | ✅ brak      | Dodać `tags=["psyche"]`        |
| [travel_endpoint.py](travel_endpoint.py)                 | `/api/travel`   | ✅ brak      | Dodać `tags=["travel"]`        |
| [programista_endpoint.py](programista_endpoint.py)       | `/api/code`     | ✅ brak      | Dodać `tags=["code"]`          |
| [core/assistant_endpoint.py](core/assistant_endpoint.py) | `/api/chat`     | ✅ brak      | Dodać `tags=["chat-advanced"]` |
| [core/admin_endpoint.py](core/admin_endpoint.py)         | `/api/admin`    | ✅ brak      | Dodać `tags=["admin"]`         |

### 3.5. P2: Niespójne nazewnictwo tagów

| Tag                     | Pliki                    | Problem              |
| ----------------------- | ------------------------ | -------------------- |
| `speech` vs `stt`       | stt_endpoint.py          | Niespójne z prefixem |
| `Proactive Suggestions` | suggestions_endpoint.py  | Spacje, Title Case   |
| `AI Negocjator`         | negocjator_endpoint.py   | Spacje, polski       |
| `AI Hacker Assistant`   | hacker_endpoint.py       | Spacje               |
| `Legal Office`          | legal_office_endpoint.py | Spacje               |
| `Self-Reflection`       | reflection_endpoint.py   | Myślnik              |

**Docelowy standard:**

```python
# Tagi: lowercase, bez spacji, myślniki zamiast underscore
tags=["stt"]
tags=["suggestions"]
tags=["negocjator"]
tags=["hacker"]
tags=["legal"]
tags=["reflection"]
```

---

## 4. MECHANIZMY ŁADOWANIA ROUTERÓW

### 4.1. app.py - Dynamiczne ładowanie (L:82-161)

```python
# Mechanizm
def _try_import_router(modname: str) -> Tuple[Optional[Any], Optional[str]]:
    m = importlib.import_module(modname)
    r = getattr(m, "router", None)  # SZUKA ATRYBUTU "router"
    return r, None

# Lista root_modules (L:104-112)
root_modules = [
    ("assistant_simple", "Chat (Commercial)"),
    ("stt_endpoint", "STT"),
    ("tts_endpoint", "TTS"),
    ("suggestions_endpoint", "Suggestions"),
    ("internal_endpoint", "Internal"),
    ("files_endpoint", "Files"),
    ("routers", "Admin/Debug"),
]

# Lista core_modules (L:134-144)
core_modules = [
    ("core.assistant_endpoint", "Chat (Advanced)"),
    ("core.memory_endpoint", "Memory"),
    ("core.cognitive_endpoint", "Cognitive"),
    ("core.negocjator_endpoint", "Negotiator"),
    ("core.reflection_endpoint", "Reflection"),
    ("core.legal_office_endpoint", "Legal Office"),
    ("core.hybrid_search_endpoint", "Hybrid Search"),
    ("core.batch_endpoint", "Batch Processing"),
    ("core.prometheus_endpoint", "Metrics"),
]
```

**Cechy:**

- ✅ Graceful degradation (nieudane importy nie blokują startu)
- ✅ Logowanie sukcesu/porażki
- ❌ Szuka tylko atrybutu `router` (nie wykryje `writer_router`)
- ❌ Nie ładuje wszystkich dostępnych routerów

### 4.2. core/app.py - Statyczne ładowanie (L:241-377)

```python
# Wzorzec
try:
    import assistant_endpoint
    app.include_router(assistant_endpoint.router)
    print("✓ Assistant endpoint")
except Exception as e:
    print(f"✗ Assistant endpoint: {e}")
```

**Cechy:**

- ✅ Graceful degradation
- ✅ Pozwala na dodanie prefix/tags przy include_router
- ❌ Hardcoded imports
- ❌ Nie jest używany (core/app.py to alternatywny entrypoint)

---

## 5. WZORCE AUTORYZACJI W ROUTERACH

### 5.1. Wykryte wzorce

| Wzorzec                                      | Ilość | Pliki                                  | Bezpieczeństwo           |
| -------------------------------------------- | ----- | -------------------------------------- | ------------------------ |
| `def _auth(req: Request)` + `Depends(_auth)` | 8     | writing, travel, psyche, routers, ...  | ⚠️ Lokalna funkcja       |
| `Depends(auth_dependency)`                   | 4     | suggestions_endpoint, core/...         | ✅ Centralna z core.auth |
| `_auth_dep` (alias)                          | 3     | routers.py, writer_pro.py              | ⚠️ Lokalna kopia         |
| **Brak auth**                                | 5     | stt_endpoint, prometheus_endpoint, ... | ❌ NIEBEZPIECZNE         |

### 5.2. Endpointy BEZ autoryzacji — ANALIZA RYZYKA

#### A) STT/TTS — ⚠️ RYZYKO KOSZTOWE

| Plik                | Endpointy                  | Ryzyko                       | Wpływ                  |
| ------------------- | -------------------------- | ---------------------------- | ---------------------- |
| `./stt_endpoint.py` | `POST /api/stt/transcribe` | Zużycie API Whisper/zewn.    | 🟡 Średni — koszty API |
| `./stt_endpoint.py` | `GET /api/stt/providers`   | Info o providerach           | 🟢 Niski               |
| `./tts_endpoint.py` | `POST /api/tts/speak`      | Zużycie API ElevenLabs/zewn. | 🟠 Wysoki — koszty API |
| `./tts_endpoint.py` | `GET /api/tts/voices`      | Info o głosach               | 🟢 Niski               |

**Opcje naprawy:**

| Opcja                                | Opis                                        | Implementacja                                               |
| ------------------------------------ | ------------------------------------------- | ----------------------------------------------------------- |
| **A1: Auth wymagany**                | Wszystkie endpointy wymagają tokenu         | Dodać `dependencies=[Depends(auth_dependency)]` do routerów |
| **A2: Auth opcjonalny + rate-limit** | Bez tokenu: limit 10 req/min + allowlist IP | Middleware z `slowapi` + `ALLOWED_IPS` env                  |

**Rekomendacja:** Opcja A1 dla produkcji, A2 dla demo/dev.

#### B) Monitoring — ✅ OK (z zastrzeżeniem)

| Plik                            | Endpointy      | Ryzyko                | Wpływ                  |
| ------------------------------- | -------------- | --------------------- | ---------------------- |
| `./core/prometheus_endpoint.py` | `GET /metrics` | Info o stanie systemu | 🟢 Niski (standardowe) |
| `./core/prometheus_endpoint.py` | `GET /health`  | Health check          | 🟢 Brak                |

**Status:** ✅ OK dla monitoring (Prometheus/Grafana wymaga dostępu).

**Opcjonalne zabezpieczenie:**

```python
# Ograniczenie do sieci wewnętrznej:
@router.get("/metrics")
async def metrics(request: Request):
    if not request.client.host.startswith(("10.", "172.", "192.168.")):
        raise HTTPException(403, "Internal only")
    ...
```

#### C) Internal — ✅ ZABEZPIECZONE

| Plik                     | Endpoint                     | Mechanizm zabezpieczenia               |
| ------------------------ | ---------------------------- | -------------------------------------- |
| `./internal_endpoint.py` | `GET /api/internal/ui_token` | Localhost-only lub `UI_EXPOSE_TOKEN=1` |

### 5.3. Analiza internal_endpoint.py

```python
# L:11-25
@router.get("/ui_token")
async def get_ui_token(req: Request):
    # Zwraca token tylko jeśli:
    # 1. UI_EXPOSE_TOKEN=1 w env, LUB
    # 2. Request pochodzi z localhost
    if os.getenv("UI_EXPOSE_TOKEN") == "1":
        return {"token": os.getenv("AUTH_TOKEN", "")}
    if req.client and req.client.host in ("127.0.0.1", "::1", "localhost"):
        return {"token": os.getenv("AUTH_TOKEN", "")}
    raise HTTPException(403, "Forbidden")
```

✅ Zabezpieczone - token tylko dla localhost lub gdy jawnie włączone.

---

## 6. PLAN UNIFIKACJI

### 6.0. DECYZJA ARCHITEKTONICZNA: allowlist vs autoload

| Opcja                  | Opis                                                       | Zalety                                        | Wady                                                 |
| ---------------------- | ---------------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------- |
| **ALLOWLIST** (obecne) | Listy `root_modules` i `core_modules` w `./app.py`         | Kontrola co jest eksponowane, jawne włączanie | Wymaga ręcznego dodawania nowych routerów            |
| **AUTOLOAD**           | Automatyczne skanowanie `*_endpoint.py` + atrybut `router` | Zero konfiguracji                             | Ryzyko przypadkowego eksponowania WIP/testowego kodu |

**DECYZJA: ALLOWLIST (utrzymujemy obecny model)**

**Uzasadnienie:** W projekcie z wieloma routerami w różnych stanach gotowości (NIEPODPIĘTE, WIP, testy) jawna kontrola przez allowlist zapobiega przypadkowemu eksponowaniu niekompletnego kodu. Nowe routery dodajemy świadomie do list `root_modules`/`core_modules` — 1 linijka w `./app.py`.

### 6.1. Docelowy standard routera

```python
# WZORZEC REFERENCYJNY

from fastapi import APIRouter, Depends, Request, HTTPException
from core.auth import auth_dependency
from core.config import AUTH_TOKEN

router = APIRouter(
    prefix="/api/domain",      # Zawsze z prefixem
    tags=["domain"],           # Lowercase, bez spacji
    dependencies=[Depends(auth_dependency)]  # Globalna auth dla routera
)

@router.get("/endpoint")
async def get_endpoint():
    """Dokumentacja endpointu dla OpenAPI."""
    return {"ok": True}
```

### 6.2. Zmiany do wykonania

#### A) Dodać brakujące routery do app.py

| Plik                   | Dodać do       | Linia  | Kod                                          |
| ---------------------- | -------------- | ------ | -------------------------------------------- |
| `writing_endpoint`     | `root_modules` | ~L:112 | `("writing_endpoint", "Writing"),`           |
| `psyche_endpoint`      | `root_modules` | ~L:112 | `("psyche_endpoint", "Psyche"),`             |
| `travel_endpoint`      | `root_modules` | ~L:112 | `("travel_endpoint", "Travel"),`             |
| `research_endpoint`    | `root_modules` | ~L:112 | `("research_endpoint", "Research"),`         |
| `programista_endpoint` | `root_modules` | ~L:112 | `("programista_endpoint", "Code Executor"),` |
| `nlp_endpoint`         | `root_modules` | ~L:112 | `("nlp_endpoint", "NLP"),`                   |
| `core.admin_endpoint`  | `core_modules` | ~L:144 | `("core.admin_endpoint", "Admin [core]"),`   |

#### B) Naprawić nazwy routerów

| Plik                           | Linia | Zmiana                                                       |
| ------------------------------ | ----- | ------------------------------------------------------------ |
| [writer_pro.py](writer_pro.py) | L:96  | `writer_router = APIRouter(...)` → `router = APIRouter(...)` |

#### C) Dodać prefix do prometheus_endpoint.py (root)

| Plik                                             | Linia | Zmiana                                                                                       |
| ------------------------------------------------ | ----- | -------------------------------------------------------------------------------------------- |
| [prometheus_endpoint.py](prometheus_endpoint.py) | L:12  | `router = APIRouter()` → `router = APIRouter(prefix="/api/prometheus", tags=["monitoring"])` |

#### D) Dodać brakujące tagi

| Plik                                               | Linia | Zmiana                    |
| -------------------------------------------------- | ----- | ------------------------- |
| [assistant_endpoint.py](assistant_endpoint.py)     | L:40  | Dodać `tags=["chat"]`     |
| [internal_endpoint.py](internal_endpoint.py)       | L:11  | Dodać `tags=["internal"]` |
| [files_endpoint.py](files_endpoint.py)             | L:15  | Dodać `tags=["files"]`    |
| [writing_endpoint.py](writing_endpoint.py)         | L:26  | Dodać `tags=["writing"]`  |
| [psyche_endpoint.py](psyche_endpoint.py)           | L:26  | Dodać `tags=["psyche"]`   |
| [travel_endpoint.py](travel_endpoint.py)           | L:18  | Dodać `tags=["travel"]`   |
| [programista_endpoint.py](programista_endpoint.py) | L:17  | Dodać `tags=["code"]`     |
| [core/admin_endpoint.py](core/admin_endpoint.py)   | L:24  | Dodać `tags=["admin"]`    |

#### E) Zunifikować auth

| Plik                          | Obecny wzorzec  | Docelowy wzorzec                                                             |
| ----------------------------- | --------------- | ---------------------------------------------------------------------------- |
| Wszystkie z `def _auth(req):` | Lokalna funkcja | `from core.auth import auth_dependency` + `Depends(auth_dependency)`         |
| Wszystkie bez auth            | Brak            | Dodać `dependencies=[Depends(auth_dependency)]` do routera lub indywidualnie |

#### F) DUPLIKATY ROOT/CORE — WYMAGA ANALIZY PKT 07

**WAŻNE:** Żadne usuwanie bez dowodu z import-grafu (pkt 07). Poniżej tylko KONFLICTY do unifikacji.

| Konflikt                        | Status                                        | Akcja (po pkt 07)                      |
| ------------------------------- | --------------------------------------------- | -------------------------------------- |
| `research_endpoint.py` (oba)    | CONFLICT(P0) - ten sam prefix `/api/research` | Wybrać 1 źródło, drugie archiwizować   |
| `psyche_endpoint.py` (oba)      | CONFLICT(P0) - ten sam prefix `/api/psyche`   | Wybrać 1 źródło, drugie archiwizować   |
| `suggestions_endpoint.py` (oba) | Root podpięty, core nie                       | Core kandydat do archiwizacji (pkt 07) |

**Uwaga:** `suggestions_endpoint.py` (root) jest ładowany przez `app.py`. Core weryfikować w pkt 07.

---

## 7. WERYFIKACJA ZMIAN

### 7.1. Endpointy diagnostyczne (POTWIERDZONE)

| Endpoint                  | Plik       | Linia     | Funkcja                                     |
| ------------------------- | ---------- | --------- | ------------------------------------------- |
| `GET /api/routers/status` | `./app.py` | L:163-165 | Zwraca `{"loaded": [...], "failed": [...]}` |
| `GET /api/endpoints/list` | `./app.py` | L:167-176 | Zwraca `{"count": N, "items": [...]}`       |

**Cytat z `./app.py` L:163-176:**

```python
@app.get("/api/routers/status")
async def routers_status() -> Dict[str, Any]:
    return {"loaded": loaded, "failed": failed, "ts": _now()}

@app.get("/api/endpoints/list")
async def endpoints_list() -> Dict[str, Any]:
    out = []
    for rt in app.router.routes:
        path = getattr(rt, "path", None)
        methods = getattr(rt, "methods", None)
        if path and methods:
            out.append({"path": path, "methods": sorted(list(methods))})
    out.sort(key=lambda x: x["path"])
    return {"count": len(out), "items": out, "ts": _now()}
```

### 7.2. Weryfikacja runtime

#### A) Przez HTTP (gdy serwer działa)

```bash
# Sprawdź status routerów:
curl http://localhost:8000/api/routers/status | jq

# Lista wszystkich endpointów:
curl http://localhost:8000/api/endpoints/list | jq '.count'
```

#### B) Przez Python (bez uruchomionego serwera)

**WARUNKI OBOWIĄZKOWE:**

| Warunek    | Wymagane                                          | Powód                                                 |
| ---------- | ------------------------------------------------- | ----------------------------------------------------- |
| CWD        | `cd /path/to/mrd`                                 | Importy relatywne (`core.xxx`) wymagają root projektu |
| PYTHONPATH | nie trzeba ustawiać jeśli CWD=mrd                 | Python domyślnie dodaje CWD do path                   |
| Zależności | zainstalowane (`pip install -r requirements.txt`) | Import zawiedzie bez FastAPI itp.                     |

**PEWNA PROCEDURA WERYFIKACJI:**

```bash
# 1. Wejdź do katalogu projektu (OBOWIĄZKOWE)
cd /mnt/c/Users/48501/Desktop/mrd   # Linux/WSL
# lub
cd C:\Users\48501\Desktop\mrd       # Windows

# 2. Uruchom test importu
python -c "
import sys
print(f'CWD: {__import__("os").getcwd()}')
import app
print(f'Loaded: {len(app.loaded)}')
print(f'Failed: {len(app.failed)}')
print('--- Routes ---')
for r in app.app.routes:
    p = getattr(r, 'path', None)
    if p: print(p)
"
```

**MOŻLIWE BŁĘDY:**

| Błąd                                             | Przyczyna                            | Rozwiązanie                                       |
| ------------------------------------------------ | ------------------------------------ | ------------------------------------------------- |
| `ModuleNotFoundError: No module named 'core'`    | CWD nie jest katalogiem `mrd/`       | `cd mrd` przed uruchomieniem                      |
| `ModuleNotFoundError: No module named 'fastapi'` | Brak zależności                      | `pip install -r requirements.txt`                 |
| `ImportError: attempted relative import`         | Uruchomiono z niewłaściwego katalogu | Upewnij się że jesteś w `mrd/`, nie w `mrd/core/` |

### 7.3. Weryfikacja statyczna (grep)

```bash
# Zlicz routery zdefiniowane:
grep -rn "= APIRouter(" --include="*.py" | wc -l

# Znajdź routery bez prefixów:
grep -rn "= APIRouter()" --include="*.py"

# Znajdź routery z niestandardą nazwą:
grep -rn "_router = APIRouter" --include="*.py"
```

### 7.4. Oczekiwany wynik po pełnej unifikacji

```
✅ Loaded routers: 17 (obecny stan) → docelowo 24 (po dodaniu 7 niepodpiętych z sekcji 6.2.A)
⛔ Failed routers: 0

OpenAPI docs (/docs):
- Wszystkie tagi widoczne i posortowane
- Wszystkie endpointy pod /api/* (oprócz /v1/* i /health)
- Auth wymagane na wszystkich poza /health, /metrics
```

---

## 8. PODSUMOWANIE

| Metryka                     | Wartość              |
| --------------------------- | -------------------- |
| **Routerów zdefiniowanych** | 35                   |
| **Routerów ładowanych**     | 17                   |
| **Routerów niepodpiętych**  | 18 (wymaga pkt 07)   |
| **Routerów bez prefixu**    | 2                    |
| **Routerów bez tagów**      | 9                    |
| **Endpointów bez auth**     | 5 (patrz sekcja 5.2) |
| **Duplikatów root/core**    | 3 pary               |

**Kluczowe problemy:**

1. **18 routerów niepodpiętych w app.py** - wymaga analizy czy są używane inaczej (pkt 07)
2. **Niespójne nazewnictwo** - `writer_router` zamiast `router` → P1
3. **Brak tagów** - OpenAPI docs mniej czytelne → P2
4. **Lokalne funkcje auth** - niespójność, trudniejsze utrzymanie → P2
5. **CONFLICT(P0)** - ten sam prefix `/api/chat`, `/api/research`, `/api/psyche` w 2+ plikach

---

## 9. DOWODY (CITATIONS)

### 9.1 Wersje zależności

**Źródło:** `./requirements.txt` L:7-13

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
pydantic>=2.9.0
jinja2>=3.1.0
aiofiles>=23.2.0
starlette>=0.40.0
```

**Komenda weryfikacji:**

```bash
$ head -20 requirements.txt | grep -E 'fastapi|starlette|pydantic|uvicorn'
```

### 9.2 Brak plików uruchomieniowych

**Komenda (Linux):**

```bash
$ ls -la Dockerfile docker-compose* systemd* *.service start*.sh 2>/dev/null
ls: cannot access 'Dockerfile': No such file or directory
ls: cannot access 'docker-compose*': No such file or directory
ls: cannot access 'systemd*': No such file or directory
ls: cannot access '*.service': No such file or directory
ls: cannot access 'start*.sh': No such file or directory
```

**Wniosek:** Brak dowodu jak aplikacja jest uruchamiana na serwerze — wymaga weryfikacji.

### 9.3 Wykrycie routerów

**Komenda (Linux):**

```bash
$ grep -rn "= APIRouter(" --include="*.py" | wc -l
35
```

### 9.4 Routery bez prefixu

**Komenda (Linux):**

```bash
$ grep -rn "= APIRouter()" --include="*.py"
./prometheus_endpoint.py:12:router = APIRouter()
./core/prometheus_endpoint.py:12:router = APIRouter()
```

### 9.5 Routery z niestandardą nazwą

**Komenda (Linux):**

```bash
$ grep -rn "_router = APIRouter" --include="*.py"
./writer_pro.py:96:writer_router = APIRouter(prefix="/api/writer", tags=["writing"])
```

### 9.6 Endpointy diagnostyczne

**Źródło:** `./app.py` L:163-176

```python
@app.get("/api/routers/status")
async def routers_status() -> Dict[str, Any]:
    return {"loaded": loaded, "failed": failed, "ts": _now()}

@app.get("/api/endpoints/list")
async def endpoints_list() -> Dict[str, Any]:
    out = []
    for rt in app.router.routes:
        path = getattr(rt, "path", None)
        methods = getattr(rt, "methods", None)
        if path and methods:
            out.append({"path": path, "methods": sorted(list(methods))})
    out.sort(key=lambda x: x["path"])
    return {"count": len(out), "items": out, "ts": _now()}
```

### 9.7 Cytaty z ./app.py (mechanizm ładowania)

**L:82-89** — Mechanizm szukający atrybutu `router`:

```python
def _try_import_router(modname: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        m = importlib.import_module(modname)
        r = getattr(m, "router", None)  # <-- szuka "router"
        if r is None:
            return None, "no router attr"
        return r, None
```

**L:100-108** — `root_modules` (7 modułów):

```python
root_modules = [
    ("assistant_simple", "Chat (Commercial)"),
    ("stt_endpoint", "STT (Speech-to-Text)"),
    ("tts_endpoint", "TTS (Text-to-Speech)"),
    ("suggestions_endpoint", "Suggestions"),
    ("internal_endpoint", "Internal"),
    ("files_endpoint", "Files (Advanced)"),
    ("routers", "Admin/Debug"),
]
```

**L:127-137** — `core_modules` (9 modułów):

```python
core_modules = [
    ("core.assistant_endpoint", "Chat (Advanced) [core]"),
    ("core.memory_endpoint", "Memory [core]"),
    ("core.cognitive_endpoint", "Cognitive [core]"),
    ("core.negocjator_endpoint", "Negotiator [core]"),
    ("core.reflection_endpoint", "Reflection [core]"),
    ("core.legal_office_endpoint", "Legal Office [core]"),
    ("core.hybrid_search_endpoint", "Hybrid Search [core]"),
    ("core.batch_endpoint", "Batch Processing [core]"),
    ("core.prometheus_endpoint", "Metrics [core]"),
]
```

### 9.8 Klasyfikacja PODPIĘTY/NIEPODPIĘTY

| Status           | Definicja                                                                           |
| ---------------- | ----------------------------------------------------------------------------------- |
| ✅ PODPIĘTY      | Router jest w `root_modules` lub `core_modules` w `./app.py`                        |
| ⚠️ NIEPODPIĘTY   | Router NIE jest w tych listach (może być używany przez `./core/app.py` lub inaczej) |
| ❓ WYMAGA PKT 07 | Ostateczna klasyfikacja (ORPHAN/LEGACY) wymaga analizy import-grafu                 |

**ZAKAZ:** W pkt 01-03 nie rozstrzygamy czy plik jest "martwy" ani nie rekomendujemy usunięcia.

---

**STOP — sprawdź ten punkt. Czy coś poprawić/doprecyzować? Czy mam dodać coś jeszcze? Jeśli OK, przechodzę do: `AUDYT/03_ENDPOINTY_KONFLIKTY_DEAD_ROUTES3.md`.**
