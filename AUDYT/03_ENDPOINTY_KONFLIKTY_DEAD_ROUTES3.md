# AUDYT PUNKT 3: ENDPOINTY, KONFLIKTY I DEAD ROUTES

**Data audytu:** 26 grudnia 2025  
**Zakres:** Wszystkie endpointy HTTP w `mrd/**`  
**Metoda:** grep z twardym outputem (poniżej)

---

## 0. ŚRODOWISKO AUDYTU

| Parametr                        | Wartość                                              |
| ------------------------------- | ---------------------------------------------------- |
| **System**                      | Linux (bash via WSL)                                 |
| **Katalog roboczy**             | `/mnt/c/Users/48501/Desktop/mrd`                     |
| **Metoda zliczania endpointów** | `grep -E '@router\.(get\|post\|put\|delete\|patch)'` |
| **Filtr wykluczający**          | `grep -v 'patch_\|fix_\|tools_'` (pliki jednorazowe) |

**UWAGA:** Wszystkie ścieżki w audycie używają formatu Linux (`./core/app.py`), nie Windows.

---

## 0.1 Komenda: Zliczenie @router.\* dekoratorów

```bash
$ grep -rE '@router\.(get|post|put|delete|patch)\(' --include='*.py' | grep -v 'patch_\|fix_\|tools_' | wc -l
176
```

### 0.2 Komenda: Pełna lista @router.\* (surowy output)

```bash
$ grep -rnE '@router\.(get|post|put|delete|patch)\(' --include='*.py' | grep -v 'patch_\|fix_\|tools_' | sort
```

**RAW OUTPUT (176 linii - poniżej unikalne, bez patch\_\*.py):**

