# AUDYT MRD - CZĘŚĆ 1: MAPA PROJEKTU + ENTRYPOINT TRUTH

## 1.1 DRZEWO PROJEKTU (istotne pliki)

```
mrd/
├── app.py                          # ⭐ GŁÓWNY ENTRYPOINT (root)
├── core/
│   ├── app.py                      # ⚠️ ALTERNATYWNY ENTRYPOINT (core/)
│   ├── __init__.py
│   ├── config.py                   # Konfiguracja ENV
│   ├── auth.py                     # Autoryzacja
│   ├── assistant_endpoint.py       # Router: /api/chat
│   ├── memory_endpoint.py          # Router: /api/memory
│   ├── cognitive_endpoint.py       # Router: /api/cognitive
│   ├── negocjator_endpoint.py      # Router: /api/negocjator
│   ├── reflection_endpoint.py      # Router: /api/reflection
│   ├── legal_office_endpoint.py    # Router: /api/legal
│   ├── hybrid_search_endpoint.py   # Router: /api/search
│   ├── batch_endpoint.py           # Router: /api/batch
│   ├── prometheus_endpoint.py      # Router: /metrics
│   ├── admin_endpoint.py           # Router: /api/admin
│   ├── research_endpoint.py        # Router: /api/research
│   ├── psyche_endpoint.py          # Router: /api/psyche
│   ├── suggestions_endpoint.py     # Router: /api/suggestions
│   ├── hacker_endpoint.py          # Router: /api/hacker
│   ├── auction_endpoint.py         # Router: /api/auction
│   ├── chat_advanced_endpoint.py   # Router: /core/chat/advanced
│   └── [inne moduły core...]
├── assistant_simple.py             # Router: /api/chat (duplikat!)
├── assistant_endpoint.py           # Router: /api/chat (duplikat!)
├── stt_endpoint.py                 # Router: /api/stt
├── tts_endpoint.py                 # Router: /api/tts
├── suggestions_endpoint.py        # Router: /api/suggestions (duplikat!)
├── internal_endpoint.py            # Router: /api/internal
├── files_endpoint.py               # Router: /api/files
├── routers.py                      # Router: /api/routers
├── openai_compat.py                # Router: /v1
├── nlp_endpoint.py                 # Router: /api/nlp
├── research_endpoint.py            # Router: /api/research (duplikat!)
├── prometheus_endpoint.py          # Router: /metrics (duplikat!)
├── psyche_endpoint.py              # Router: /api/psyche (duplikat!)
├── writing_endpoint.py             # Router: /api/writing
├── programista_endpoint.py         # Router: /api/code
├── travel_endpoint.py              # Router: /api/travel
├── requirements.txt                # Zależności Python
├── start.sh                        # Skrypt startowy (dev)
├── start_api.sh                    # Skrypt startowy (prod)
├── deploy.py                       # Deployment script
├── print_routes.py                 # Narzędzie diagnostyczne
└── [pliki patch_*, fix_*, tools_*] # Pliki pomocnicze/patchy
```

## 1.2 WSZYSTKIE POTENCJALNE ENTRYPOINTY

### A) `app.py` (ROOT) - ⭐ GŁÓWNY ENTRYPOINT
**Lokalizacja:** `mrd/app.py`  
**Typ:** FastAPI aplikacja  
**Uruchomienie:**
```bash
# Dev
uvicorn app:app --host 0.0.0.0 --port 8080 --reload

# Prod (via start.sh)
bash start.sh

# Prod (via start_api.sh)
bash start_api.sh
```

**Co robi:**
- Tworzy `FastAPI()` aplikację
- Ładuje `.env` z `ROOT_DIR/.env`
- Dynamicznie importuje routery z listy `root_modules` i `core_modules`
- Obsługuje błędy importów (try/except, non-fatal)
- Mountuje frontend statyczny
- Dodaje CORS middleware
- Endpoint `/health` i `/api/routers/status`

**Routery ładowane:**
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

**Problem:** Dynamiczne importy z try/except - jeśli router się nie załaduje, jest pomijany bez błędu.

---

### B) `core/app.py` - ⚠️ ALTERNATYWNY ENTRYPOINT
**Lokalizacja:** `mrd/core/app.py`  
**Typ:** FastAPI aplikacja (alternatywna)  
**Uruchomienie:**
```bash
uvicorn core.app:app --host 0.0.0.0 --port 8080
```

**Co robi:**
- Tworzy `FastAPI()` aplikację
- Importuje routery bezpośrednio (nie dynamicznie):
  - `assistant_endpoint` (root)
  - `psyche_endpoint` (root)
  - `programista_endpoint` (root)
  - `files_endpoint` (root)
  - `travel_endpoint` (root)
  - `admin_endpoint` (core)
  - `captcha_endpoint` (core - może nie istnieć!)
  - `prometheus_endpoint` (root)
  - `tts_endpoint` (root)
  - `stt_endpoint` (root)
  - `writing_endpoint` (root)
  - `suggestions_endpoint` (root)
  - `batch_endpoint` (root)
  - `research_endpoint` (root)

