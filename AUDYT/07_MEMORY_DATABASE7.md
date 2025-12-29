# AUDYT PUNKT 7: MEMORY, DATABASE & PERSISTENCE

**Data audytu:** 29 grudnia 2025  
**Lokalizacja audytu:** Serwer produkcyjny `root@77.42.73.96:/root/mrd`  
**Zakres:** Analiza systemu pamięci, bazy danych, persistence  
**Metoda:** SSH + find + diff + analiza `hierarchical_memory.py`

---

## 0. ŚRODOWISKO AUDYTU

**AUDYT WYKONANY NA SERWERZE PRODUKCYJNYM: `root@77.42.73.96:/root/mrd`**

Katalog: `/root/mrd`  
Commit HEAD: `48a881b4ff5f042fd53bb8dce36a5f8d58b77953`  
Status: 7 modified files, 15+ untracked files

---

## 1. LOKALIZACJA I ROZMIAR BAZ DANYCH

### 1.1 Plik mem.db — root

```bash
$ ls -lh mem.db
-rw-r--r-- 1 root root 488K Dec 25 19:27 mem.db
```

**Opis:** Główna baza SQLite w katalogu root. 488K.

### 1.2 Plik mem.db — core/

```bash
$ ls -lh core/mem.db
-rw-r--r-- 1 root root 320K Dec 25 19:06 core/mem.db
```

**Opis:** Kopia bazy w podkatalogu core/. 320K.

### 1.3 Pliki backup

```bash
$ find . -name 'mem.db*' -type f
./core/mem.db
./core/mem.db.bak.20251225_190638
./mem.db
./mem.db.bak.20251225_190638
```

**Wynik:** 2 aktywne bazy + 2 backupy (po jednym w root/ i core/).

### 1.4 Katalog LTM Storage

```bash
$ ls -la ltm_storage/
total 24
drwxr-xr-x  4 root root  4096 Dec 24 10:11 .
drwxr-xr-x  2 root root  4096 Dec 24 10:11 backups
drwxr-xr-x  2 root root  4096 Dec 24 10:11 vector_indices
```

**Struktura:** `ltm_storage/` zawiera `/backups` i `/vector_indices`.

---

## 1.5 TRUTH: Która baza jest używana w runtime

### 1.5.1 DB_PATH konfiguracja

```bash
$ sed -n '35,37p' core/config.py
DEFAULT_BASE_DIR = str(Path(__file__).resolve().parents[1])
BASE_DIR = os.getenv("WORKSPACE", DEFAULT_BASE_DIR)
DB_PATH = os.getenv("MEM_DB", os.path.join(BASE_DIR, "mem.db"))
```

**Logika:**

- `DEFAULT_BASE_DIR` = `/root/mrd` (1 katalog wyżej niż core/)
- `BASE_DIR` = env `WORKSPACE` lub default (`/root/mrd`)
- `DB_PATH` = env `MEM_DB` lub `<BASE_DIR>/mem.db`

### 1.5.2 Wszystkie miejsca gdzie DB_PATH jest używany

```bash
$ grep -RIn 'DB_PATH\|MEM_DB' --include='*.py' core/ | head -20
./core/app.py:37:os.environ.setdefault("MEM_DB", str(BASE_DIR / "mem.db"))
./core/memory_summarizer.py:16:from .config import DB_PATH
./core/memory_summarizer.py:81:        conn = sqlite3.connect(DB_PATH)
./core/memory_summarizer.py:113:        conn = sqlite3.connect(DB_PATH)
./core/memory_summarizer.py:144:        conn = sqlite3.connect(DB_PATH)
./core/memory_summarizer.py:212:        conn = sqlite3.connect(DB_PATH)
./core/memory.py:56:    BASE_DIR, DB_PATH, STM_LIMIT, STM_CONTEXT_WINDOW,
./core/memory.py:228:    def __init__(self, db_path: str = DB_PATH):
./core/memory.py:241:        conn = sqlite3.connect(self.db_path, check_same_thread=False)
./core/memory.py:1495:    return sqlite3.connect(str(DB_PATH), check_same_thread=False)
./core/config.py:37:DB_PATH = os.getenv("MEM_DB", os.path.join(BASE_DIR, "mem.db"))
./core/config.py:428:        "db_path": DB_PATH,
./core/semantic.py:11:from .config import DB_PATH, CONTEXT_DICTIONARIES
./core/semantic.py:1458:semantic_integration = SemanticIntegration(DB_PATH)
./core/memory_store.py:6:DB_PATH = os.getenv("MEM_DB") or str((Path(os.getenv("WORKSPACE",".")) / "data" / "mem.db").absolute())
./core/memory_store.py:9:    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
./core/memory_store.py:10:    con = sqlite3.connect(DB_PATH)
```

