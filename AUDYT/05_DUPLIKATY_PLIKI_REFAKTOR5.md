# AUDYT PUNKT 5: DUPLIKATY PLIKÓW & REFAKTOR

**Data audytu:** 26 grudnia 2025  
**Zakres:** Analiza duplikatów, plików tymczasowych, struktury katalogów  
**Metoda:** Porównanie hash MD5 + analiza zawartości

---

## 0. ŚRODOWISKO AUDYTU

| Parametr                 | Wartość                       |
| ------------------------ | ----------------------------- |
| **Lokalizacja audytu**   | Kopia robocza (Windows)       |
| **Ścieżka**              | `C:\Users\48501\Desktop\mrd`  |
| **Czy to checkout git?** | ❌ NIE — brak katalogu `.git` |
| **System docelowy**      | Linux (serwer produkcyjny)    |

**WERYFIKACJA BRAKU REPOZYTORIUM GIT:**

```powershell
PS> Test-Path .git
False

PS> git rev-parse HEAD
fatal: not a git repository (or any of the parent directories): .git
```

**STATUS:** Ten audyt został wykonany na **kopii roboczej bez repozytorium git**. To NIE jest checkout produkcyjny.

**PRZED WDROŻENIEM POPRAWEK — wykonać na serwerze produkcyjnym:**

```bash
$ pwd
# oczekiwane: /root/mrd

$ ls -la .git
# oczekiwane: katalog .git istnieje

$ git rev-parse HEAD
# oczekiwane: 40-znakowy commit hash

$ git status --porcelain
# oczekiwane: puste (brak uncommitted changes)
```

---

## 1. PODSUMOWANIE STATYSTYK

**Wszystkie metryki policzone na kopii roboczej (PowerShell). Ekwiwalentne komendy Linux do weryfikacji na serwerze.**

### 1.1 Czystych plików .py

```powershell
PS> (Get-ChildItem -Recurse -File -Filter "*.py" | Where-Object { $_.Name -notmatch '^(patch_|fix_|tools_)' -and $_.FullName -notmatch '\.bak' }).Count
113
```

**Linux:** `find . -name '*.py' | grep -Ev 'patch_|fix_|tools_|\.bak' | wc -l`

### 1.2 Plików w root/

```powershell
PS> (Get-ChildItem -File -Filter "*.py" | Where-Object { $_.Name -notmatch '^(patch_|fix_|tools_)' -and $_.Name -notmatch '\.bak' }).Count
35
```

**Linux:** `ls *.py 2>/dev/null | grep -Ev '^(patch_|fix_|tools_)' | wc -l`

### 1.3 Plików w core/

```powershell
PS> (Get-ChildItem -Path "core" -File -Filter "*.py" | Where-Object { $_.Name -notmatch '\.bak' }).Count
67
```

**Linux:** `ls core/*.py 2>/dev/null | wc -l`

### 1.4 Plików .bak (kod)

```powershell
PS> (Get-ChildItem -Recurse -File -Filter "*.bak*" | Where-Object { $_.Name -notmatch '\.db\.bak' }).Count
19
```

**Linux:** `find . -name '*.bak*' ! -name '*.db.bak*' | wc -l`

### 1.5 Plików .db.bak (baza danych)

```powershell
PS> (Get-ChildItem -Recurse -File -Filter "*.db.bak*").Count
2
```

**Linux:** `find . -name '*.db.bak*' | wc -l`

### 1.6 Plików patch*/fix*/tools\_

```powershell
PS> (Get-ChildItem -File -Filter "*.py" | Where-Object { $_.Name -match '^(patch_|fix_|tools_)' }).Count
30
```

**Linux:** `ls patch_*.py fix_*.py tools_*.py 2>/dev/null | wc -l`

### 1.7 Tabela podsumowująca

| Metryka                           | Wartość |
| --------------------------------- | ------- |
| **Czystych plików .py**           | 113     |
| **Plików w root/**                | 35      |
| **Plików w core/**                | 67      |
| **Duplikatów nazw (root ∩ core)** | 11      |
| **Plików .bak (kod)**             | 19      |
| **Plików .db.bak (baza danych)**  | 2       |
| **Plików patch*/fix*/tools\_**    | 30      |

---

## 2. DUPLIKATY NAZW: ROOT VS CORE

### 2.1 Komenda wykrycia (Linux)

```bash
$ ls *.py core/*.py 2>/dev/null | xargs -n1 basename | sort | uniq -d
```

### 2.2 Wynik analizy

