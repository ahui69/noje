# AUDYT PUNKT 4: KONTRAKT API + OPENAPI + STREAMING

**Data:** 2025-12-26  
**Zakres:** Analiza standardów odpowiedzi, autoryzacji, OpenAPI schema i streaming  
**Cel:** Zdefiniować docelowy kontrakt API dla frontendu, wykryć niespójności i naprawić

---

## 4.1 STANDARD ODPOWIEDZI SUCCESS

### Obecne wzorce (NIESPÓJNE):

#### Wzorzec A: `{"ok": true, "answer": "...", "sources": [], "metadata": {}}`

**Używany w:**
- `core/assistant_endpoint.py` → `ChatResponse`
- `core/chat_advanced_endpoint.py` → `CognitiveResult`

**Przykład:**
```json
{
  "ok": true,
  "answer": "Odpowiedź AI",
  "sources": [{"title": "...", "url": "..."}],
  "metadata": {
    "model": "mrd-advanced",
    "session_id": "...",
    "timestamp": "2025-12-26T..."
  }
}
```

**Status:** ✅ Dobry wzorzec

---

#### Wzorzec B: `{"answer": "...", "session_id": "...", "ts": 1234567890.123, "metadata": {}}`

**Używany w:**
- `assistant_simple.py` → `chat_assistant`

**Przykład:**
```json
{
  "answer": "Odpowiedź AI",
  "session_id": "abc123",
  "ts": 1703612800.123,
  "metadata": {
    "model": "NousResearch/Hermes-3-Llama-3.1-405B",
    "base_url": "https://api.deepinfra.com/v1/openai",
    "history_used": true
  }
}
```

**Status:** ⚠️ Brak pola `ok` - frontend musi sprawdzać czy `answer` istnieje

---

#### Wzorzec C: `{"status": "success", "suggestions": [...]}`

**Używany w:**
- `suggestions_endpoint.py`
- `core/suggestions_endpoint.py`

**Przykład:**
```json
{
  "status": "success",
  "suggestions": ["Sugestia 1", "Sugestia 2"]
}
```

**Status:** ⚠️ Różny format - używa `status` zamiast `ok`

---

#### Wzorzec D: `{"ok": true, "component": "..."}`

**Używany w:**
- `core/chat_advanced_endpoint.py` → `health()`

**Przykład:**
```json
{
  "ok": true,
  "component": "chat_advanced"
}
```

**Status:** ✅ Spójny z wzorcem A

---

#### Wzorzec E: OpenAI-compatible `{"id": "...", "object": "chat.completion", "choices": [...]}`

**Używany w:**
- `openai_compat.py` → `/v1/chat/completions`
- `core/chat_advanced_endpoint.py` → `chat_advanced_openai()`