| Plik                      | L#      | Dekorator                                                 |
| ------------------------- | ------- | --------------------------------------------------------- |
| admin_endpoint.py         | 37      | `@router.get("/cache/stats")`                             |
| admin_endpoint.py         | 60      | `@router.post("/cache/clear")`                            |
| admin_endpoint.py         | 86      | `@router.get("/ratelimit/usage/{user_id}")`               |
| admin_endpoint.py         | 96      | `@router.get("/ratelimit/config")`                        |
| admin_endpoint.py         | 118     | `@router.post("/jwt/rotate")`                             |
| assistant_endpoint.py     | 49      | `@router.post("/assistant", response_model=ChatResponse)` |
| assistant_endpoint.py     | 73/77   | `@router.post("/assistant/stream")`                       |
| assistant_endpoint.py     | 107/115 | `@router.post("/auto", response_model=ChatResponse)`      |
| assistant_simple.py       | 254     | `@router.post("/assistant")`                              |
| assistant_simple.py       | 288     | `@router.post("/assistant/stream")`                       |
| auction_endpoint.py       | 65      | `@router.post("/analyze")`                                |
| auction_endpoint.py       | 177     | `@router.post("/optimize-price")`                         |
| auction_endpoint.py       | 243     | `@router.post("/optimize-description")`                   |
| auction_endpoint.py       | 326     | `@router.post("/market-analysis")`                        |
| auction_endpoint.py       | 394     | `@router.get("/categories")`                              |
| batch_endpoint.py         | 51      | `@router.post("/process")`                                |
| batch_endpoint.py         | 77      | `@router.get("/status/{batch_id}")`                       |
| batch_endpoint.py         | 89      | `@router.get("/list")`                                    |
| batch_endpoint.py         | 97      | `@router.delete("/{batch_id}")`                           |
| chat_advanced_endpoint.py | 107     | `@router.get("/health")`                                  |
| chat_advanced_endpoint.py | 112     | `@router.post("")`                                        |
| chat_advanced_endpoint.py | 157     | `@router.post("/openai")`                                 |
| chat_advanced_endpoint.py | 184     | `@router.post("/stream")`                                 |
| cognitive_endpoint.py     | 37      | `@router.post("/reflect")`                                |
| cognitive_endpoint.py     | 93      | `@router.get("/reflection/summary")`                      |
| cognitive_endpoint.py     | 127     | `@router.post("/proactive/suggestions")`                  |
| cognitive_endpoint.py     | 179     | `@router.post("/psychology/analyze")`                     |
| cognitive_endpoint.py     | 216     | `@router.get("/psychology/state/{user_id}")`              |
| cognitive_endpoint.py     | 248     | `@router.post("/process")`                                |
| cognitive_endpoint.py     | 332     | `@router.post("/nlp/analyze")`                            |
| cognitive_endpoint.py     | 378     | `@router.post("/semantic/analyze")`                       |
| cognitive_endpoint.py     | 423     | `@router.get("/tools/list")`                              |
| cognitive_endpoint.py     | 456     | `@router.get("/status")`                                  |
| files_endpoint.py         | 170     | `@router.post("/upload")`                                 |
| files_endpoint.py         | 219     | `@router.post("/upload/base64")`                          |
| files_endpoint.py         | 260     | `@router.get("/list")`                                    |
| files_endpoint.py         | 321     | `@router.get("/download")`                                |
| files_endpoint.py         | 339     | `@router.post("/analyze")`                                |
| files_endpoint.py         | 373     | `@router.post("/delete")`                                 |
| files_endpoint.py         | 388     | `@router.get("/stats")`                                   |
| files_endpoint.py         | 415     | `@router.post("/batch/analyze")`                          |
| hacker_endpoint.py        | 341     | `@router.post("/scan/ports")`                             |
| hacker_endpoint.py        | 354     | `@router.post("/scan/vulnerabilities")`                   |
| hacker_endpoint.py        | 367     | `@router.post("/exploit/sqli")`                           |
| hacker_endpoint.py        | 381     | `@router.post("/recon/domain")`                           |
| hacker_endpoint.py        | 399     | `@router.get("/tools/status")`                            |
| hacker_endpoint.py        | 429     | `@router.get("/exploits/list")`                           |
| internal_endpoint.py      | 14      | `@router.get("/ui_token")`                                |
| legal_office_endpoint.py  | 803     | `@router.post("/analyze")`                                |
| legal_office_endpoint.py  | 882     | `@router.post("/generate-response")`                      |
| legal_office_endpoint.py  | 971     | `@router.get("/templates")`                               |
| legal_office_endpoint.py  | 1021    | `@router.get("/institutions")`                            |
| legal_office_endpoint.py  | 1043    | `@router.post("/calculate-deadline")`                     |
| legal_office_endpoint.py  | 1101    | `@router.post("/upload-scan")`                            |
| memory_endpoint.py        | 30      | `@router.post("/add")`                                    |
| memory_endpoint.py        | 36      | `@router.post("/search")`                                 |
| memory_endpoint.py        | 42      | `@router.get("/export")`                                  |
| memory_endpoint.py        | 48      | `@router.post("/import")`                                 |
| memory_endpoint.py        | 54      | `@router.get("/status")`                                  |
| memory_endpoint.py        | 104     | `@router.post("/optimize")`                               |
| negocjator_endpoint.py    | 450     | `@router.post("/sprawdz-przedawnienie")`                  |
| negocjator_endpoint.py    | 475     | `@router.post("/propozycja-ugody")`                       |
| negocjator_endpoint.py    | 488     | `@router.post("/ocen-szanse")`                            |
| negocjator_endpoint.py    | 501     | `@router.post("/koszty-postepowania")`                    |
| negocjator_endpoint.py    | 515     | `@router.get("/typy-dlugow")`                             |
| negocjator_endpoint.py    | 531     | `@router.get("/info")`                                    |
| nlp_endpoint.py           | 75      | `@router.post("/analyze")`                                |
| nlp_endpoint.py           | 101     | `@router.post("/batch-analyze")`                          |
| nlp_endpoint.py           | 136     | `@router.post("/extract-topics")`                         |
| nlp_endpoint.py           | 170     | `@router.get("/stats")`                                   |
| nlp_endpoint.py           | 191     | `@router.post("/entities")`                               |
| nlp_endpoint.py           | 222     | `@router.post("/sentiment")`                              |
| nlp_endpoint.py           | 252     | `@router.post("/key-phrases")`                            |
| nlp_endpoint.py           | 283     | `@router.post("/readability")`                            |
| openai_compat.py          | 47      | `@router.get("/models")`                                  |
| openai_compat.py          | 66      | `@router.post("/chat/completions")`                       |
| programista_endpoint.py   | 73      | `@router.get("/snapshot")`                                |
| programista_endpoint.py   | 87      | `@router.post("/exec")`                                   |
| programista_endpoint.py   | 109     | `@router.post("/write")`                                  |
| programista_endpoint.py   | 123     | `@router.get("/read")`                                    |
| programista_endpoint.py   | 135     | `@router.get("/tree")`                                    |
| programista_endpoint.py   | 147     | `@router.post("/init")`                                   |
| programista_endpoint.py   | 161     | `@router.post("/plan")`                                   |
| programista_endpoint.py   | 175     | `@router.post("/lint")`                                   |
| programista_endpoint.py   | 189     | `@router.post("/test")`                                   |
| programista_endpoint.py   | 203     | `@router.post("/format")`                                 |
| programista_endpoint.py   | 217     | `@router.post("/git")`                                    |
| programista_endpoint.py   | 231     | `@router.post("/docker/build")`                           |
| programista_endpoint.py   | 245     | `@router.post("/docker/run")`                             |
| programista_endpoint.py   | 259     | `@router.post("/deps/install")`                           |
| prometheus_endpoint.py    | 14      | `@router.get("/metrics")`                                 |
| prometheus_endpoint.py    | 25      | `@router.get("/health")`                                  |
| prometheus_endpoint.py    | 30      | `@router.get("/stats")`                                   |
| psyche_endpoint.py        | 68      | `@router.get("/status")`                                  |
| psyche_endpoint.py        | 103     | `@router.post("/save")`                                   |
| psyche_endpoint.py        | 135     | `@router.get("/load")`                                    |
| psyche_endpoint.py        | 150     | `@router.post("/observe")`                                |
| psyche_endpoint.py        | 187     | `@router.post("/episode")`                                |
| psyche_endpoint.py        | 221     | `@router.get("/reflect")`                                 |
| psyche_endpoint.py        | 243     | `@router.get("/tune")`                                    |
| psyche_endpoint.py        | 276     | `@router.post("/reset")`                                  |
| psyche_endpoint.py        | 329     | `@router.post("/analyze")`                                |
| psyche_endpoint.py        | 349     | `@router.post("/set-mode")`                               |
| psyche_endpoint.py        | 371     | `@router.post("/enhance-prompt")`                         |
| reflection_endpoint.py    | 41      | `@router.post("/reflect")`                                |
| reflection_endpoint.py    | 92      | `@router.post("/adaptive-reflect")`                       |
| reflection_endpoint.py    | 145     | `@router.get("/depths")`                                  |
| reflection_endpoint.py    | 188     | `@router.get("/stats")`                                   |
| reflection_endpoint.py    | 211     | `@router.get("/meta-patterns")`                           |
| reflection_endpoint.py    | 235     | `@router.get("/history")`                                 |
| research_endpoint.py      | 40      | `@router.post("/search")`                                 |
| research_endpoint.py      | 81      | `@router.post("/autonauka")`                              |
| research_endpoint.py      | 124     | `@router.get("/sources")`                                 |
| research_endpoint.py      | 175     | `@router.get("/test")`                                    |
| routers.py                | 126     | `@router.get("/status")`                                  |
| routers.py                | 136     | `@router.get("/health")`                                  |
| routers.py                | 159     | `@router.get("/list")`                                    |
| routers.py                | 203     | `@router.get("/metrics")`                                 |
| routers.py                | 246     | `@router.get("/config")`                                  |
| routers.py                | 269     | `@router.get("/endpoints/summary")`                       |
| routers.py                | 317     | `@router.get("/debug/info")`                              |
| routers.py                | 364     | `@router.post("/cache/clear")`                            |
| routers.py                | 398     | `@router.get("/version")`                                 |
| routers.py                | 425     | `@router.get("/experimental/features")`                   |
| stt_endpoint.py           | 23      | `@router.post("/transcribe")`                             |
| stt_endpoint.py           | 144     | `@router.get("/providers")`                               |
| suggestions_endpoint.py   | 47      | `@router.post("/generate")`                               |
| suggestions_endpoint.py   | 84      | `@router.post("/inject")`                                 |
| suggestions_endpoint.py   | 110     | `@router.get("/stats")`                                   |
| suggestions_endpoint.py   | 129     | `@router.post("/analyze")`                                |
| travel_endpoint.py        | 27      | `@router.get("/search")`                                  |
| travel_endpoint.py        | 64      | `@router.get("/geocode")`                                 |
| travel_endpoint.py        | 111     | `@router.get("/attractions/{city}")`                      |
| travel_endpoint.py        | 127     | `@router.get("/hotels/{city}")`                           |
| travel_endpoint.py        | 143     | `@router.get("/restaurants/{city}")`                      |
| travel_endpoint.py        | 159     | `@router.get("/trip-plan")`                               |
| tts_endpoint.py           | 51      | `@router.get("/voices")`                                  |
| tts_endpoint.py           | 80      | `@router.post("/speak")`                                  |
| tts_endpoint.py           | 140     | `@router.get("/status")`                                  |
| writing_endpoint.py       | 107     | `@router.post("/creative")`                               |
| writing_endpoint.py       | 136     | `@router.post("/vinted")`                                 |
| writing_endpoint.py       | 161     | `@router.post("/social")`                                 |
| writing_endpoint.py       | 190     | `@router.post("/auction")`                                |
| writing_endpoint.py       | 217     | `@router.post("/auction/pro")`                            |
| writing_endpoint.py       | 248     | `@router.post("/fashion/analyze")`                        |
| writing_endpoint.py       | 358     | `@router.post("/auction/suggest-tags")`                   |
| writing_endpoint.py       | 374     | `@router.post("/auction/kb/learn")`                       |
| writing_endpoint.py       | 390     | `@router.get("/auction/kb/fetch")`                        |
| writing_endpoint.py       | 411     | `@router.post("/masterpiece/article")`                    |
| writing_endpoint.py       | 440     | `@router.post("/masterpiece/sales")`                      |
| writing_endpoint.py       | 468     | `@router.post("/masterpiece/technical")`                  |

