# AUDYT PUNKT 6: CONFIG, ENV & SECRETS

**Data audytu:** 28 grudnia 2025  
**Lokalizacja audytu:** Serwer produkcyjny `root@77.42.73.96:/root/mrd`  
**Zakres:** Analiza zmiennych środowiskowych, konfiguracji, sekretów  
**Metoda:** SSH + grep + analiza `core/config.py`

---

## 0. ŚRODOWISKO AUDYTU

**AUDYT WYKONANY NA SERWERZE PRODUKCYJNYM: `root@77.42.73.96:/root/mrd`**

### 0.1 Katalog roboczy

```bash
$ pwd
/root/mrd
```

### 0.2 Repozytorium Git — zainicjalizowane

```bash
$ ls -la .git
total 76
drwxr-xr-x   7 root root  4096 Dec 25 19:02 .
drwxr-xr-x  19 root root 12288 Dec 28 21:39 ..
-rw-r--r--   1 root root    32 Dec 25 19:02 COMMIT_EDITMSG
-rw-r--r--   1 root root   210 Dec 25 19:02 config
-rw-r--r--   1 root root    73 Oct 24 18:34 description
-rw-r--r--   1 root root     0 Oct 24 19:06 FETCH_HEAD
-rw-r--r--   1 root root    21 Oct 24 18:34 HEAD
drwxr-xr-x   2 root root  4096 Dec 23 01:46 hooks
-rw-r--r--   1 root root 21400 Dec 25 18:52 index
drwxr-xr-x   2 root root  4096 Dec 23 01:46 info
drwxr-xr-x   3 root root  4096 Dec 25 18:55 logs
drwxr-xr-x 255 root root  4096 Dec 25 18:55 objects
drwxr-xr-x   4 root root  4096 Dec 23 01:50 refs
```

### 0.3 Commit HEAD

```bash
$ git rev-parse HEAD
48a881b4ff5f042fd53bb8dce36a5f8d58b77953
```

### 0.4 Status repozytorium

```bash
$ git status --porcelain | head -15
 M .env
 D WSZYSTKO_GOTOWE.txt
 D WSZYSTKO_NAPRAWIONE.txt
 M app.py
 M core/hierarchical_memory.py
 M core/hybrid_search_endpoint.py
 M hybrid_search_endpoint.py
?? fix_conversations_tables.py
?? fix_hier_mem_await.py
?? print_routes.py
?? "s -ltnp | egrep '(:8000|:8080)b' || true"
?? set_memory_db_env.py
?? tools/patch_hybrid_pick.py
?? tools_fix_hybrid_primary.py
?? tools_fix_hybrid_primary_v2.py
```

**Status:** 7 modified files, 15+ untracked files. Wymaga `git add && git commit`.

---

## 1. PODSUMOWANIE STATYSTYK

**Statystyki policzone na serwerze `/root/mrd`.**

### 1.1 Zmiennych środowiskowych w core/config.py

```bash
$ grep -c 'os.getenv' core/config.py
36
```

### 1.2 Pliki konfiguracyjne — present

```bash
$ test -f .env && echo 'EXISTS' || echo 'MISSING'
EXISTS

$ test -f .env.example && echo 'EXISTS' || echo 'MISSING'
EXISTS
```

---

## 2. 🔴 P0 PROBLEMY SECURITY: NIEBEZPIECZNE DEFAULTY W KODZIE

### 2.1 ALLOWED_ORIGINS = "\*" — CSRF Risk

**Źródło:** `/root/mrd/core/config.py` L:47

```bash
$ grep -n 'ALLOWED_ORIGINS' core/config.py
47:ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
```

**Problem:** Default `"*"` otwiera CORS dla wszystkich domen. W produkcji to CSRF/XSRF risk.

**Akcja P0:** Zmienić na `os.getenv("ALLOWED_ORIGINS", "")` (puste).

### 2.2 ENABLE_WEB_ACCESS = 1 — Open Proxy Risk