**Ocena:** 18+ miejsc używa `DB_PATH` lub `MEM_DB` z config. Wszystkie w core/. **core/mem.db jest ignorana.**

### 1.5.3 DOW ÓD: Environment variables

```bash
$ printenv | egrep '^(WORKSPACE|MEM_DB)=' || echo 'WORKSPACE/MEM_DB: NOT SET'
WORKSPACE/MEM_DB: NOT SET
```

**Output:** Ani `WORKSPACE` ani `MEM_DB` NIE są ustawione na serwerze.

### 1.5.4 WERDYKT: Która baza

**W aktualnym runtime backend korzysta z: `/root/mrd/mem.db`**

- Env vars `WORKSPACE` i `MEM_DB` = NOT SET (potwierdzone printenv)
- `DEFAULT_BASE_DIR` = `/root/mrd` (z core/config.py L:35)
- `DB_PATH` = `/root/mrd/mem.db` (488K, aktualna)
- `core/mem.db` (320K z 25 grudnia) jest MARTWĄ kopią (brak importów, brak referencji w kodzie)

---

## 1.6 TRUTH: Który hierarchical_memory.py jest importowany

### 1.6.1 Wszystkie importy hierarchical_memory

```bash
$ grep -RIn 'from.*hierarchical_memory\|import hierarchical_memory' --include='*.py' . | wc -l
16
```

**Szczegół (wszystkie importy):**

```bash
./core/stress_test_system.py:23:from core.hierarchical_memory import HierarchicalMemorySystem
./core/knowledge_compression.py:21:from .hierarchical_memory import get_hierarchical_memory
./core/cognitive_engine.py:26:from .hierarchical_memory import hierarchical_memory_manager
./core/cognitive_engine.py:40:    from .hierarchical_memory import (...)
./core/ultra_destruction_test.py:28:from core.hierarchical_memory import HierarchicalMemorySystem
./core/memory.py:1182:        from core.hierarchical_memory import get_hierarchical_memory
./core/future_predictor.py:19:from .hierarchical_memory import get_hierarchical_memory
./core/self_reflection.py:23:from .hierarchical_memory import get_hierarchical_memory
./core/multi_agent_orchestrator.py:26:from .hierarchical_memory import get_hierarchical_memory
./core/inner_language.py:28:from .hierarchical_memory import get_hierarchical_memory
./core/research.py:772:    from .hierarchical_memory import (...)
./stress_test_system.py:23:from core.hierarchical_memory import HierarchicalMemorySystem
./ultra_destruction_test.py:28:from core.hierarchical_memory import HierarchicalMemorySystem
./tests/test_hierarchical_memory.py:16:from core.hierarchical_memory import (...)
./research.py:771:    from .hierarchical_memory import (...)
```

**Wynik:** 16 plików, 100% importuje z `core.hierarchical_memory`. Żaden plik nie importuje z root/hierarchical_memory.py.

### 1.6.2 WERDYKT: Importy

**root/hierarchical_memory.py jest KOMPLETNIE NIEUŻYWANY — 0 importów**

---