### 0.3 Komenda: @writer_router.\* (osobna zmienna)

```bash
$ grep -rnE '@writer_router\.(get|post|put|delete|patch)\(' --include='*.py'
```

**RAW OUTPUT (13 linii):**

| Plik          | L#  | Dekorator                                       |
| ------------- | --- | ----------------------------------------------- |
| writer_pro.py | 102 | `@writer_router.get("/status")`                 |
| writer_pro.py | 128 | `@writer_router.post("/creative")`              |
| writer_pro.py | 162 | `@writer_router.post("/product")`               |
| writer_pro.py | 210 | `@writer_router.post("/social")`                |
| writer_pro.py | 246 | `@writer_router.post("/auction/pro")`           |
| writer_pro.py | 282 | `@writer_router.post("/article/masterpiece")`   |
| writer_pro.py | 317 | `@writer_router.post("/sales/masterpiece")`     |
| writer_pro.py | 350 | `@writer_router.post("/technical/masterpiece")` |
| writer_pro.py | 383 | `@writer_router.post("/fashion/analyze")`       |
| writer_pro.py | 409 | `@writer_router.get("/auction/tags")`           |
| writer_pro.py | 441 | `@writer_router.get("/auction/knowledge")`      |
| writer_pro.py | 461 | `@writer_router.post("/auction/learn")`         |
| writer_pro.py | 484 | `@writer_router.get("/templates")`              |