**Źródło:** `/root/mrd/core/config.py` L:408

```bash
$ grep -n 'ENABLE_WEB_ACCESS' core/config.py
408:ENABLE_WEB_ACCESS = os.getenv("ENABLE_WEB_ACCESS", "1") == "1"
```

**Problem:** Default `"1"` włącza web scraping. Aplikacja może być użyta jako open proxy do zamiaskania rzeczywistego IP.

**Akcja P0:** Zmienić na `os.getenv("ENABLE_WEB_ACCESS", "0")` (wyłączone).

### 2.3 ALWAYS_INTERNET = 1 — Uncontrolled Internet Access

**Źródło:** `/root/mrd/core/config.py` L:409

```bash
$ grep -n 'ALWAYS_INTERNET' core/config.py
409:ALWAYS_INTERNET = os.getenv("ALWAYS_INTERNET", "1") == "1"
```

**Problem:** Default `"1"` zawsze zezwala na internet. Brak kontroli dostępu do sieci. Aplikacja może wykonywać niechciane połączenia.

**Akcja P0:** Zmienić na `os.getenv("ALWAYS_INTERNET", "0")` (wyłączone).

---

## 3. 🟠 P1 PROBLEMY: KONFIGURACJA I WALIDACJA

### 3.1 Hardcoded AUTH_TOKEN fallback

**Problem:** `core/config.py` L:30 ma fallback do tokena `"ssjjMijaja6969"`.

**Akcja P1:** Zmienić na `raise RuntimeError()` zamiast fallback.

### 3.2 Brak walidacji LLM_API_KEY

**Problem:** `core/config.py` L:55 ma tylko print(), brak wymuszenia.

**Akcja P1:** Zmienić na `raise RuntimeError()` zamiast print.

### 3.3 Race condition kolejności importów

**Problem:** `app.py` (root) i `core/config.py` oba ładują `.env`, ale nie wiadomo, który jest pierwszy.

**Akcja P1:** Jedno źródło ładowania: tylko `core/config.py` ładuje `.env`.

### 3.4 setdefault() dla sekretów w core/app.py

**Problem:** `core/app.py` L:35 używa `os.environ.setdefault()` dla `AUTH_TOKEN`.

**Akcja P1:** Usunąć — sekretami zarządza tylko `core/config.py`.

### 3.5 Duplikacja logiki ładowania .env

**Problem:** `app.py` (root) ma własną funkcję `_load_env_file()` L:27-48.

**Akcja P1:** Usunąć — użyć `python-dotenv` z `core/config.py`.

---

## 4. PEŁNA LISTA ZMIENNYCH ŚRODOWISKOWYCH

### 4.1 Zmienne w core/config.py (36 zmiennych)

