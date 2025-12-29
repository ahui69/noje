# AUDYT MRD - CZĘŚĆ 2: WYKRYCIE MIXU ROUTERÓW / FRAMEWORKÓW + PLAN UNIFIKACJI

## 2.1 WYKRYTE WZORCE ROUTINGU

### A) FastAPI + APIRouter (STANDARD) ✅

**Wzorzec:** `from fastapi import APIRouter; router = APIRouter(prefix="...", tags=["..."])`

**Pliki używające:**
- `assistant_simple.py:203` - `router = APIRouter(prefix="/api/chat", tags=["chat"])`
- `stt_endpoint.py:15` - `router = APIRouter(prefix="/api/stt", tags=["speech"])`
- `tts_endpoint.py:17` - `router = APIRouter(prefix="/api/tts", tags=["tts"])`
- `suggestions_endpoint.py:40` - `router = APIRouter(prefix="/api/suggestions", tags=["Proactive Suggestions"])`
- `internal_endpoint.py:11` - `router = APIRouter(prefix="/api/internal")`
- `files_endpoint.py:15` - `router = APIRouter(prefix="/api/files")`
- `routers.py:28` - `router = APIRouter(prefix="/api/routers", tags=["routers"])`
- `openai_compat.py:15` - `router = APIRouter(prefix="/v1", tags=["openai_compat"])`
- `nlp_endpoint.py:23` - `router = APIRouter(prefix="/api/nlp", tags=["nlp"])`
- `research_endpoint.py:15` - `router = APIRouter(prefix="/api/research", tags=["research"])`
- `prometheus_endpoint.py:12` - `router = APIRouter()` (bez prefixu!)
- `psyche_endpoint.py:26` - `router = APIRouter(prefix="/api/psyche")`
- `writing_endpoint.py:26` - `router = APIRouter(prefix="/api/writing")`
- `programista_endpoint.py:17` - `router = APIRouter(prefix="/api/code")`
- `travel_endpoint.py:18` - `router = APIRouter(prefix="/api/travel")`
- `core/assistant_endpoint.py:40` - `router = APIRouter(prefix="/api/chat")` ⚠️ DUPLIKAT!
- `core/memory_endpoint.py:9` - `router = APIRouter(prefix="/api/memory", tags=["memory"])`
- `core/cognitive_endpoint.py:14` - `router = APIRouter(prefix="/api/cognitive", tags=["cognitive"])`
- `core/negocjator_endpoint.py:26` - `router = APIRouter(prefix="/api/negocjator", tags=["AI Negocjator"])`
- `core/reflection_endpoint.py:21` - `router = APIRouter(prefix="/api/reflection", tags=["Self-Reflection"])`
- `core/legal_office_endpoint.py:49` - `router = APIRouter(prefix="/api/legal", tags=["Legal Office"])`
- `core/hybrid_search_endpoint.py:20` - `router = APIRouter(prefix="/api/search", tags=["search"])`
- `core/batch_endpoint.py:45` - `router = APIRouter(prefix="/api/batch", tags=["batch"])`
- `core/prometheus_endpoint.py:12` - `router = APIRouter()` (bez prefixu!)
- `core/admin_endpoint.py:24` - `router = APIRouter(prefix="/api/admin")`
- `core/research_endpoint.py:15` - `router = APIRouter(prefix="/api/research", tags=["research"])` ⚠️ DUPLIKAT!
- `core/psyche_endpoint.py:26` - `router = APIRouter(prefix="/api/psyche")` ⚠️ DUPLIKAT!
- `core/suggestions_endpoint.py:23` - `router = APIRouter(prefix="/api/suggestions", tags=["Proactive Suggestions"])` ⚠️ DUPLIKAT!
- `core/hacker_endpoint.py:26` - `router = APIRouter(prefix="/api/hacker", tags=["AI Hacker Assistant"])`
- `core/auction_endpoint.py:17` - `router = APIRouter(prefix="/api/auction", tags=["AI Auction"])`
- `core/chat_advanced_endpoint.py:28` - `router = APIRouter(prefix="/core/chat/advanced", tags=["core-chat-advanced"])` ⚠️ NIESTANDARDOWY PREFIX!