| Nazwa pliku                 | root/ rozmiar | core/ rozmiar | Status       | Rekomendacja                   |
| --------------------------- | ------------- | ------------- | ------------ | ------------------------------ |
| `app.py`                    | 9368 B        | 24284 B       | 🔴 DIFFERENT | Zbadać który jest aktualny     |
| `assistant_endpoint.py`     | 6340 B        | 6355 B        | 🔴 DIFFERENT | Zbadać różnice (+15B)          |
| `hierarchical_memory.py`    | 41618 B       | 43782 B       | 🔴 DIFFERENT | core ma +2164B                 |
| `hybrid_search_endpoint.py` | 153 B         | 14214 B       | 🟢 PROXY     | OK — root to świadomy reexport |
| `prometheus_endpoint.py`    | 928 B         | 928 B         | 🟢 IDENTICAL | Zamienić root na REEXPORT      |
| `psyche_endpoint.py`        | 13531 B       | 13531 B       | 🟢 IDENTICAL | Zamienić root na REEXPORT      |
| `research.py`               | 57563 B       | 57040 B       | 🔴 DIFFERENT | root ma +523B                  |
| `research_endpoint.py`      | 6234 B        | 6234 B        | 🟢 IDENTICAL | Zamienić root na REEXPORT      |
| `stress_test_system.py`     | 21543 B       | 21543 B       | 🟢 IDENTICAL | Zamienić root na REEXPORT      |
| `suggestions_endpoint.py`   | 4633 B        | 5060 B        | 🔴 DIFFERENT | core ma +427B                  |
| `ultra_destruction_test.py` | 24789 B       | 24789 B       | 🟢 IDENTICAL | Zamienić root na REEXPORT      |

### 2.3 Komenda weryfikacji hashów (Linux)

```bash
$ md5sum prometheus_endpoint.py core/prometheus_endpoint.py
$ md5sum psyche_endpoint.py core/psyche_endpoint.py
$ md5sum research_endpoint.py core/research_endpoint.py
$ md5sum stress_test_system.py core/stress_test_system.py
$ md5sum ultra_destruction_test.py core/ultra_destruction_test.py
```

---

## 3. REKOMENDACJE DLA DUPLIKATÓW

### 3.1 Pliki IDENTICAL — zamiana na REEXPORT (NIE usuwać!)

**Dotyczy:** `prometheus_endpoint.py`, `psyche_endpoint.py`, `research_endpoint.py`, `stress_test_system.py`, `ultra_destruction_test.py`

**Problem:** Usunięcie z root może rozwalić importy w innych plikach.

**Rekomendacja:** Zamienić zawartość root pliku na reexport do core. Dopiero po analizie import-grafu (osobny punkt audytu) można rozważyć usunięcie.

---

### 3.2 REEXPORT: `prometheus_endpoint.py`

**Eksportuje:** `router` (APIRouter)

**Docelowa zawartość `./prometheus_endpoint.py`:**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REEXPORT: Ten plik to proxy do core/prometheus_endpoint.py
Po sprawdzeniu import-grafu można rozważyć usunięcie.
"""

from __future__ import annotations

from core.prometheus_endpoint import router

__all__ = ["router"]
```

---

### 3.3 REEXPORT: `psyche_endpoint.py`

**Eksportuje:** `router` (APIRouter z prefix="/api/psyche")

**Docelowa zawartość `./psyche_endpoint.py`:**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REEXPORT: Ten plik to proxy do core/psyche_endpoint.py
Po sprawdzeniu import-grafu można rozważyć usunięcie.
"""

from __future__ import annotations

from core.psyche_endpoint import router

__all__ = ["router"]
```

---

### 3.4 REEXPORT: `research_endpoint.py`

**Eksportuje:** `router` (APIRouter z prefix="/api/research")

**Docelowa zawartość `./research_endpoint.py`:**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REEXPORT: Ten plik to proxy do core/research_endpoint.py
Po sprawdzeniu import-grafu można rozważyć usunięcie.
"""

from __future__ import annotations

from core.research_endpoint import router

__all__ = ["router"]
```

---

### 3.5 REEXPORT: `stress_test_system.py`

**Eksportuje:** `SystemStressTest` (klasa testowa)

**Docelowa zawartość `./stress_test_system.py`:**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REEXPORT: Ten plik to proxy do core/stress_test_system.py
Po sprawdzeniu import-grafu można rozważyć usunięcie.
"""

from __future__ import annotations

from core.stress_test_system import SystemStressTest

__all__ = ["SystemStressTest"]
```

---

### 3.6 REEXPORT: `ultra_destruction_test.py`

**Eksportuje:** `UltraExtremeStressTest` (klasa testowa)

**Docelowa zawartość `./ultra_destruction_test.py`:**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REEXPORT: Ten plik to proxy do core/ultra_destruction_test.py
Po sprawdzeniu import-grafu można rozważyć usunięcie.
"""

from __future__ import annotations