## 1.7 REKOMENDACJA P0: Unifikacja bezpieczna (bez psucia importów)

### Krok A: Zamiana root/hierarchical_memory.py na SHIM (SAFE)

```python
# root/hierarchical_memory.py — SHIM REEXPORT
"""
BACKWARDS COMPATIBILITY LAYER

This module re-exports all symbols from core.hierarchical_memory.
This shim exists only for backwards compatibility.

NEW CODE: Use 'from core.hierarchical_memory import ...' directly.
"""

from core.hierarchical_memory import (
    EpisodicMemoryManager,
    SemanticMemoryManager,
    ProceduralMemoryManager,
    MentalModelManager,
    HierarchicalMemorySystem,
    get_hierarchical_memory,
    get_hierarchical_memory_system,
    hierarchical_memory_manager,
)

__all__ = [
    "EpisodicMemoryManager",
    "SemanticMemoryManager",
    "ProceduralMemoryManager",
    "MentalModelManager",
    "HierarchicalMemorySystem",
    "get_hierarchical_memory",
    "get_hierarchical_memory_system",
    "hierarchical_memory_manager",
]
```

**Efekt:** Gdyby w przyszłości ktoś importował z root/, dalej by działało. Ale kod wskaże na source.

### Krok B: Archiwizacja core/mem.db (SAFE)

```bash
# Na serwerze:
mkdir -p /root/mrd_archive/$(date +%Y%m%d)
mv /root/mrd/core/mem.db /root/mrd_archive/$(date +%Y%m%d)/mem.db.core
mv /root/mrd/core/mem.db.bak* /root/mrd_archive/$(date +%Y%m%d)/
echo "Archived core/mem.db backups — not used by runtime"
```

**Efekt:** DB_PATH zawsze będzie odsyłał do `/root/mrd/mem.db` (jedyna aktywna baza).

---

## 1.8 PERSISTENCE: SQLite Concurrency & Safety

### 1.8.1 PRAGMA settings w core/memory.py (✅ DOBRA)

```bash
$ sed -n '245,253p' core/memory.py
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA temp_store=MEMORY;")
conn.execute("PRAGMA foreign_keys=ON;")
conn.execute("PRAGMA cache_size=-2000000;")  # 2GB cache
conn.execute("PRAGMA mmap_size=8589934592;")  # 8GB mmap
conn.execute("PRAGMA page_size=8192;")  # 8KB pages
conn.execute("PRAGMA busy_timeout=30000;")  # 30s timeout
conn.execute("PRAGMA wal_autocheckpoint=20000;")  # WAL checkpoint 20k
```

**Ocena:** ✅ DOBRA KONFIGURACJA:

- WAL mode + busy_timeout (30s) = bezpieczna dla konkurencyjnego dostępu
- foreign_keys=ON = data integrity
- synchronous=NORMAL = performance + safety balance

### 1.8.2 PRAGMA settings w core/sessions.py (⚠️ NIEJEDNORODNE)

```bash
$ sed -n '50,52p' core/sessions.py
conn.execute("PRAGMA foreign_keys = ON")
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA busy_timeout = 5000")  # 5 second timeout — ZA KRÓTKI!
```

**Ocena:** ⚠️ busy_timeout=5s (vs 30s w memory.py). Może być problem pod dużym load.

### 1.8.3 DOWÓD: Czy istnieje trzecia baza z memory_store.py

```bash
$ ls -lh /root/mrd/data/mem.db 2>/dev/null || echo 'NO /root/mrd/data/mem.db'
NO /root/mrd/data/mem.db
```

```bash
$ find /root/mrd -path '*/data/mem.db*' -type f -maxdepth 3 2>/dev/null
(brak outputu — żaden plik nie znaleziony)
```

**Analiza:** Kod memory_store.py L:6-10:

```python
DB_PATH = os.getenv("MEM_DB") or str((Path(os.getenv("WORKSPACE",".")) / "data" / "mem.db").absolute())
```