**Przykład:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1703612800,
  "model": "mrd-advanced",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Odpowiedź"},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
}
```

**Status:** ✅ Standard OpenAI - OK dla kompatybilności

---

### 🎯 DOCELOWY STANDARD SUCCESS (REKOMENDOWANY):

```json
{
  "ok": true,
  "data": {
    // Dane specyficzne dla endpointu
  },
  "metadata": {
    "timestamp": 1703612800.123,
    "request_id": "req-abc123",
    "model": "...",  // opcjonalne
    "session_id": "...",  // opcjonalne
  }
}
```

**LUB dla chat (backward compatibility):**

```json
{
  "ok": true,
  "answer": "Odpowiedź AI",
  "sources": [],  // opcjonalne
  "metadata": {
    "timestamp": 1703612800.123,
    "model": "...",
    "session_id": "..."
  }
}
```

**Zalety:**
- Spójny format `ok: true/false`
- `data` dla danych specyficznych
- `metadata` dla informacji systemowych
- Backward compatible z istniejącymi endpointami

---

## 4.2 STANDARD ODPOWIEDZI ERROR

### Obecne wzorce (NIESPÓJNE):

#### Wzorzec A: FastAPI `HTTPException` → `{"detail": "Error message"}`

**Używany w:**
- Większość endpointów przez `raise HTTPException(status_code=401, detail="Unauthorized")`

**Przykład:**
```json
{
  "detail": "Unauthorized"
}
```

**Status:** ✅ Standard FastAPI - OK

---

#### Wzorzec B: Custom `{"ok": false, "error": "...", "detail": "..."}`

**Używany w:**
- `app.py` → `any_exc()` exception handler

**Przykład:**
```json
{
  "detail": "Internal Server Error",
  "error": "ValueError: ..."
}
```

**Status:** ⚠️ Brak pola `ok: false` - frontend musi sprawdzać status code

---

#### Wzorzec C: `{"ok": false, "answer": "Błąd: ...", "sources": [], "metadata": {}}`

**Używany w:**
- `core/assistant_endpoint.py` → `force_auto_learn()` przy błędzie

**Przykład:**
```json
{
  "ok": false,
  "answer": "Błąd podczas autonauki: ...",
  "sources": [],
  "metadata": {}
}
```

**Status:** ⚠️ Używa `answer` dla błędu - niespójne

---

#### Wzorzec D: `{"status": "error", "message": "..."}`

**Używany w:**
- `suggestions_endpoint.py`
- `core/suggestions_endpoint.py`

**Przykład:**
```json
{
  "status": "error",
  "message": "Brakujące pole: message"
}
```

**Status:** ⚠️ Różny format - używa `status` zamiast `ok`

---

### 🎯 DOCELOWY STANDARD ERROR (REKOMENDOWANY):

```json
{
  "ok": false,
  "error": {
    "code": "UNAUTHORIZED",  // lub "VALIDATION_ERROR", "INTERNAL_ERROR", etc.
    "message": "Unauthorized",
    "detail": "Missing or invalid authentication token"
  },
  "metadata": {
    "timestamp": 1703612800.123,
    "request_id": "req-abc123"
  }
}
```

**LUB dla backward compatibility z FastAPI:**

```json
{
  "detail": "Error message"
}
```

**Status codes:**
- `400` - Validation Error
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error
- `502` - Bad Gateway (upstream error)

---

## 4.3 STANDARD AUTORYZACJI

### Obecne wzorce (NIESPÓJNE):

#### Wzorzec A: `auth_dependency` z `core.auth` (Bearer Token)

**Używany w:**
- Większość core endpointów
- `core/assistant_endpoint.py`
- `core/cognitive_endpoint.py`
- `core/memory_endpoint.py`
- `core/reflection_endpoint.py`
- `core/legal_office_endpoint.py`
- `core/negocjator_endpoint.py`
- `core/batch_endpoint.py`
- `suggestions_endpoint.py` (root)
- `routers.py`

**Format:**
```python
from core.auth import auth_dependency

@router.post("/endpoint", dependencies=[Depends(auth_dependency)])
async def endpoint(...):
    ...
```

**Header:**
```
Authorization: Bearer {AUTH_TOKEN}
```

**Weryfikacja:**
- `core/auth.py:check_auth()` → używa `hmac.compare_digest()` (bezpieczne)
- Jeśli `AUTH_TOKEN` nie jest ustawiony → zwraca `True` (brak auth)

**Status:** ✅ Najlepszy wzorzec - bezpieczny, spójny

---

#### Wzorzec B: Custom `_auth()` funkcje

**Używany w:**
- `assistant_simple.py` → `_auth_ok()`
- `core/assistant_endpoint.py` → `_auth()`
- `files_endpoint.py` → `_auth()`
- `core/legal_office_endpoint.py` → `_auth()`

**Format:**
```python
def _auth_ok(req: Request) -> bool:
    if not AUTH_TOKEN:
        return True
    got = (req.headers.get("authorization") or "").strip()
    return got == AUTH_TOKEN  # ⚠️ NIE BEZPIECZNE - timing attack!

@router.post("/endpoint")
async def endpoint(req: Request, ...):
    if not _auth_ok(req):
        raise HTTPException(status_code=401, detail="Unauthorized")
    ...