**Problem:** Importuje `captcha_endpoint` który może nie istnieć (brak w repo).

---

### C) `__main__` (brak)
Brak `if __name__ == "__main__"` w `app.py` root, ale jest w `core/app.py` (linie 623-645).

---

### D) Skrypty startowe

#### `start.sh`
**Lokalizacja:** `mrd/start.sh`  
**Co robi:**
1. Sprawdza Python3
2. Zabija stare sesje na porcie 8080
3. Sprawdza Node.js/npm
4. Buduje frontend Angular (`npm run build:prod`)
5. Tworzy venv i instaluje requirements.txt
6. Inicjalizuje bazę danych SQLite
7. Uruchamia `uvicorn app:app --host 0.0.0.0 --port 8080`

**Entrypoint:** `app:app` (root)

#### `start_api.sh`
**Lokalizacja:** `mrd/start_api.sh`  
**Co robi:**
1. Zabija proces na porcie 8080
2. Ładuje `.env`
3. Ustawia PYTHONPATH
4. Uruchamia `uvicorn app:app` w tle

**Entrypoint:** `app:app` (root)

---

## 1.3 ENTRYPOINT TRUTH - JEDEN DOCELOWY SPOSÓB

### ✅ DECYZJA: `app.py` (ROOT) jako JEDYNY entrypoint

**Uzasadnienie:**
1. `app.py` (root) ma dynamiczne ładowanie routerów z obsługą błędów
2. `core/app.py` ma hardcoded importy które mogą się wywalić
3. Skrypty startowe (`start.sh`, `start_api.sh`) wskazują na `app:app` (root)
4. `app.py` (root) ma lepszą diagnostykę (`/api/routers/status`)

### 🎯 DOCELOWY SPOSÓB URUCHOMIENIA

#### DEV (development):
```bash
cd /path/to/mrd
source .venv/bin/activate  # jeśli venv
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

#### PROD (production):
```bash
cd /path/to/mrd
# Opcja 1: via start.sh (pełna inicjalizacja)
bash start.sh

# Opcja 2: via start_api.sh (szybki start)
bash start_api.sh

# Opcja 3: via gunicorn (dla większego obciążenia)
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

### ⚠️ CO MUSI BYĆ ZROBIONE, ŻEBY START BYŁ BEZ BŁĘDÓW

#### P0 - BLOKUJĄCE START:

1. **Importy - brakujące moduły:**
   - ❌ `captcha_endpoint` importowany w `core/app.py:306` - **NIE ISTNIEJE**
   - ✅ Wszystkie inne moduły istnieją

2. **ENV - wymagane zmienne:**
   - `LLM_API_KEY` - **WYMAGANE** (bez tego chat nie działa)
   - `LLM_MODEL` - **WYMAGANE** (default: "Qwen/Qwen3-Next-80B-A3B-Instruct")
   - `LLM_BASE_URL` - opcjonalne (default: "https://api.deepinfra.com/v1/openai")
   - `AUTH_TOKEN` - opcjonalne (default: "ssjjMijaja6969" - **INSECURE!**)
   - `MEM_DB` - opcjonalne (default: `ROOT_DIR/mem.db`)
   - `UPLOAD_DIR` - opcjonalne (default: `/workspace/mrd/out/uploads`)

3. **Ścieżki - katalogi:**
   - `logs/` - tworzony automatycznie w `app.py:24`
   - `data/` - tworzony w `assistant_simple.py:23`
   - `UPLOAD_DIR` - tworzony w `files_endpoint.py:26`
   - `mem.db` - tworzony automatycznie przy pierwszym użyciu

4. **Zależności Python:**
   - Wszystkie z `requirements.txt` muszą być zainstalowane
   - **KRYTYCZNE:** `fastapi`, `uvicorn`, `httpx`, `pydantic>=2.9.0`
   - **OPCJONALNE:** `redis` (dla cache), `spacy` (dla NLP)

5. **Baza danych:**
   - SQLite `mem.db` - tworzona automatycznie
   - Tabele tworzone w `start.sh` (linie 182-252) lub przy pierwszym użyciu

#### P1 - BLOKUJĄCE FUNKCJE (ale nie start):

1. **LLM API:**
   - Bez `LLM_API_KEY` - chat zwraca błąd "⚠️ Brak LLM_API_KEY w .env"
   - Bez `LLM_MODEL` - używa defaultu