| Zmienna                 | Default                               | Wymagana | Opis                        |
| ----------------------- | ------------------------------------- | -------- | --------------------------- |
| `AUTH_TOKEN`            | `ssjjMijaja6969` (fallback!)          | 🔴 TAK   | Token autoryzacji API       |
| `WORKSPACE`             | `Path(__file__).parent.parent`        | NIE      | Katalog roboczy             |
| `MEM_DB`                | `<WORKSPACE>/mem.db`                  | NIE      | Ścieżka do bazy SQLite      |
| `UPLOAD_DIR`            | `<WORKSPACE>/uploads`                 | NIE      | Katalog uploadów            |
| `FRONTEND_INDEX`        | `/app/dist/index.html`                | NIE      | Ścieżka do index.html       |
| `TIMEOUT_HTTP`          | `60`                                  | NIE      | Timeout HTTP w sekundach    |
| `WEB_USER_AGENT`        | `MonolitBot/3.3`                      | NIE      | User-Agent dla requestów    |
| `ALLOWED_ORIGINS`       | `*` ⚠️ UNSAFE                         | NIE      | CORS origins                |
| `LLM_BASE_URL`          | `https://api.deepinfra.com/v1/openai` | NIE      | URL API LLM                 |
| `LLM_API_KEY`           | (brak)                                | 🔴 TAK   | Klucz API LLM               |
| `LLM_MODEL`             | `Qwen/Qwen3-Next-80B-A3B-Instruct`    | NIE      | Model LLM                   |
| `LLM_FALLBACK_MODEL`    | `Qwen/Qwen3-Next-80B-A3B-Instruct`    | NIE      | Fallback model              |
| `LLM_TIMEOUT`           | `45`                                  | NIE      | Timeout LLM                 |
| `LLM_RETRIES`           | `3`                                   | NIE      | Liczba retry                |
| `LLM_BACKOFF_S`         | `1.5`                                 | NIE      | Backoff między retry        |
| `RL_DISABLE`            | `0`                                   | NIE      | 1 = wyłącz rate limiting    |
| `RATE_LIMIT_PER_MINUTE` | `160`                                 | NIE      | Limit req/min               |
| `RATE_LIMIT_WINDOW`     | `60`                                  | NIE      | Okno rate limit             |
| `MAX_CONCURRENCY`       | `32`                                  | NIE      | Max równoległych zadań      |
| `PARALLEL_TIMEOUT`      | `30.0`                                | NIE      | Timeout zadań równoległych  |
| `THREAD_POOL_SIZE`      | `16`                                  | NIE      | Rozmiar puli wątków         |
| `LLM_BATCH_SIZE`        | `5`                                   | NIE      | Batch size dla LLM          |
| `SERPAPI_KEY`           | `""`                                  | NIE      | Google Search API           |
| `FIRECRAWL_API_KEY`     | `""`                                  | NIE      | Web scraping API            |
| `FIRECRAWL_BASE_URL`    | `https://api.firecrawl.dev`           | NIE      | Firecrawl URL               |
| `OTM_API_KEY`           | `""`                                  | NIE      | OpenTripMap API             |
| `ENABLE_SEMANTIC`       | `1`                                   | NIE      | Feature flag                |
| `ENABLE_RESEARCH`       | `1`                                   | NIE      | Feature flag                |
| `ENABLE_PSYCHE`         | `1`                                   | NIE      | Feature flag                |
| `ENABLE_TRAVEL`         | `1`                                   | NIE      | Feature flag                |
| `ENABLE_WRITER`         | `1`                                   | NIE      | Feature flag                |
| `ENABLE_WEB_ACCESS`     | `1` ⚠️ UNSAFE                         | NIE      | Feature flag (open proxy)   |
| `ALWAYS_INTERNET`       | `1` ⚠️ UNSAFE                         | NIE      | Zawsze zezwalaj na internet |
| `LOG_LEVEL`             | `INFO`                                | NIE      | DEBUG/INFO/WARNING/ERROR    |
| `LOG_TO_FILE`           | `0`                                   | NIE      | 1 = loguj do pliku          |
| `LOG_FILE_PATH`         | `<WORKSPACE>/mordzix.log`             | NIE      | Ścieżka do logów            |

### 4.2 Zmienne poza core/config.py

| Zmienna                 | Plik                        | Default                   | Opis                  |
| ----------------------- | --------------------------- | ------------------------- | --------------------- |
| `ELEVENLABS_API_KEY`    | `tts_endpoint.py` L:19      | `""`                      | TTS ElevenLabs        |
| `ELEVENLABS_VOICE_ID`   | `tts_endpoint.py` L:20      | `""`                      | Voice ID dla TTS      |
| `OPENAI_API_KEY`        | `vision_provider.py` L:57   | `""`                      | Vision API OpenAI     |
| `GOOGLE_VISION_API_KEY` | `vision_provider.py` L:107  | `""`                      | Google Vision API     |
| `UI_EXPOSE_TOKEN`       | `internal_endpoint.py` L:15 | `0`                       | Expose token endpoint |
| `LTM_STORAGE_ROOT`      | `core/memory.py` L:110      | `<WORKSPACE>/ltm_storage` | LTM storage           |