```

**Header:**
```
Authorization: {AUTH_TOKEN}  # ⚠️ Bez "Bearer " prefix!
```

**Weryfikacja:**
- Proste porównanie stringów → ⚠️ **NIE BEZPIECZNE** (timing attack)
- Różne formaty headerów (`authorization` vs `Authorization`)

**Status:** ❌ **NIEBEZPIECZNE** - używa prostego porównania zamiast `hmac.compare_digest()`

---

#### Wzorzec C: `verify_token()` z `core.auth`

**Używany w:**
- `core/cognitive_endpoint.py`
- `core/reflection_endpoint.py`
- `core/suggestions_endpoint.py` (core)

**Format:**
```python
from core.auth import verify_token

def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "unauthorized")
    token = authorization.replace("Bearer ", "").strip()
    if token != AUTH_TOKEN:  # ⚠️ NIE BEZPIECZNE!
        raise HTTPException(401, "unauthorized")
    return True

@router.post("/endpoint")
async def endpoint(..., auth=Depends(verify_token)):
    ...
```

**Status:** ⚠️ **NIEBEZPIECZNE** - używa prostego porównania

---

#### Wzorzec D: Brak autoryzacji

**Używany w:**
- `assistant_endpoint.py` (root) → zwraca `True` zawsze
- Wiele endpointów health/status
- `prometheus_endpoint.py` → `/metrics` (standard Prometheus)

**Status:** ✅ OK dla publicznych endpointów (health, metrics)

---

### 🎯 DOCELOWY STANDARD AUTORYZACJI (REKOMENDOWANY):

**Jeden standard: `auth_dependency` z `core.auth`**

```python
from core.auth import auth_dependency

@router.post("/endpoint", dependencies=[Depends(auth_dependency)])
async def endpoint(...):
    ...