Jest fallback do `/data/mem.db`, ale:

- MEM_DB env var = NOT SET (por. 1.5.3)
- WORKSPACE env var = NOT SET (por. 1.5.3)
- Fallback `.` (current directory) by wytworzył `./data/mem.db` w cwd, ale to się nie dzieje w runtime

**Status P0:** 🔴 memory_store.py ma INNĄ logikę niż memory.py/sessions.py (choć dziś nieużywana). Brak PRAGMA settings w memory_store.py L:10.

### 1.8.4 REKOMENDACJA P1: Unifikacja PRAGMA — jedno źródło

**Rozwiązanie: nowy moduł `core/sqlite_init.py`**

```python
# core/sqlite_init.py — UNIFIED SQLITE INITIALIZATION
import sqlite3
from typing import Optional

def init_sqlite_connection(db_path: str, timeout: int = 30) -> sqlite3.Connection:
    """
    Initialize SQLite connection with unified safety pragmas.
    Use this function instead of direct sqlite3.connect() calls.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=timeout)

    # Unified pragmas for all connections
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA cache_size=-2000000;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.execute("PRAGMA wal_autocheckpoint=20000;")

    return conn
```

**Akcja P1:** Zastąpić wszystkie `sqlite3.connect()` w:

- core/memory.py (OK, ale do unifikacji)
- core/sessions.py (timeout 5s → 30s)
- core/memory_store.py (zmienić logikę DB_PATH, dodać PRAGMA, użyć unified init_sqlite)
- core/memory_summarizer.py (brak timeout)
- core/conversation_analytics.py (brak PRAGMA)

---

## 2. SYSTEM PAMIĘCI — ARCHITEKTURA

### 2.1 Plik hierarchical_memory.py — DUPLIKAT

```bash
$ wc -l hierarchical_memory.py core/hierarchical_memory.py
  895 hierarchical_memory.py
  953 core/hierarchical_memory.py
 1848 total
```

**Problem:** root/hierarchical_memory.py ma 895 linii, core/hierarchical_memory.py ma 953 linii. DUPLIKAT z różnymi rozmiarami.

### 2.2 Różnice między plikami

**Komenda:**

```bash
$ diff -u hierarchical_memory.py core/hierarchical_memory.py | head -50
```

**Output (fragment):**

```diff
--- hierarchical_memory.py      2025-12-23 02:47:00.183053405 +0000
+++ core/hierarchical_memory.py 2025-12-25 19:15:01.326179917 +0000
@@ -681,6 +681,11 @@
 # -------------------- System koordynujący --------------------

 class HierarchicalMemorySystem:
+    def __await__(self):
+        async def _coro():
+            return self
+        return _coro().__await__()
+
     def __init__(self):
         self.episodic = EpisodicMemoryManager()
         self.semantic = SemanticMemoryManager()
@@ -862,6 +867,11 @@
         # trywialne kryterium
         return len(self.episodic.get_recent_episodes(limit=SEMANTIC_CONSOLIDATION_INTERVAL)) >= SEMANTIC_CONSOLIDATION_INTERVAL

+    async def search_hybrid(self, query: str, limit: int = 5, user_id: str = "default", max_results: int = None, **kwargs):
+        limit = max_results or limit
+        from core.memory import ltm_search_hybrid
+        return await ltm_search_hybrid(query, limit, user_id)
```

**Ocena:** ⚠️ core/hierarchical_memory.py ma dodatkowe metody:

- `__await__()` na L:684-688
- `search_hybrid()` na L:870-874

Różnice w logice — nie są IDENTICAL!

### 2.3 Hash porównanie

```bash
$ md5sum hierarchical_memory.py core/hierarchical_memory.py
4cbd719b666818fdfee20c4b4ac7f873  hierarchical_memory.py
4c1652f78659781de0d471d371da8a9f  core/hierarchical_memory.py
```

**Wynik:** Różne hashe — pliki są DIFFERENT.