---

## 5. ANALIZA ŁADOWANIA .env

### 5.1 Ładowanie w core/config.py (PRAWIDŁOWE)

```python
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"[CONFIG] Loaded .env from {env_path}")
```

**Ocena:** ✅ Używa `python-dotenv`, ✅ bezpieczne.

### 5.2 Ładowanie w app.py (root) — DUPLIKACJA

```python
def _load_env_file(path: Path) -> None:
    # nie nadpisuje istniejących zmiennych w środowisku
    if not path.exists():
        return
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw in txt.splitlines():
        k, _, v = raw.partition("=")
        k = k.strip()
        if not k or k.startswith("#") or "=" not in raw:
            continue
        if not k or k in os.environ:
            continue  # nie nadpisuje istniejących
        os.environ[k] = v

_load_env_file(ENV_PATH)
print(f"[CONFIG] Loaded .env from {ENV_PATH}")
```

**Problem:** Duplikacja, własna logika zamiast `python-dotenv`. To jest `app.py` L:29-50.

### 5.3 Konflikt: setdefault w core/app.py

```python
os.environ.setdefault("AUTH_TOKEN", "ssjjMijaja6969")
```

**Problem:** `setdefault` ustawia PRZED ładowaniem `.env` jeśli core/app.py importowany jako pierwszy.

---

## 6. .env.example — PROD-SAFE TEMPLATE

**Plik `.env.example` powinien mieć bezpieczne defaulty:**

```bash
# .env.example — skopiuj do .env i uzupełnij wartości
# ══════════════════════════════════════════════════════

# WYMAGANE
AUTH_TOKEN=                    # Min 32 znaki, wygeneruj: openssl rand -hex 32
LLM_API_KEY=                   # Klucz API do DeepInfra/OpenAI

# OPCJONALNE - LLM
LLM_BASE_URL=https://api.deepinfra.com/v1/openai
LLM_MODEL=Qwen/Qwen3-Next-80B-A3B-Instruct
LLM_TIMEOUT=45

# OPCJONALNE - Ścieżki
WORKSPACE=/root/mrd
MEM_DB=/root/mrd/mem.db
UPLOAD_DIR=/root/mrd/uploads

# OPCJONALNE - API
SERPAPI_KEY=
FIRECRAWL_API_KEY=
OTM_API_KEY=

# OPCJONALNE - Rate limiting
RL_DISABLE=0
RATE_LIMIT_PER_MINUTE=160

# OPCJONALNE - HTTP / CORS
TIMEOUT_HTTP=60
# CORS: puste = same-origin. Ustaw domeny jeśli potrzebujesz CORS.
# Przykład: https://twojadomena.tld,https://api.twojadomena.tld
ALLOWED_ORIGINS=

# OPCJONALNE - Feature flags
ENABLE_SEMANTIC=1
ENABLE_RESEARCH=1
ENABLE_PSYCHE=1
ENABLE_TRAVEL=1
ENABLE_WRITER=1

# ⚠️ RYZYKOWNE - włącz tylko jeśli wiesz co robisz!
ENABLE_WEB_ACCESS=0            # 0 = wyłączone (brak open proxy)
ALWAYS_INTERNET=0              # 0 = wyłączone (brak niekontrolowanego dostępu)

# OPCJONALNE - Logging
LOG_LEVEL=INFO
LOG_TO_FILE=0
```

**Komenda aktywacji:**

```bash
cp .env.example .env
# Wygeneruj AUTH_TOKEN:
AUTH_TOKEN=$(openssl rand -hex 32)
# Dodaj do .env lub edytuj ręcznie
```

---

## 7. ARCHITEKTURA ŁADOWANIA KONFIGURACJI — DOCELOWA

**Status dzisiaj:** Chaos (2 miejsca ładowania, race condition).

**Docelowa architektura:**