**Status:** ✅ STANDARD (używany wszędzie)

---

### B) Ręczne mapowanie ścieżek (app.add_api_route) ⚠️

**Wzorzec:** `app.add_api_route(path, endpoint, methods=[...])`

**Pliki używające:**
- `app.py:246` - `app.add_api_route()` w funkcji `_mrd__auto_alias_double_api_prefix()` (tworzy aliasy dla `/api/api/...`)

**Status:** ⚠️ UŻYWANE TYLKO DO ALIASÓW (nie do głównych endpointów)

---

### C) Dynamiczne importy routerów (try/except) ⚠️

**Wzorzec:** `importlib.import_module()` + `getattr(module, "router")` + `app.include_router()`

**Pliki używające:**
- `app.py:82-161` - `_try_import_router()` i `_include()` z try/except

**Status:** ⚠️ UŻYWANE DO ŁADOWANIA ROUTERÓW Z OBSŁUGĄ BŁĘDÓW

---

### D) Brak innych frameworków ✅

**Sprawdzone:**
- ❌ Brak Flask/Blueprint
- ❌ Brak Starlette routes (poza FastAPI)
- ❌ Brak własnych routerów (poza APIRouter)
- ❌ Brak ręcznego mapowania ścieżek (poza aliasami)

**Status:** ✅ TYLKO FASTAPI + APIRouter

---

## 2.2 TABELA: MECHANIZM | PLIKI | JAK DZIAŁA | RYZYKO | DECYZJA DOCELOWA

| Mechanizm | Pliki | Jak działa | Ryzyko | Decyzja docelowa |
|-----------|-------|------------|--------|------------------|
| **APIRouter (standard)** | Wszystkie endpointy | `router = APIRouter(prefix="...")` → `app.include_router(router)` | ✅ Niskie | ✅ **ZOSTAĆ** - to jest standard |
| **Dynamiczne importy** | `app.py:82-161` | `importlib.import_module()` + try/except | ⚠️ Średnie - ciche pomijanie błędów | ✅ **ZOSTAĆ** ale dodać `STRICT_ROUTER_LOADING` |
| **Ręczne aliasy** | `app.py:224-256` | `app.add_api_route()` dla `/api/api/...` → `/api/...` | ✅ Niskie - tylko aliasy | ✅ **ZOSTAĆ** - pomocne dla kompatybilności |
| **Hardcoded importy** | `core/app.py:245-382` | Bezpośrednie `import` + `app.include_router()` | ❌ Wysokie - wywala się przy braku modułu | ❌ **USUNĄĆ** - używać `app.py` (root) |

---

## 2.3 KONFLIKTY I DUPLIKATY

### ❌ KONFLIKT 1: Duplikat `/api/chat`

**Routery:**
1. `assistant_simple.py:203` - `prefix="/api/chat"`
2. `core/assistant_endpoint.py:40` - `prefix="/api/chat"` ⚠️

**Endpointy:**
- `assistant_simple.py:254` - `POST /api/chat/assistant`
- `assistant_simple.py:288` - `POST /api/chat/assistant/stream`
- `core/assistant_endpoint.py:49` - `POST /api/chat/assistant` ⚠️ DUPLIKAT!
- `core/assistant_endpoint.py:73` - `POST /api/chat/assistant/stream` ⚠️ DUPLIKAT!
- `core/assistant_endpoint.py:107` - `POST /api/chat/auto` (unikalny)

**Wpływ:** 
- Jeśli oba są załadowane, FastAPI użyje ostatniego (ten który został dodany później)
- Niepewność który endpoint jest aktywny