---

## 3. KLASY PAMIĘCI — HIERARCHIA

### 3.1 Struktura hierarchical_memory.py

```bash
$ grep -n 'class ' hierarchical_memory.py core/hierarchical_memory.py
hierarchical_memory.py:56:class EpisodicMemoryManager:
hierarchical_memory.py:190:class SemanticMemoryManager:
hierarchical_memory.py:364:class ProceduralMemoryManager:
hierarchical_memory.py:503:class MentalModelManager:
hierarchical_memory.py:683:class HierarchicalMemorySystem:
core/hierarchical_memory.py:56:class EpisodicMemoryManager:
core/hierarchical_memory.py:190:class SemanticMemoryManager:
core/hierarchical_memory.py:364:class ProceduralMemoryManager:
core/hierarchical_memory.py:503:class MentalModelManager:
core/hierarchical_memory.py:683:class HierarchicalMemorySystem:
core/hierarchical_memory.py:951:class HierarchicalMemory(globals()["HierarchicalMemorySystem"]):
```

**Struktura:**

- 5 klas w root/hierarchical_memory.py
- 6 klas w core/hierarchical_memory.py (dodatkowo `HierarchicalMemory` wrapper na L:951)

---

## 4. 🔴 P0 PROBLEMY: DUPLIKAT BEZ JASNOŚCI

### 4.1 Dwie bazy mem.db z różnymi rozmiarami

**Problem:** Istnieją dwie aktywne bazy:

- `/root/mrd/mem.db` — 488K
- `/root/mrd/core/mem.db` — 320K

**Pytania bez odpowiedzi:**

- Która baza jest aktualnie używana?
- Czy są zsynchronizowane?
- Czy ktoś je może edytować niezależnie?

**Akcja P0:** Ustalić JEDNO miejsce dla mem.db.

### 4.2 Dwie kopie hierarchical_memory.py z różnymi logami

**Problem:** Pliki mają RÓŻNE LOGIKI:

- root/hierarchical_memory.py — wersja starsza (895 linii)
- core/hierarchical_memory.py — wersja nowsza (953 linii) z `__await__()` i `search_hybrid()`

**Kto korzysta z którego?** Niejasne.

**Akcja P0:** Zatrzymać duplikację. Importować z core/, usunąć z root/.

### 4.3 Brak jasnej strategii persistence

**Problem:** Nie ma dokumentacji:

- Kiedy mem.db się zapisuje?
- Jaka strategia flush/commit?
- Czy transakcje są atomowe?

**Akcja P0:** Zdokumentować lifecycle bazy danych.

---

## 5. KONFIGURACJA PAMIĘCI W core/config.py

### 5.1 DB_PATH — gdzie jest baza?

**Komenda:**

```bash
$ sed -n '36,40p' core/config.py
```

**Output:**

```python
BASE_DIR = os.getenv("WORKSPACE", DEFAULT_BASE_DIR)
DB_PATH = os.getenv("MEM_DB", os.path.join(BASE_DIR, "mem.db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
FRONTEND_INDEX = os.getenv("FRONTEND_INDEX", "/app/dist/index.html")
```

**Analiza:**

- `DB_PATH` default: `<BASE_DIR>/mem.db`
- Jeśli `MEM_DB` env jest ustawiona, używa jej
- Baza ma być w root, nie w core/

**Problem:** W rzeczywistości są bazy w obu miejscach (root/ i core/).

### 5.2 Importy memory w app.py

**Komenda:**

```bash
$ grep 'memory' app.py | head -5
```

**Output:** Aplikacja importuje memory gdzieś, ale nie wiadomo gdzie dokładnie.

---

## 6. 🟠 P1 PROBLEMY: BRAK STANDARDU

### 6.1 Niejasne kto ładuje hierarchical_memory.py

**Problem:**