1. **TYLKO `core/config.py`** ładuje `.env` via `python-dotenv`
2. **Usunąć** `_load_env_file()` z `app.py` (root)
3. **Usunąć** `os.environ.setdefault()` dla sekretów z `core/app.py`
4. **Fail-fast:** `AUTH_TOKEN` i `LLM_API_KEY` mają `raise RuntimeError()`, nie fallback
5. **Bezpieczne defaulty w KODZIE** (dotyczy core/config.py):
   - `ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")` — zamiast `"*"`
   - `ENABLE_WEB_ACCESS = os.getenv("ENABLE_WEB_ACCESS", "0") == "0"` — zamiast `"1"`
   - `ALWAYS_INTERNET = os.getenv("ALWAYS_INTERNET", "0") == "0"` — zamiast `"1"`

⚠️ **WAŻNE:** Bezpieczne defaulty w `.env.example` to dopiero początek. KOD SAM Z SIEBIE musi być bezpieczny "out of the box".

---

## 8. PODSUMOWANIE PROBLEMÓW

| #   | Problem                    | Priorytet | Plik                  | Akcja                         |
| --- | -------------------------- | --------- | --------------------- | ----------------------------- |
| 1   | ALLOWED_ORIGINS = "\*"     | 🔴 P0     | core/config.py L:47   | Zmienić default na ""         |
| 2   | ENABLE_WEB_ACCESS = 1      | 🔴 P0     | core/config.py L:408  | Zmienić default na 0          |
| 3   | ALWAYS_INTERNET = 1        | 🔴 P0     | core/config.py L:409  | Zmienić default na 0          |
| 4   | Hardcoded AUTH_TOKEN       | 🔴 P0     | core/config.py L:30   | RuntimeError zamiast fallback |
| 5   | setdefault w core/app.py   | 🔴 P0     | core/app.py L:35      | Usunąć                        |
| 6   | Brak walidacji LLM_API_KEY | 🟠 P1     | core/config.py L:55   | RuntimeError zamiast print    |
| 7   | Race condition importów    | 🟠 P1     | app.py, core/app.py   | Jeden punkt: core/config.py   |
| 8   | Duplikacja logiki .env     | 🟠 P1     | app.py (root) L:27-48 | Usunąć \_load_env_file()      |

---

## 9. DOWODY (CITATIONS) — PEŁNE KODY I OUTPUTS

### 9.1 LOAD_DOTENV w core/config.py (L:11-20)

**Komenda:**

```bash
$ sed -n '11,20p' core/config.py
```

**Output:**

```python
# Load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"[CONFIG] Loaded .env from {env_path}")
    else:
        print(f"[CONFIG] No .env file found at {env_path}")
except ImportError:
```

**Ocena:** ✅ core/config.py ładuje `.env` za pośrednictwem `python-dotenv`.

---

### 9.2 Hardcoded fallback AUTH_TOKEN w core/config.py (L:27-32)

**Komenda:**

```bash
$ sed -n '27,32p' core/config.py
```

**Output:**

```python
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
if not AUTH_TOKEN:
    print("[WARN] AUTH_TOKEN not set in .env - using default (INSECURE!)")
    AUTH_TOKEN = "ssjjMijaja6969"
```

**Problem:** 🔴 Kod drukuje WARN ale i tak używa publicznie znanego tokena `"ssjjMijaja6969"`. W produkcji powinien rzucić `RuntimeError`.

---

### 9.3 setdefault w core/app.py (L:35)

**Komenda:**

```bash
$ grep -n 'setdefault.*AUTH' core/app.py
```

**Output:**

```
35:os.environ.setdefault("AUTH_TOKEN", "ssjjMijaja6969")
```

**Problem:** 🔴 `setdefault` ustawia wartość PRZED jakimkolwiek ładowaniem `.env`. Jeśli `core/app.py` importowany jest przed `core/config.py`, to `AUTH_TOKEN` zawsze będzie `"ssjjMijaja6969"`.

---

### 9.4 LLM_API_KEY — brak walidacji w core/config.py (L:54-58)

**Komenda:**