**Naprawa:**
1. **Opcja A:** Usunąć `core/assistant_endpoint.py` i używać tylko `assistant_simple.py`
2. **Opcja B:** Przenieść `core/assistant_endpoint.py` do prefixu `/api/chat/advanced` i zostawić `assistant_simple.py` jako podstawowy
3. **Opcja C:** Połączyć funkcjonalność - `assistant_simple.py` jako wrapper, `core/assistant_endpoint.py` jako implementacja

**Rekomendacja:** Opcja B - `core/assistant_endpoint.py` ma więcej funkcji (cognitive engine), więc przenieść do `/api/chat/advanced`

---

### ❌ KONFLIKT 2: Duplikat `/api/research`

**Routery:**
1. `research_endpoint.py:15` - `prefix="/api/research"`
2. `core/research_endpoint.py:15` - `prefix="/api/research"` ⚠️

**Wpływ:** Ostatni załadowany nadpisuje pierwszy

**Naprawa:** Sprawdzić różnice i zdecydować który zostaje, lub zmienić prefix jednego

---

### ❌ KONFLIKT 3: Duplikat `/api/psyche`

**Routery:**
1. `psyche_endpoint.py:26` - `prefix="/api/psyche"`
2. `core/psyche_endpoint.py:26` - `prefix="/api/psyche"` ⚠️

**Wpływ:** Ostatni załadowany nadpisuje pierwszy

**Naprawa:** Sprawdzić różnice i zdecydować który zostaje

---

### ❌ KONFLIKT 4: Duplikat `/api/suggestions`

**Routery:**
1. `suggestions_endpoint.py:40` - `prefix="/api/suggestions"`
2. `core/suggestions_endpoint.py:23` - `prefix="/api/suggestions"` ⚠️

**Wpływ:** Ostatni załadowany nadpisuje pierwszy

**Naprawa:** Sprawdzić różnice i zdecydować który zostaje

---

### ❌ KONFLIKT 5: Duplikat `/metrics` (prometheus)

**Routery:**
1. `prometheus_endpoint.py:12` - `router = APIRouter()` (bez prefixu!)
2. `core/prometheus_endpoint.py:12` - `router = APIRouter()` (bez prefixu!) ⚠️

**Endpointy:**
- `prometheus_endpoint.py:14` - `GET /metrics`
- `core/prometheus_endpoint.py:14` - `GET /metrics` ⚠️ DUPLIKAT!

**Wpływ:** Ostatni załadowany nadpisuje pierwszy

**Naprawa:** 
- `core/prometheus_endpoint.py` jest mountowany w `core/app.py:317` z prefixem `/api/prometheus`
- `prometheus_endpoint.py` (root) nie ma prefixu w routerze, więc endpointy są na `/metrics`
- **Decyzja:** Zostawić `core/prometheus_endpoint.py` z prefixem `/api/prometheus`, usunąć `prometheus_endpoint.py` (root)

---

### ⚠️ NIESTANDARDOWY PREFIX: `/core/chat/advanced`

**Router:**
- `core/chat_advanced_endpoint.py:28` - `prefix="/core/chat/advanced"` ⚠️

**Problem:** Prefix `/core/...` nie jest zgodny z konwencją `/api/...`

**Naprawa:** Zmienić na `/api/chat/advanced`

---

## 2.4 DEAD ROUTES (nie załadowane do app)

### ❌ DEAD ROUTE 1: `core/chat_advanced_endpoint.py`

**Router:** `prefix="/core/chat/advanced"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `core/chat_advanced_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` ani `core_modules` w `app.py`

**Naprawa:** Dodać do `core_modules` w `app.py:132-142`

---

### ❌ DEAD ROUTE 2: `core/admin_endpoint.py`

**Router:** `prefix="/api/admin"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `core/admin_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` ani `core_modules` w `app.py`

**Naprawa:** Dodać do `core_modules` w `app.py:132-142`

---

### ❌ DEAD ROUTE 3: `core/hacker_endpoint.py`