```

**Header (standard):**
```
Authorization: Bearer {AUTH_TOKEN}
```

**Zalety:**
- ✅ Bezpieczne - używa `hmac.compare_digest()`
- ✅ Spójne - jeden wzorzec dla wszystkich endpointów
- ✅ FastAPI dependency - automatyczna walidacja
- ✅ Obsługuje brak `AUTH_TOKEN` (zwraca `True`)

**Migracja:**
1. Zastąpić wszystkie custom `_auth()` funkcje przez `auth_dependency`
2. Ujednolicić format header: `Authorization: Bearer {token}`
3. Usunąć proste porównania stringów

---

## 4.4 OPENAPI SCHEMA

### Obecny stan:

#### Generowanie schema:

**Entrypoint:** FastAPI automatycznie generuje OpenAPI schema z:
- Dekoratorów `@router.get/post/...()`
- Modeli Pydantic (`response_model`, `BaseModel`)
- Docstrings funkcji

**Endpoint:** `/openapi.json` i `/docs` (Swagger UI)

**Problemy wykryte:**

1. **Duplikaty ścieżek:**
   - `/api/chat/assistant` - 3 routery (konflikt)
   - `/api/chat/assistant/stream` - 3 routery (konflikt)
   - `/api/suggestions/*` - 2 routery (duplikaty)

2. **Brakujące `response_model`:**
   - Wiele endpointów nie ma `response_model` → schema nie ma struktury odpowiedzi
   - Przykład: `assistant_simple.py` → `chat_assistant()` nie ma `response_model`

3. **Niespójne modele:**
   - Różne nazwy pól (`ok` vs `status`, `answer` vs `content`)
   - Różne struktury (`ChatResponse` vs `CognitiveResult`)

4. **Brakujące opisy:**
   - Wiele endpointów nie ma `summary` ani `description`
   - Przykład: `files_endpoint.py` → większość endpointów bez opisów

---

### 🎯 DOCELOWY STANDARD OPENAPI:

#### 1. Wszystkie endpointy mają `response_model`:

```python
from pydantic import BaseModel

class ChatResponse(BaseModel):
    ok: bool
    answer: str
    sources: Optional[List[Dict]] = []
    metadata: Dict[str, Any] = {}

@router.post("/assistant", response_model=ChatResponse)
async def chat_assistant(...):
    ...
```

#### 2. Wszystkie endpointy mają `summary` i `description`:

```python
@router.post(
    "/assistant",
    response_model=ChatResponse,
    summary="Chat z AI",
    description="Główny endpoint do rozmowy z AI. Obsługuje pamięć, research i streaming."
)
async def chat_assistant(...):
    ...
```

#### 3. Wszystkie modele mają `Field` z opisami:

```python
class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="Lista wiadomości w konwersacji")
    user_id: Optional[str] = Field("default", description="ID użytkownika")
    use_memory: bool = Field(True, description="Czy używać pamięci długoterminowej")
```

#### 4. Wszystkie błędy mają `responses`:

```python
@router.post(
    "/assistant",
    response_model=ChatResponse,
    responses={
        401: {"description": "Unauthorized - brak lub nieprawidłowy token"},
        400: {"description": "Bad Request - nieprawidłowe dane wejściowe"},
        500: {"description": "Internal Server Error"}
    }
)
async def chat_assistant(...):
    ...
```

---

## 4.5 STREAMING (SSE - Server-Sent Events)

### Obecne implementacje:

#### Implementacja A: OpenAI-compatible (`openai_compat.py`)

**Endpoint:** `POST /v1/chat/completions` (z `stream: true`)

**Format chunków:**
```
data: {"id": "chatcmpl-abc", "object": "chat.completion.chunk", "choices": [{"delta": {"content": "tekst"}, "finish_reason": null}]}

data: {"id": "chatcmpl-abc", "object": "chat.completion.chunk", "choices": [{"delta": {"content": "tekst"}, "finish_reason": null}]}

data: [DONE]
```

**Keepalive:**
```
: keepalive

```

**Media type:** `text/event-stream`

**Headers:**
- `Content-Type: text/event-stream`
- `Cache-Control: no-cache`
- `Connection: keep-alive`

**Status:** ✅ Standard OpenAI - kompatybilny z klientami OpenAI

---

#### Implementacja B: Custom format (`assistant_simple.py`)

**Endpoint:** `POST /api/chat/assistant/stream`

**Format chunków:**
```
data: {"event": "meta", "data": {"session_id": "abc", "ts": 1234567890.123, "model": "..."}}

data: {"event": "delta", "data": "tekst"}

data: {"event": "delta", "data": "tekst"}

data: {"event": "done", "data": {"ok": true}}
```

**Keepalive:**
```
: ping

```

**Media type:** `text/event-stream`

**Status:** ⚠️ Custom format - niekompatybilny z OpenAI

---

#### Implementacja C: Custom format (`core/assistant_endpoint.py`)

**Endpoint:** `POST /api/chat/assistant/stream`

**Format chunków:**
```
data: {"type": "start"}

data: {"type": "chunk", "content": "tekst"}

data: {"type": "chunk", "content": "tekst"}

data: {"type": "complete", "answer": "pełna odpowiedź", "metadata": {...}}
```

**Media type:** `text/event-stream`

**Status:** ⚠️ Custom format - niekompatybilny z OpenAI

---

#### Implementacja D: Custom format (`core/chat_advanced_endpoint.py`)

**Endpoint:** `POST /core/chat/advanced/stream` (DEAD)

**Format chunków:**
```
event: message
data: {"type": "start"}

data: {"choices": [{"delta": {"content": "tekst"}, "index": 0, "finish_reason": null}]}

data: {"choices": [{"delta": {"content": "tekst"}, "index": 0, "finish_reason": null}]}

data: {"choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]}

data: [DONE]

```

**Media type:** `text/event-stream`

**Status:** ❌ DEAD - endpoint nie jest aktywny

---

### 🎯 DOCELOWY STANDARD STREAMING (REKOMENDOWANY):

#### Opcja A: OpenAI-compatible (REKOMENDOWANA)

**Format chunków:**
```
data: {"id": "chatcmpl-abc", "object": "chat.completion.chunk", "created": 1234567890, "model": "...", "choices": [{"index": 0, "delta": {"content": "tekst"}, "finish_reason": null}]}

data: [DONE]
```

**Zalety:**
- ✅ Kompatybilny z klientami OpenAI
- ✅ Standardowy format
- ✅ Łatwa integracja z frontendem

**Używany w:** `/v1/chat/completions` (już działa)

---

#### Opcja B: Custom format (dla backward compatibility)

**Format chunków:**
```
data: {"type": "start", "session_id": "abc", "model": "..."}

data: {"type": "chunk", "content": "tekst"}

data: {"type": "chunk", "content": "tekst"}

data: {"type": "complete", "answer": "pełna odpowiedź", "metadata": {...}}
```

**Zalety:**
- ✅ Więcej informacji (session_id, metadata)
- ✅ Łatwiejsze parsowanie (tylko `type` i `content`)

**Używany w:** `/api/chat/assistant/stream` (custom endpointy)

---

### Standardy techniczne:

#### Headers (wymagane):

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no  # dla nginx
```

#### Keepalive:

- **Interwał:** 15-30 sekund (lub konfigurowalny przez ENV)
- **Format:** `: keepalive\n\n` (komentarz SSE)
- **Cel:** Zapobieganie timeoutom proxy/load balancer

#### Chunk format:

- **Minimalny rozmiar:** 1 znak
- **Maksymalny rozmiar:** 1800 znaków (konfigurowalny)
- **Boundary detection:** Dzielenie na granicach zdań (`.!?\n`)

#### Client disconnection handling:

- **Wykrywanie:** FastAPI automatycznie wykrywa zamknięcie połączenia
- **Cleanup:** Używać `try/finally` do zwolnienia zasobów
- **Logowanie:** Logować przerwane połączenia

**Przykład:**
```python
async def generate():
    try:
        # Stream logic
        async for chunk in stream_source:
            yield chunk
    except asyncio.CancelledError:
        # Client disconnected
        log_info("Client disconnected")
        raise
    finally:
        # Cleanup
        await cleanup_resources()
```

---

## 4.6 PROBLEMY I NAPRAWY

### ❌ PROBLEM 1: Niespójne formaty odpowiedzi

**Objaw:** Różne endpointy używają różnych formatów (`ok` vs `status`, `answer` vs `content`)  
**Wpływ:** Frontend musi obsługiwać wiele formatów  
**Naprawa:**
1. Ujednolicić do wzorca: `{"ok": true, "data": {...}, "metadata": {...}}`
2. Dla backward compatibility: zachować `{"ok": true, "answer": "...", "sources": [], "metadata": {...}}` dla chat

**Pliki do zmiany:**
- `suggestions_endpoint.py` → zmienić `status` na `ok`
- `assistant_simple.py` → dodać `ok: true` do odpowiedzi

---

### ❌ PROBLEM 2: Niebezpieczne metody autoryzacji

**Objaw:** Custom `_auth()` funkcje używają prostego porównania stringów  
**Wpływ:** Podatność na timing attack  
**Naprawa:**
1. Zastąpić wszystkie custom `_auth()` przez `auth_dependency` z `core.auth`
2. Ujednolicić format header: `Authorization: Bearer {token}`

**Pliki do zmiany:**
- `assistant_simple.py` → użyć `auth_dependency`
- `core/assistant_endpoint.py` → użyć `auth_dependency`
- `files_endpoint.py` → użyć `auth_dependency`
- `core/legal_office_endpoint.py` → użyć `auth_dependency`

---

### ❌ PROBLEM 3: Brakujące `response_model` w OpenAPI

**Objaw:** Wiele endpointów nie ma `response_model` → schema nie ma struktury odpowiedzi  
**Wpływ:** Frontend nie wie jakiej struktury oczekiwać  
**Naprawa:**
1. Dodać `response_model` do wszystkich endpointów
2. Dodać `summary` i `description` do wszystkich endpointów
3. Dodać `responses` z kodami błędów

**Pliki do zmiany:**
- `assistant_simple.py` → dodać `response_model=ChatResponse`
- `files_endpoint.py` → dodać modele odpowiedzi
- Wszystkie endpointy bez `response_model`

---

### ❌ PROBLEM 4: Niespójne formaty streaming

**Objaw:** 4 różne formaty streaming (OpenAI, custom, custom2, custom3)  
**Wpływ:** Frontend musi obsługiwać wiele formatów  
**Naprawa:**
1. Ujednolicić do OpenAI-compatible dla `/v1/chat/completions`
2. Ujednolicić do custom format dla `/api/chat/assistant/stream`
3. Usunąć nieaktywne endpointy streaming

**Pliki do zmiany:**
- `core/assistant_endpoint.py` → ujednolicić format
- `assistant_simple.py` → ujednolicić format

---

## 4.7 CHECKLIST NAPRAWY

### P0 - BLOKUJĄCE:

- [ ] **P0.1:** Zastąpić niebezpieczne `_auth()` przez `auth_dependency` (timing attack)
- [ ] **P0.2:** Ujednolicić format header: `Authorization: Bearer {token}`

### P1 - WAŻNE:

- [ ] **P1.1:** Ujednolicić formaty odpowiedzi (`ok` vs `status`)
- [ ] **P1.2:** Dodać `response_model` do wszystkich endpointów
- [ ] **P1.3:** Ujednolicić formaty streaming

### P2 - CLEANUP:

- [ ] **P2.1:** Dodać `summary` i `description` do wszystkich endpointów
- [ ] **P2.2:** Dodać `responses` z kodami błędów do OpenAPI
- [ ] **P2.3:** Dodać `Field` z opisami do wszystkich modeli Pydantic

---

## 4.8 WERYFIKACJA KOŃCOWA

### Test 1: Sprawdź OpenAPI schema

```bash
curl http://localhost:8080/openapi.json | jq '.paths | keys | length'
# Powinno zwrócić liczbę endpointów

curl http://localhost:8080/openapi.json | jq '.paths."/api/chat/assistant".post.responses'
# Powinno zwrócić strukturę odpowiedzi
```

### Test 2: Sprawdź czy nie ma duplikatów ścieżek

```bash
curl http://localhost:8080/openapi.json | jq '.paths | keys | group_by(.) | map(select(length > 1))'
# Powinno zwrócić pustą listę []
```

### Test 3: Sprawdź streaming

```bash
# Test OpenAI-compatible streaming
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "test"}], "stream": true}' \
  --no-buffer

# Test custom streaming
curl -X POST http://localhost:8080/api/chat/assistant/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{"messages": [{"role": "user", "content": "test"}]}' \
  --no-buffer
```

### Test 4: Sprawdź autoryzację

```bash
# Test z poprawnym tokenem
curl -X POST http://localhost:8080/api/chat/assistant \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'
# Powinno zwrócić 200 OK

# Test bez tokenu
curl -X POST http://localhost:8080/api/chat/assistant \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'
# Powinno zwrócić 401 Unauthorized
```

---

## 4.9 DEFINICJA DONE (DoD)

✅ **Kontrakt API zakończony gdy:**
1. Wszystkie endpointy używają `auth_dependency` (bezpieczna autoryzacja)
2. Wszystkie odpowiedzi mają spójny format (`ok: true/false`)
3. Wszystkie endpointy mają `response_model` w OpenAPI
4. Streaming jest ujednolicony (OpenAI-compatible dla `/v1`, custom dla `/api/chat`)
5. OpenAPI schema generuje się bez błędów
6. Brak duplikatów ścieżek w OpenAPI

---

**STOP — sprawdź ten punkt. Czy coś poprawić/doprecyzować? Czy mam dodać coś jeszcze? Jeśli OK, przechodzę do następnego punktu: `AUDYT/05_IMPORTY_CYKLE_BRAKI_ASYNC_BLOCKING.md`.**