### 0.4 Komenda: @app.\* endpointy bezpośrednie

```bash
$ grep -rnE '@app\.(get|post|put|delete|patch)\(' --include='*.py' | grep -v 'patch_\|fix_\|tools_\|test'
```

**RAW OUTPUT (18 linii, bez komentarzy/docstrings):**

| Plik          | L#  | Dekorator                            |
| ------------- | --- | ------------------------------------ |
| app.py (root) | 67  | `@app.get("/health")`                |
| app.py (root) | 163 | `@app.get("/api/routers/status")`    |
| app.py (root) | 167 | `@app.get("/api/endpoints/list")`    |
| core/app.py   | 391 | `@app.get("/api")`                   |
| core/app.py   | 392 | `@app.get("/status")`                |
| core/app.py   | 423 | `@app.get("/health")`                |
| core/app.py   | 428 | `@app.get("/api/endpoints/list")`    |
| core/app.py   | 453 | `@app.get("/api/automation/status")` |
| core/app.py   | 471 | `@app.get("/")`                      |
| core/app.py   | 472 | `@app.get("/app")`                   |
| core/app.py   | 473 | `@app.get("/chat")`                  |
| core/app.py   | 497 | `@app.get("/{full_path:path}")`      |
| core/app.py   | 512 | `@app.get("/sw.js")`                 |
| core/app.py   | 513 | `@app.get("/ngsw-worker.js")`        |
| core/app.py   | 529 | `@app.get("/manifest.webmanifest")`  |
| core/app.py   | 543 | `@app.get("/favicon.ico")`           |