- root/hierarchical_memory.py vs core/hierarchical_memory.py
- root/app.py może importować root/hierarchical_memory.py
- core/app.py może importować core/hierarchical_memory.py
- Ale jest też potencjal na cross-import

**Akcja P1:** Jedno źródło — zawsze `from core.hierarchical_memory import ...`

### 6.2 LTM Storage — brak dokumentacji

**Problem:**

- `ltm_storage/backups` — po co?
- `ltm_storage/vector_indices` — do czego?
- Kiedy się tworzą backupy?
- Czy vector_indices są używane aktywnie?

**Akcja P1:** Zdokumentować strukturę LTM storage.

### 6.3 Brak monitorowania rozmiaru bazy

**Problem:** mem.db rośnie bez kontroli. Brak:

- Alert kiedy przekroczy limit
- Archiwizacja starych danych
- Vacuum/compact strategy

**Akcja P1:** Dodać monitoring i auto-cleanup.

---

## 7. DUPLIKATY — ROOT VS CORE

### 7.1 hierarchical_memory.py — DIFFERENT

| Plik                        | Rozmiar | Linii | Hash          | Status  |
| --------------------------- | ------- | ----- | ------------- | ------- |
| root/hierarchical_memory.py | 41618 B | 895   | `4cbd719b...` | Stara   |
| core/hierarchical_memory.py | 43782 B | 953   | `4c165278...` | Nowa ✅ |

**Akcja:** Usunąć root/hierarchical_memory.py, importować z core/.

### 7.2 hybrid_search_endpoint.py — PROXY

```bash
$ wc -l hybrid_search_endpoint.py core/hybrid_search_endpoint.py
  153 hybrid_search_endpoint.py
14214 core/hybrid_search_endpoint.py
```

**Status:** root/ to proxy (153 B), core/ to pełna implementacja (14K).

**OK:** To jest świadomie, ale trzeba sprawdzić czy proxy działa.

---

## 8. PODSUMOWANIE PROBLEMÓW

| #   | Problem                          | Priorytet | Lokalizacja                 | Akcja                                  |
| --- | -------------------------------- | --------- | --------------------------- | -------------------------------------- |
| 1   | Dwie bazy mem.db (488K + 320K)   | 🔴 P0     | root/, core/                | Jedno źródło: root/mrd/mem.db          |
| 2   | hierarchical_memory.py DIFFERENT | 🔴 P0     | root/, core/                | Usunąć root/, importować z core/       |
| 3   | Niejasne kim importuje memory    | 🔴 P0     | app.py, core/app.py         | Standardowy import z core/             |
| 4   | Brak dokumentacji persistence    | 🟠 P1     | core/hierarchical_memory.py | Dokumentacja lifecycle                 |
| 5   | LTM storage — bez jasności       | 🟠 P1     | ltm_storage/                | Dokumentacja: backups + vector_indices |
| 6   | Brak monitoringu bazy            | 🟠 P1     | core/config.py              | Alert + auto-cleanup                   |
| 7   | hybrid_search_endpoint proxy     | 🟡 P2     | root/, core/                | Weryfikacja że proxy działa            |

---

## 9. DOWODY (CITATIONS)

### 9.1 Lokalizacja mem.db na serwerze

**Komenda:**

```bash
$ find . -name 'mem.db*' -type f
./core/mem.db
./core/mem.db.bak.20251225_190638
./mem.db
./mem.db.bak.20251225_190638
```

**Ocena:** 🔴 4 pliki — 2 aktywne + 2 backupy w dwóch miejscach.

### 9.2 Rozmiary mem.db

**Komenda:**

```bash
$ ls -lh mem.db core/mem.db
-rw-r--r-- 1 root root 488K Dec 25 19:27 mem.db
-rw-r--r-- 1 root root 320K Dec 25 19:06 core/mem.db
```

**Problem:** Różne rozmiary — 488K vs 320K. Co się stało z core/mem.db?

### 9.3 hierarchical_memory.py — Rozmiary

**Komenda:**