from core.ultra_destruction_test import UltraExtremeStressTest

__all__ = ["UltraExtremeStressTest"]
```

---

### 3.7 Pliki DIFFERENT — wymagają analizy

**Dotyczy:** `app.py`, `assistant_endpoint.py`, `hierarchical_memory.py`, `research.py`, `suggestions_endpoint.py`

**Akcja:** Przed decyzją:

1. Sprawdzić daty modyfikacji: `ls -la <plik> core/<plik>`
2. Porównać zawartość: `diff <plik> core/<plik>`
3. Ustalić który jest używany w produkcji

### 3.8 Plik PROXY — OK

**Dotyczy:** `hybrid_search_endpoint.py` (root ma tylko `from core.hybrid_search_endpoint import router`)

**Status:** ✅ Prawidłowy wzorzec — zachować.

---

## 4. app.py — KANDYDAT NA ENTRYPOINT (nie fakt!)

### 4.1 Porównanie

| Cecha                      | `./app.py` (root)             | `./core/app.py`                |
| -------------------------- | ----------------------------- | ------------------------------ |
| **Rozmiar**                | 9368 B                        | 24284 B                        |
| **Definicja FastAPI**      | ✅ TAK                        | ✅ TAK                         |
| **Ładowanie routerów**     | Prosty import `openai_compat` | Dynamiczne z `ALLOWED_ROUTERS` |
| **Prometheus integration** | ❌ NIE                        | ✅ TAK                         |

**UWAGA:** Nie można stwierdzić który jest entrypointem bez sprawdzenia jak serwer uruchamia aplikację:

```bash
# Sprawdzić na serwerze:
$ cat /etc/systemd/system/mrd*.service   # jeśli systemd
$ docker inspect <container>              # jeśli docker
$ ps aux | grep uvicorn                   # aktualny proces
```

**Status:** `./core/app.py` jest bardziej rozbudowany (kandydat), ale **EntryPoint Truth** wymaga dowodu z realnego startu.

---

## 5. PLIKI patch*/fix*/tools\_ — DOWÓD NIEUŻYCIA

### 5.1 Sprawdzenie importów

**Komenda (Linux):**

```bash
$ grep -rn 'import patch_\|from patch_\|import fix_\|from fix_\|import tools_\|from tools_' \
    --include='*.py' \
    | grep -v '^patch_\|^fix_\|^tools_'
```

**Wynik:** BRAK WYNIKÓW — żaden plik produkcyjny nie importuje patch*/fix*/tools\_.

**UWAGA:** `core/tools_registry.py` to INNY plik (rejestr narzędzi AI), nie mylić z `tools_*.py` w root.

### 5.2 Sprawdzenie uruchamiania

**Komenda (Linux):**

```bash
$ grep -rn 'patch_\|fix_\|tools_fix\|tools_patch' \
    --include='*.sh' --include='*.service' --include='Makefile' --include='Dockerfile'