---

## 1. PODSUMOWANIE STATYSTYK (Z DOWODAMI)

| Metryka                             | Wartość | Źródło                                                      |
| ----------------------------------- | ------- | ----------------------------------------------------------- |
| Dekoratory `@router.*` (unikalne)   | **176** | `grep -rE '@router\.(get\|...)' \| grep -v patch_ \| wc -l` |
| Dekoratory `@writer_router.*`       | **13**  | `grep -rE '@writer_router\.(get\|...)' \| wc -l`            |
| Dekoratory `@app.*` (obie app.py)   | **18**  | `grep -rE '@app\.(get\|...)' \| grep -v patch_ \| wc -l`    |
| **RAZEM endpointów zdefiniowanych** | **207** | 176 + 13 + 18                                               |

### Klasyfikacja wg statusu podpięcia w `app.py` (root):

| Status                  | Ilość | Opis                                                        |
| ----------------------- | ----- | ----------------------------------------------------------- |
| ✅ Podpięte w app.py    | 76    | Routery z listy `root_modules` + `core_modules` (32+44)     |
| ⚠️ NIEPODPIĘTE w app.py | 100   | Routery NIEZAWARTE w app.py (nie oznacza martwych!)         |
| 🔴 CONFLICT(P0)         | 6     | Duplikaty method+path (do rozwiązania)                      |
| 🔴 BUG(P0)              | 1     | `core/hybrid_search_endpoint.py` — 0 endpointów (utracone!) |

**WAŻNE:** Status "NIEPODPIĘTE" NIE oznacza automatycznie "MARTWE". Pliki mogą być:

- importowane dynamicznie (importlib, plugin loader)
- używane przez alternatywny entrypoint `core/app.py`
- importowane jako moduły (bez include_router)

Ostateczna klasyfikacja ORPHAN/DEAD wymaga analizy import-grafu (pkt 07).

---

## 2. LISTA MODUŁÓW ŁADOWANYCH PRZEZ `app.py` (TWARDE ŹRÓDŁO)

**Źródło:** `app.py` linie 100-145 (`root_modules` + `core_modules`)