2. **TTS/STT:**
   - `ELEVENLABS_API_KEY` - wymagane dla TTS
   - `ELEVENLABS_VOICE_ID` - wymagane dla TTS
   - `OPENAI_API_KEY` lub `GROQ_API_KEY` - wymagane dla STT

3. **Redis (opcjonalny):**
   - Jeśli `core/redis_middleware.py` jest używany, Redis powinien być dostępny
   - Fallback do mock jeśli brak

---

## 1.4 PROBLEMY Z ENTRYPOINTAMI

### ❌ PROBLEM 1: Dwa entrypointy (`app.py` vs `core/app.py`)

**Objaw:** Dwa różne pliki tworzą FastAPI aplikację  
**Przyczyna:** Prawdopodobnie refaktor - `core/app.py` to stara wersja  
**Wpływ:** 
- Niepewność który entrypoint używać
- Różne routery w różnych entrypointach
- `core/app.py` importuje nieistniejący `captcha_endpoint`

**Naprawa:**
1. Usunąć `core/app.py` LUB
2. Przenieść do `core/app.py.bak` i zaktualizować dokumentację
3. Upewnić się że wszystkie skrypty wskazują na `app:app` (root)

**Weryfikacja:**
```bash
# Sprawdź który entrypoint jest używany
grep -r "uvicorn.*app" start.sh start_api.sh deploy.py

# Sprawdź czy core/app.py jest importowany gdziekolwiek
grep -r "from core.app import\|import core.app\|core.app:app" .
```

---

### ❌ PROBLEM 2: Dynamiczne importy z try/except (non-fatal errors)

**Objaw:** Routery które się nie ładują są pomijane bez błędu  
**Lokalizacja:** `app.py:82-161`  
**Przyczyna:** `_try_import_router()` i `_include()` zwracają `None` przy błędzie  
**Wpływ:**
- Ciche pomijanie routerów z błędami
- Trudne debugowanie - trzeba sprawdzić `/api/routers/status`

**Naprawa:**
1. Dodać opcję `STRICT_ROUTER_LOADING=1` w ENV
2. Jeśli `STRICT_ROUTER_LOADING=1`, rzucić wyjątek zamiast pomijać
3. Domyślnie `STRICT_ROUTER_LOADING=0` (backward compatibility)

**Weryfikacja:**
```bash
# Sprawdź które routery się załadowały
curl http://localhost:8080/api/routers/status | jq '.loaded, .failed'
```

---

### ❌ PROBLEM 3: Brakujący `captcha_endpoint` w `core/app.py`

**Objaw:** Import `captcha_endpoint` w `core/app.py:306`  
**Lokalizacja:** `core/app.py:306`  
**Przyczyna:** Plik `captcha_endpoint.py` nie istnieje w repo  
**Wpływ:** Jeśli ktoś użyje `core/app.py` jako entrypoint, aplikacja się nie uruchomi

**Naprawa:**
1. Usunąć import `captcha_endpoint` z `core/app.py:306` LUB
2. Utworzyć pusty `captcha_endpoint.py` z routerem (jeśli funkcja jest potrzebna) LUB
3. Opakować w try/except jak w `app.py` (root)

**Weryfikacja:**
```bash
# Sprawdź czy captcha_endpoint istnieje
find . -name "*captcha*" -type f

# Sprawdź import
grep -n "captcha_endpoint" core/app.py
```

---

## 1.5 REKOMENDACJE

### ✅ ENTRYPOINT TRUTH (docelowy):

**Używać:** `app.py` (root) jako JEDYNY entrypoint

**Komendy:**
```bash
# Dev
uvicorn app:app --host 0.0.0.0 --port 8080 --reload

# Prod (via start.sh)
bash start.sh

# Prod (via gunicorn)
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

### ✅ USUNIĘCIE `core/app.py`:

**Akcja:** Przenieść `core/app.py` do `core/app.py.legacy` i zaktualizować dokumentację

**Uzasadnienie:**
- `app.py` (root) ma lepszą diagnostykę
- `app.py` (root) ma dynamiczne ładowanie z obsługą błędów
- Wszystkie skrypty wskazują na `app:app` (root)

---

## 1.6 CHECKLISTA NAPRAWY (P0)

- [ ] **P0.1:** Usunąć/archiwizować `core/app.py` (lub opakować importy w try/except)
- [ ] **P0.2:** Usunąć import `captcha_endpoint` z `core/app.py:306` (jeśli zostaje)
- [ ] **P0.3:** Dodać `.env.example` z wymaganymi zmiennymi
- [ ] **P0.4:** Zweryfikować że wszystkie skrypty wskazują na `app:app` (root)
- [ ] **P0.5:** Dodać walidację ENV przy starcie (opcjonalnie - warning jeśli brak LLM_API_KEY)

---

**KONIEC CZĘŚCI 1**