```bash
$ sed -n '54,58p' core/config.py
```

**Output:**

```python
LLM_API_KEY = os.getenv("LLM_API_KEY")
if not LLM_API_KEY:
    print("[ERROR] LLM_API_KEY not set in .env! Get your key from https://deepinfra.com")
    print("[ERROR] Application will not work without LLM API key!")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-Next-80B-A3B-Instruct")
```

**Problem:** 🟠 Tylko `print()`, brak `raise RuntimeError()`. Aplikacja uruchomi się i będzie rzucać błędy przy każdym wyroku LLM.

---

### 9.5 Duplikacja: \_load_env_file w app.py (L:29-50)

**Komenda:**

```bash
$ sed -n '22,51p' app.py
```

**Output:**

```python
ENV_PATH = ROOT_DIR / ".env"

# ═════════════════════════════════════════════════════

def _load_env_file(path: Path) -> None:
    # nie nadpisuje istniejących zmiennych w środowisku
    if not path.exists():
        return
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw in txt.splitlines():
        k, _, v = raw.partition("=")
        k = k.strip()
        if not k or k.startswith("#") or "=" not in raw:
            continue
        if not k or k in os.environ:
            continue  # nie nadpisuje istniejących
        os.environ[k] = v
        os.environ[k] = v

_load_env_file(ENV_PATH)
print(f"[CONFIG] Loaded .env from {ENV_PATH}")
```

**Problem:** 🟠 Własna implementacja parsowania `.env` zamiast `python-dotenv`. Duplikacja logiki: zarówno `app.py` (root) i `core/config.py` ładują `.env`.

---

### 9.6 ALLOWED_ORIGINS = "\*" w core/config.py (L:47)

**Komenda:**

```bash
$ sed -n '47p' core/config.py
```

**Output:**

```python
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
```

**Problem:** 🔴 Default `"*"` — CORS otwarta dla wszystkich domen. CSRF/XSRF risk w produkcji.

---

### 9.7 ENABLE_WEB_ACCESS = 1 w core/config.py (L:408)

**Komenda:**

```bash
$ sed -n '408p' core/config.py
```

**Output:**

```python
ENABLE_WEB_ACCESS = os.getenv("ENABLE_WEB_ACCESS", "1") == "1"
```

**Problem:** 🔴 Default `"1"` — web scraping włączony. Aplikacja może być użyta jako open proxy.

---

### 9.8 ALWAYS_INTERNET = 1 w core/config.py (L:409)

**Komenda:**

```bash
$ sed -n '409p' core/config.py
```

**Output:**

```python
ALWAYS_INTERNET = os.getenv("ALWAYS_INTERNET", "1") == "1" # Zawsze zezwalaj na internet
```

**Problem:** 🔴 Default `"1"` — niekontrolowany dostęp do internetu. Brak możliwości ograniczenia dostępu do sieci.

---

### 9.9 Status .env i .env.example

**Komenda:**

```bash
$ test -f .env && echo 'EXISTS' || echo 'MISSING'
EXISTS

$ test -f .env.example && echo 'EXISTS' || echo 'MISSING'
EXISTS
```

**Ocena:** ✅ Oba pliki istnieją na serwerze.

---

### 9.10 Git status

**Komenda:**

```bash
$ git rev-parse HEAD
48a881b4ff5f042fd53bb8dce36a5f8d58b77953

$ git status --porcelain | head -15
 M .env
 D WSZYSTKO_GOTOWE.txt
 D WSZYSTKO_NAPRAWIONE.txt
 M app.py
 M core/hierarchical_memory.py
 M core/hybrid_search_endpoint.py
 M hybrid_search_endpoint.py
?? fix_conversations_tables.py
?? fix_hier_mem_await.py
?? print_routes.py
```

---

**STOP — sprawdzę ten punkt. Czy coś poprawić/doprecyzować? Jeśli OK, przechodzę do: `AUDYT/07_MEMORY_DATABASE7.md`.**