```python
# root_modules (L:100-108):
root_modules = [
    ("assistant_simple", "Chat (Commercial)"),
    ("stt_endpoint", "STT (Speech-to-Text)"),
    ("tts_endpoint", "TTS (Text-to-Speech)"),
    ("suggestions_endpoint", "Suggestions"),
    ("internal_endpoint", "Internal"),
    ("files_endpoint", "Files (Advanced)"),
    ("routers", "Admin/Debug"),
]

# core_modules (L:127-137):
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

**Dodatkowo na sztywno (L:53):**

```python
from openai_compat import router as openai_compat_router
app.include_router(openai_compat_router)
```

**RAZEM podpiętych modułów:** 7 (root) + 9 (core) + 1 (openai_compat) = **17 modułów**

---

## 3. CONFLICT(P0) — DUPLIKATY METODA+ŚCIEŻKA

**Definicja:** Ten sam HTTP method + ta sama pełna ścieżka zdefiniowane w 2+ plikach.

### 3.1 Lista konfliktów

| #   | Method | Pełna ścieżka                 | Plik 1                             | Plik 2                            | Status           |
| --- | ------ | ----------------------------- | ---------------------------------- | --------------------------------- | ---------------- |
| 1   | POST   | `/api/chat/assistant`         | `assistant_simple.py` L:254        | `core/assistant_endpoint.py` L:49 | **CONFLICT(P0)** |
| 2   | POST   | `/api/chat/assistant`         | `assistant_simple.py` L:254        | `assistant_endpoint.py` L:49      | **CONFLICT(P0)** |
| 3   | POST   | `/api/chat/assistant/stream`  | `assistant_simple.py` L:288        | `core/assistant_endpoint.py` L:73 | **CONFLICT(P0)** |
| 4   | POST   | `/api/chat/assistant/stream`  | `assistant_simple.py` L:288        | `assistant_endpoint.py` L:77      | **CONFLICT(P0)** |
| 5   | POST   | `/api/chat/auto`              | `core/assistant_endpoint.py` L:107 | `assistant_endpoint.py` L:115     | **CONFLICT(P0)** |
| 6   | GET    | `/api/psyche/status` (i inne) | `psyche_endpoint.py`               | `core/psyche_endpoint.py`         | **CONFLICT(P0)** |

**UWAGA:** Pliki `psyche_endpoint.py`, `research_endpoint.py`, `suggestions_endpoint.py` mają IDENTYCZNE kopie w root i core — 100% duplikat treści.

### 3.2 Plan unifikacji CONFLICT(P0)

| #   | Konflikt                       | Plan naprawy                                                                                                                                                         | Priorytet |
| --- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| 1-4 | `/api/chat/assistant*` 3 pliki | Ustalić JEDEN źródłowy: `assistant_simple.py` (prostszy) LUB `core/assistant_endpoint.py` (zaawansowany). Drugi plik: wyłączyć routing LUB zmergować funkcjonalność. | P0        |
| 5   | `/api/chat/auto`               | Pozostawić tylko w `core/assistant_endpoint.py` (aktualnie podpięty). `assistant_endpoint.py` (root) oznaczyć jako "kandydat do archiwizacji po pkt 07".             | P0        |
| 6   | Duplikaty root/core            | Wybrać wersję CORE (nowsza, lepsza). Wersję ROOT oznaczyć jako "kandydat do archiwizacji (wymaga potwierdzenia w pkt 07)".                                           | P0        |

---

## 4. ROUTERY NIEPODPIĘTE W `app.py` (NIE OZNACZA MARTWYCH!)

**Metodologia:** Porównanie listy modułów w `app.py` z plikami zawierającymi `router = APIRouter()`.

### 4.1 Pliki ROOT z routerami NIEPODPIĘTYMI w app.py

| Plik                      | Prefix          | Endpointów | Status podpięcia          | Uwagi                                       |
| ------------------------- | --------------- | ---------- | ------------------------- | ------------------------------------------- |
| `assistant_endpoint.py`   | `/api/chat`     | 3          | ⚠️ NIEPODPIĘTE (konflikt) | Duplikat funkcjonalności z assistant_simple |
| `writing_endpoint.py`     | `/api/writing`  | 12         | ⚠️ NIEPODPIĘTE            | Może być ładowany przez core/app.py         |
| `psyche_endpoint.py`      | `/api/psyche`   | 11         | ⚠️ NIEPODPIĘTE            | Duplikat core/psyche_endpoint.py            |
| `travel_endpoint.py`      | `/api/travel`   | 6          | ⚠️ NIEPODPIĘTE            |                                             |
| `research_endpoint.py`    | `/api/research` | 4          | ⚠️ NIEPODPIĘTE            | Duplikat core/                              |
| `programista_endpoint.py` | `/api/code`     | 14         | ⚠️ NIEPODPIĘTE            |                                             |
| `nlp_endpoint.py`         | `/api/nlp`      | 8          | ⚠️ NIEPODPIĘTE            |                                             |
| `prometheus_endpoint.py`  | (brak!)         | 3          | ⚠️ NIEPODPIĘTE            | Router bez prefix!                          |
| `writer_pro.py`           | `/api/writer`   | 13         | ⚠️ NIEPODPIĘTE            | Używa `writer_router` zamiast `router`      |

### 4.2 Pliki CORE z routerami NIEPODPIĘTYMI w app.py

| Plik                             | Prefix                | Endpointów | Status podpięcia | Uwagi              |
| -------------------------------- | --------------------- | ---------- | ---------------- | ------------------ |
| `core/admin_endpoint.py`         | `/api/admin`          | 5          | ⚠️ NIEPODPIĘTE   |                    |
| `core/hacker_endpoint.py`        | `/api/hacker`         | 6          | ⚠️ NIEPODPIĘTE   |                    |
| `core/chat_advanced_endpoint.py` | `/core/chat/advanced` | 4          | ⚠️ NIEPODPIĘTE   |                    |
| `core/auction_endpoint.py`       | `/api/auction`        | 5          | ⚠️ NIEPODPIĘTE   |                    |
| `core/research_endpoint.py`      | `/api/research`       | 4          | ⚠️ NIEPODPIĘTE   | Duplikat root      |
| `core/psyche_endpoint.py`        | `/api/psyche`         | 11         | ⚠️ NIEPODPIĘTE   | Duplikat root      |
| `core/suggestions_endpoint.py`   | `/api/suggestions`    | 4          | ⚠️ NIEPODPIĘTE   | Root jest podpięty |

---

## 5. BUG: Router bez endpointów

### 5.1 `core/hybrid_search_endpoint.py`

**Komenda weryfikacyjna:**

```powershell
PS> Select-String -Path "core\hybrid_search_endpoint.py" -Pattern "@router\." -SimpleMatch
# (brak wyników)
```

**Fakt:** Plik definiuje `router = APIRouter(prefix="/api/search", tags=["search"])` w L:20, ale **NIE ZAWIERA ANI JEDNEGO dekoratora `@router.*`**.

**Dowód z backup:**

```powershell
PS> Select-String -Path "core\hybrid_search_endpoint.py.bak.call_helper.20251226-091020" -Pattern "@router\.post" -SimpleMatch
core\hybrid_search_endpoint.py.bak.call_helper.20251226-091020:480:@router.post("/hybrid", response_model=HybridSearchResponse)
```

**Status:** 🔴 **BUG P0** — endpoint `/api/search/hybrid` istniał, został utracony. Wymagana naprawa: przywrócić z backup L:480-555.

---

## 6. PROBLEM: Router z niewłaściwą nazwą zmiennej

### 6.1 `writer_pro.py`

**Komenda weryfikacyjna:**

```bash
$ grep -n 'writer_router\s*=' writer_pro.py
96:writer_router = APIRouter(prefix="/api/writer", tags=["writing"])
```

**Problem:** `app.py` L:85-87 szuka atrybutu `router`:

```python
r = getattr(m, "router", None)
if r is None:
    return None, "no router attr"