**Router:** `prefix="/api/hacker"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `core/hacker_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` ani `core_modules` w `app.py`

**Naprawa:** Dodać do `core_modules` w `app.py:132-142` (opcjonalnie - jeśli funkcja jest potrzebna)

---

### ❌ DEAD ROUTE 4: `core/auction_endpoint.py`

**Router:** `prefix="/api/auction"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `core/auction_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` ani `core_modules` w `app.py`

**Naprawa:** Dodać do `core_modules` w `app.py:132-142` (opcjonalnie - jeśli funkcja jest potrzebna)

---

### ❌ DEAD ROUTE 5: `nlp_endpoint.py` (root)

**Router:** `prefix="/api/nlp"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `nlp_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` w `app.py`

**Naprawa:** Dodać do `root_modules` w `app.py:104-112`

---

### ❌ DEAD ROUTE 6: `writing_endpoint.py` (root)

**Router:** `prefix="/api/writing"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `writing_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` w `app.py`

**Naprawa:** Dodać do `root_modules` w `app.py:104-112`

---

### ❌ DEAD ROUTE 7: `programista_endpoint.py` (root)

**Router:** `prefix="/api/code"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `programista_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` w `app.py`

**Naprawa:** Dodać do `root_modules` w `app.py:104-112`

---

### ❌ DEAD ROUTE 8: `travel_endpoint.py` (root)

**Router:** `prefix="/api/travel"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `travel_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` w `app.py`

**Naprawa:** Dodać do `root_modules` w `app.py:104-112`

---

### ❌ DEAD ROUTE 9: `research_endpoint.py` (root)