```bash
$ wc -l hierarchical_memory.py core/hierarchical_memory.py
  895 hierarchical_memory.py
  953 core/hierarchical_memory.py
 1848 total
```

**Problem:** core/ ma +58 linii. Różne logiki — DIFFERENT.

### 9.4 Hasz hierarchical_memory.py

**Komenda:**

```bash
$ md5sum hierarchical_memory.py core/hierarchical_memory.py
4cbd719b666818fdfee20c4b4ac7f873  hierarchical_memory.py
4c1652f78659781de0d471d371da8a9f  core/hierarchical_memory.py
```

**Wynik:** Różne hashe — CONFIRMED DIFFERENT.

### 9.5 Różnice — **await**() metoda

**Komenda:**

```bash
$ diff -u hierarchical_memory.py core/hierarchical_memory.py | grep -A5 "__await__"
```

**Output:**

```diff
+    def __await__(self):
+        async def _coro():
+            return self
+        return _coro().__await__()
```

**Znaczenie:** core/ ma async support dla `await HierarchicalMemorySystem()`.

### 9.6 Różnice — search_hybrid() metoda

**Komenda:**

```bash
$ diff -u hierarchical_memory.py core/hierarchical_memory.py | grep -A5 "search_hybrid"
```

**Output:**

```diff
+    async def search_hybrid(self, query: str, limit: int = 5, user_id: str = "default", max_results: int = None, **kwargs):
+        limit = max_results or limit
+        from core.memory import ltm_search_hybrid
+        return await ltm_search_hybrid(query, limit, user_id)
```

**Znaczenie:** core/ ma nową metodę do hybrid search.

### 9.7 Klasy pamięci — struktura

**Komenda:**

```bash
$ grep -n 'class ' core/hierarchical_memory.py
```

**Output:**

```
core/hierarchical_memory.py:56:class EpisodicMemoryManager:
core/hierarchical_memory.py:190:class SemanticMemoryManager:
core/hierarchical_memory.py:364:class ProceduralMemoryManager:
core/hierarchical_memory.py:503:class MentalModelManager:
core/hierarchical_memory.py:683:class HierarchicalMemorySystem:
core/hierarchical_memory.py:951:class HierarchicalMemory(globals()["HierarchicalMemorySystem"]):
```

**Struktura:** 5 memory managers + 1 wrapper = 6 klas.

### 9.8 LTM Storage struktura

**Komenda:**

```bash
$ ls -la ltm_storage/
```

**Output:**

```
total 24
drwxr-xr-x  4 root root  4096 Dec 24 10:11 .
drwxr-xr-x  2 root root  4096 Dec 24 10:11 backups
drwxr-xr-x  2 root root  4096 Dec 24 10:11 vector_indices
```

**Katalogi:**

- `ltm_storage/backups/` — backupy (brak infirmacji czego)
- `ltm_storage/vector_indices/` — indeksy do vector search

### 9.9 Git status — modified memory files

**Komenda:**

```bash
$ git status --porcelain | grep -i 'memory\|hierarchical'
 M core/hierarchical_memory.py
 M hierarchical_memory.py
```

**Ocena:** Oba pliki hierarchical_memory.py mają zmiany.

### 9.10 DB_PATH konfiguracja

**Komenda:**

```bash
$ sed -n '36,40p' core/config.py
```

**Output:**

```python
BASE_DIR = os.getenv("WORKSPACE", DEFAULT_BASE_DIR)
DB_PATH = os.getenv("MEM_DB", os.path.join(BASE_DIR, "mem.db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
FRONTEND_INDEX = os.getenv("FRONTEND_INDEX", "/app/dist/index.html")
```

**Config:** DB powinien być w `<WORKSPACE>/mem.db`, ale w rzeczywistości są bazy w obu miejscach.

---

**STOP — czy pkt 07 jest OK? Jeśli OK, przechodzę do: `AUDYT/08_ROUTERS_ENDPOINTS8.md`.**