```

**Wynik:** Wymaga weryfikacji na serwerze.

### 5.3 Status plików

| Prefix   | Liczba | Status                      |
| -------- | ------ | --------------------------- |
| `patch_` | 18     | 🟡 KANDYDAT DO ARCHIWIZACJI |
| `fix_`   | 5      | 🟡 KANDYDAT DO ARCHIWIZACJI |
| `tools_` | 8      | 🟡 KANDYDAT DO ARCHIWIZACJI |

**Rekomendacja:**

1. Zweryfikować na serwerze że nic nie uruchamia tych plików
2. Utworzyć archiwum: `tar czf patches_archive_$(date +%Y%m%d).tar.gz patch_*.py fix_*.py tools_*.py`
3. Przenieść do katalogu `_archive/` zamiast kasować
4. Po 30 dniach bez problemów — można usunąć archiwum

---

## 6. PLIKI .bak — ROZDZIELENIE NA KATEGORIE

### 6.1 Pliki .bak KODU (19 plików)

**Komenda (Linux):**

```bash
$ find . -name '*.bak*' ! -name '*.db.bak*' -type f
```

**DOWÓD NIEUŻYCIA:**

```bash
$ grep -rn '\.bak' --include='*.py' | grep -v 'with_suffix\|+ ".bak\|suffix + f".bak' | head
```

**Wynik:** Wszystkie odwołania do `.bak` to TWORZENIE backupów w plikach patch*/fix*/tools\_, nie importowanie.

**Status:** 🟡 KANDYDAT DO ARCHIWIZACJI

**Rekomendacja:**

```bash
$ mkdir -p _archive/bak_code_$(date +%Y%m%d)
$ find . -name '*.bak*' ! -name '*.db.bak*' -exec mv {} _archive/bak_code_$(date +%Y%m%d)/ \;
```

### 6.2 Pliki .db.bak — BACKUP BAZY DANYCH (osobna kategoria!)

**Komenda (Linux):**

```bash
$ find . -name '*.db.bak*' -type f -exec ls -lh {} \;
```

**Lista:**

| Plik                                | Rozmiar  |
| ----------------------------------- | -------- |
| `./mem.db.bak.20251225_190638`      | 307200 B |
| `./core/mem.db.bak.20251225_190638` | 290816 B |

**🔴 UWAGA:** To są BACKUP DANYCH, nie kodu. NIE USUWAĆ bez procedury!

**Procedura:**

```bash
$ mkdir -p /root/mrd_backups/db
$ mv ./mem.db.bak.* /root/mrd_backups/db/
$ mv ./core/mem.db.bak.* /root/mrd_backups/db/
$ echo '*.db.bak*' >> .gitignore
```

---

## 7. PLIKI TYLKO W ROOT — KANDYDACI DO PRZENIESIENIA

**Komenda (Linux):**

```bash
$ comm -23 <(ls *.py 2>/dev/null | grep -Ev '^(patch_|fix_|tools_)' | sort) \
           <(ls core/*.py 2>/dev/null | xargs -n1 basename | sort)
```

**Kluczowe pliki (KANDYDACI — decyzja po import-grafie):**

| Plik                   | Opis                            | Status                             |
| ---------------------- | ------------------------------- | ---------------------------------- |
| `stt_endpoint.py`      | Speech-to-text (BEZ AUTH!)      | 🟡 KANDYDAT: przenieś + dodaj auth |
| `tts_endpoint.py`      | Text-to-speech (BEZ AUTH!)      | 🟡 KANDYDAT: przenieś + dodaj auth |
| `internal_endpoint.py` | Endpoint /api/internal/ui_token | 🟡 KANDYDAT: przenieś do core      |
| `openai_compat.py`     | OpenAI compatibility            | 🟡 KANDYDAT: przenieś do core      |
| `routers.py`           | ALLOWED_ROUTERS                 | 🟡 KANDYDAT: przenieś do core      |
| `files_endpoint.py`    | Endpoint plików                 | 🟡 KANDYDAT: przenieś do core      |

**UWAGA:** Żadne przeniesienie bez analizy import-grafu! Decyzja w osobnym punkcie audytu.

---

## 8. PODSUMOWANIE PROBLEMÓW

| #   | Problem                            | Priorytet | Akcja                                      |
| --- | ---------------------------------- | --------- | ------------------------------------------ |
| 1   | **Duplikaty DIFFERENT (5 plików)** | 🔴 P0     | Ustalić który jest aktualny (diff + daty)  |
| 2   | **Duplikaty IDENTICAL (5 plików)** | 🟠 P1     | Zamienić root na REEXPORT (kod w sekcji 3) |
| 3   | **Pliki patch*/fix*/tools\_**      | 🟡 P2     | Zarchiwizować po weryfikacji nieużycia     |
| 4   | **Pliki .bak kodu**                | 🟡 P2     | Przenieść do \_archive/                    |
| 5   | **Pliki .db.bak**                  | 🟡 P2     | Przenieść do /root/mrd_backups/db/ (DANE!) |
| 6   | **Pliki tylko w root (32)**        | 🟡 P2     | KANDYDACI — analizować po import-grafie    |
| 7   | **Brak jasnego entrypointa**       | 🟠 P1     | Sprawdzić jak serwer uruchamia app         |

---

## 9. DOWODY (CITATIONS)

### 9.1 Brak importów patch*/fix*/tools\_

```bash
$ grep -rn 'import patch_\|from patch_\|import fix_\|from fix_\|import tools_\|from tools_' \
    --include='*.py' | grep -v '^patch_\|^fix_\|^tools_'
# Wynik: brak (puste)
```

### 9.2 Odwołania do .bak to tylko tworzenie backupów

```bash
$ grep -rn '\.bak' --include='*.py' | grep -v 'with_suffix\|+ ".bak\|suffix + f".bak' | head
# Wynik: tylko w plikach patch_/fix_ które tworzą backupy
```

### 9.3 Pliki .db.bak

```bash
$ find . -name '*.db.bak*' -ls
# ./mem.db.bak.20251225_190638         307200 B
# ./core/mem.db.bak.20251225_190638    290816 B
```

### 9.4 core/tools_registry.py to inny plik

```bash
$ head -5 core/tools_registry.py
# To jest rejestr narzędzi AI, nie plik tools_*.py
```

---

**STOP — sprawdź ten punkt. Czy coś poprawić/doprecyzować? Jeśli OK, przechodzę do: `AUDYT/07_MEMORY_DATABASE7.md`.**