```

**Skutek:** 13 endpointów z `writer_pro.py` nigdy nie zostanie automatycznie załadowanych.

**Status:** 🟠 **P1** — zmienić `writer_router` na `router` LUB dodać alias `router = writer_router`.

---

## 7. KANDYDACI DO ARCHIWIZACJI (WYMAGA PKT 07)

**WAŻNE:** Na tym etapie NIE zalecam usuwania żadnych plików. Poniższe to tylko KANDYDACI do analizy w pkt 07 (import-graf).

| Plik                             | Powód kandydatury                        | Wymaga weryfikacji                     |
| -------------------------------- | ---------------------------------------- | -------------------------------------- |
| `assistant_endpoint.py` (root)   | Duplikat `core/assistant_endpoint.py`    | Sprawdzić czy importowany dynamicznie  |
| `psyche_endpoint.py` (root)      | Duplikat `core/psyche_endpoint.py`       | j.w.                                   |
| `research_endpoint.py` (root)    | Duplikat `core/research_endpoint.py`     | j.w.                                   |
| `suggestions_endpoint.py` (core) | Duplikat root (root jest podpięty)       | j.w.                                   |
| `core/app.py`                    | Alternatywny entrypoint, może nieużywany | Sprawdzić czy startowany gdzie indziej |

---

## 8. WERYFIKACJA — KOMENDY DO URUCHOMIENIA

```bash
# 1. Potwierdzenie że hybrid_search nie ma endpointów:
$ grep -n '@router\.\(get\|post\)' core/hybrid_search_endpoint.py