**Router:** `prefix="/api/research"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `research_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` w `app.py`

**Naprawa:** Dodać do `root_modules` w `app.py:104-112` LUB usunąć jeśli `core/research_endpoint.py` jest używany

---

### ❌ DEAD ROUTE 10: `psyche_endpoint.py` (root)

**Router:** `prefix="/api/psyche"`  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `psyche_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` w `app.py`

**Naprawa:** Dodać do `root_modules` w `app.py:104-112` LUB usunąć jeśli `core/psyche_endpoint.py` jest używany

---

### ❌ DEAD ROUTE 11: `prometheus_endpoint.py` (root)

**Router:** `prefix=""` (bez prefixu)  
**Status:** ❌ NIE ZAŁADOWANY w `app.py` (root)  
**Lokalizacja:** `prometheus_endpoint.py`  
**Uzasadnienie:** Brak w liście `root_modules` w `app.py`

**Naprawa:** Usunąć - używać `core/prometheus_endpoint.py` z prefixem `/api/prometheus`

---

## 2.5 PLAN MIGRACJI DO JEDNEGO STANDARDU

### ✅ DECYZJA DOCELOWA: FastAPI + APIRouter (JEDYNY standard)

**Uzasadnienie:**
- Wszystkie routery już używają APIRouter ✅
- Brak innych frameworków ✅
- Dynamiczne importy są OK (z obsługą błędów) ✅

**Co NIE zmieniać:**
- ✅ APIRouter - zostaje
- ✅ Dynamiczne importy w `app.py` - zostają (ale dodać `STRICT_ROUTER_LOADING`)
- ✅ Aliasy `/api/api/...` → `/api/...` - zostają

**Co zmienić:**
- ❌ Usunąć `core/app.py` (alternatywny entrypoint)
- ❌ Rozwiązać duplikaty routerów
- ❌ Dodać dead routes do `app.py` LUB usunąć jeśli nieużywane
- ❌ Zmienić prefix `/core/chat/advanced` → `/api/chat/advanced`

---

### KROK 1: Rozwiązać duplikaty

**Akcje:**
1. `/api/chat`:
   - `assistant_simple.py` → `/api/chat` (podstawowy)
   - `core/assistant_endpoint.py` → `/api/chat/advanced` (zaawansowany)

2. `/api/research`:
   - Sprawdzić różnice między `research_endpoint.py` (root) a `core/research_endpoint.py`
   - Zostawić jeden, usunąć drugi LUB zmienić prefix

3. `/api/psyche`:
   - Sprawdzić różnice między `psyche_endpoint.py` (root) a `core/psyche_endpoint.py`
   - Zostawić jeden, usunąć drugi LUB zmienić prefix

4. `/api/suggestions`:
   - Sprawdzić różnice między `suggestions_endpoint.py` (root) a `core/suggestions_endpoint.py`
   - Zostawić jeden, usunąć drugi LUB zmienić prefix

5. `/metrics`:
   - Usunąć `prometheus_endpoint.py` (root)
   - Zostawić `core/prometheus_endpoint.py` z prefixem `/api/prometheus`

---

### KROK 2: Dodać dead routes do app.py

**Akcje:**
1. Dodać do `root_modules` w `app.py:104-112`:
   ```python
   ("nlp_endpoint", "NLP Analysis"),
   ("writing_endpoint", "Writing"),
   ("programista_endpoint", "Code Executor"),
   ("travel_endpoint", "Travel Search"),
   ("research_endpoint", "Research"),  # LUB usunąć jeśli core/research_endpoint jest używany
   ("psyche_endpoint", "Psyche"),  # LUB usunąć jeśli core/psyche_endpoint jest używany
   ```

2. Dodać do `core_modules` w `app.py:132-142`:
   ```python
   ("core.chat_advanced_endpoint", "Chat (Advanced) [core]"),
   ("core.admin_endpoint", "Admin [core]"),
   ("core.hacker_endpoint", "Hacker [core]"),  # opcjonalnie
   ("core.auction_endpoint", "Auction [core]"),  # opcjonalnie
   ```

---

### KROK 3: Zmienić niestandardowy prefix

**Akcje:**
1. `core/chat_advanced_endpoint.py:28`:
   ```python
   # PRZED:
   router = APIRouter(prefix="/core/chat/advanced", tags=["core-chat-advanced"])
   
   # PO:
   router = APIRouter(prefix="/api/chat/advanced", tags=["chat-advanced"])
   ```

---

### KROK 4: Usunąć core/app.py

**Akcje:**
1. Przenieść `core/app.py` do `core/app.py.legacy`
2. Zaktualizować dokumentację (jeśli istnieje)

---

## 2.6 CHECKLISTA NAPRAWY (P0/P1)

### P0 - BLOKUJĄCE START:

- [ ] **P0.1:** Rozwiązać duplikat `/api/chat` (przenieść `core/assistant_endpoint.py` do `/api/chat/advanced`)
- [ ] **P0.2:** Rozwiązać duplikat `/api/research` (zdecydować który zostaje)
- [ ] **P0.3:** Rozwiązać duplikat `/api/psyche` (zdecydować który zostaje)
- [ ] **P0.4:** Rozwiązać duplikat `/api/suggestions` (zdecydować który zostaje)
- [ ] **P0.5:** Usunąć `prometheus_endpoint.py` (root) - używać `core/prometheus_endpoint.py`

### P1 - BLOKUJĄCE FUNKCJE:

- [ ] **P1.1:** Dodać dead routes do `app.py` (nlp, writing, programista, travel, research, psyche)
- [ ] **P1.2:** Dodać dead routes z core do `app.py` (chat_advanced, admin, hacker, auction)
- [ ] **P1.3:** Zmienić prefix `/core/chat/advanced` → `/api/chat/advanced`
- [ ] **P1.4:** Usunąć/archiwizować `core/app.py`

### P2 - PORZĄDKI:

- [ ] **P2.1:** Dodać `STRICT_ROUTER_LOADING` w ENV (opcjonalnie - dla strict mode)
- [ ] **P2.2:** Dodać walidację że wszystkie routery mają unikalne prefixy przy starcie

---

**KONIEC CZĘŚCI 2**