# 2. Lista podpiętych routerów (z logów startu app):
$ cd /mnt/c/Users/48501/Desktop/mrd && python -c "import app" 2>&1 | grep -E '✅|⏭️|⚠️'

# 3. Sprawdzenie konfliktów /api/chat:
$ grep -rn 'prefix="/api/chat"' --include='*.py' | cut -d: -f1 | sort -u
```

---

## 9. DOWODY (CITATIONS)

### 9.1 Liczba endpointów @router.\*

**Komenda:**

```bash
$ grep -rE '@router\.(get|post|put|delete|patch)\(' --include='*.py' | grep -v 'patch_\|fix_\|tools_' | wc -l
176
```

### 9.2 Liczba endpointów @writer_router.\*

**Komenda:**

```bash
$ grep -rE '@writer_router\.(get|post|put|delete|patch)\(' --include='*.py' | wc -l
13
```

### 9.3 Liczba endpointów @app.\*

**Komenda:**

```bash
$ grep -rE '@app\.(get|post|put|delete|patch)\(' --include='*.py' | grep -v 'patch_\|fix_\|tools_\|test' | wc -l
18
```

### 9.4 Endpointy w routerach PODPIĘTYCH (root)

**Komenda:**

```bash
$ grep -E '@router\.(get|post|put|delete|patch)' assistant_simple.py stt_endpoint.py tts_endpoint.py suggestions_endpoint.py internal_endpoint.py files_endpoint.py routers.py openai_compat.py | cut -d: -f1 | sort | uniq -c
      2 assistant_simple.py
      8 files_endpoint.py
      1 internal_endpoint.py
      2 openai_compat.py
     10 routers.py
      2 stt_endpoint.py
      4 suggestions_endpoint.py
      3 tts_endpoint.py
# RAZEM: 32 endpointów
```

### 9.5 Endpointy w routerach PODPIĘTYCH (core)

**Komenda:**

```bash
$ grep -E '@router\.(get|post|put|delete|patch)' core/assistant_endpoint.py core/memory_endpoint.py core/cognitive_endpoint.py core/negocjator_endpoint.py core/reflection_endpoint.py core/legal_office_endpoint.py core/hybrid_search_endpoint.py core/batch_endpoint.py core/prometheus_endpoint.py | cut -d: -f1 | sort | uniq -c
      3 core/assistant_endpoint.py
      4 core/batch_endpoint.py
     10 core/cognitive_endpoint.py
      6 core/legal_office_endpoint.py
      6 core/memory_endpoint.py
      6 core/negocjator_endpoint.py
      3 core/prometheus_endpoint.py
      6 core/reflection_endpoint.py
# RAZEM: 44 endpointów (ale hybrid_search = 0!)
```

### 9.6 Brak endpointów w hybrid_search_endpoint.py

**Komenda:**

```bash
$ grep -n '@router\.\(get\|post\)' core/hybrid_search_endpoint.py
# (brak wyników)
```

**Backup (L:480):**

```bash
$ grep -n '@router\.post' core/hybrid_search_endpoint.py.bak.call_helper.20251226-091020
480:@router.post("/hybrid", response_model=HybridSearchResponse)
```

### 9.7 Klasyfikacja PODPIĘTY/NIEPODPIĘTY

| Status           | Definicja                                                                           |
| ---------------- | ----------------------------------------------------------------------------------- |
| ✅ PODPIĘTY      | Router jest w `root_modules` lub `core_modules` w `./app.py`                        |
| ⚠️ NIEPODPIĘTY   | Router NIE jest w tych listach (może być używany przez `./core/app.py` lub inaczej) |
| ❓ WYMAGA PKT 07 | Ostateczna klasyfikacja (ORPHAN/LEGACY) wymaga analizy import-grafu                 |

**ZAKAZ:** W pkt 01-03 nie rozstrzygamy czy plik jest "martwy" ani nie rekomendujemy usunięcia.

---

**STOP — sprawdź ten punkt. Czy coś poprawić/doprecyzować? Jeśli OK, przechodzę do: `AUDYT/04_SECURITY_AUTH_TOKENS4.md`.**
