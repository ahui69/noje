# 🧪 TESTY - Mordzix AI

## 📁 STRUKTURA

```
tests/
├── conftest.py              # Pytest config + fixtures
├── test_api_endpoints.py    # API endpoints tests
├── test_core_modules.py     # Core modules tests
├── test_integration.py      # Integration E2E tests
├── test_vision_tts.py       # Vision/TTS/Captcha tests
└── README.md               # This file
```

---

## 🚀 JAK URUCHOMIĆ

### 1. Install dependencies:
```bash
pip install pytest pytest-asyncio httpx
```

### 2. Run ALL tests:
```bash
cd /workspace/full
pytest
```

### 3. Run specific test file:
```bash
pytest tests/test_api_endpoints.py
```

### 4. Run specific test class:
```bash
pytest tests/test_api_endpoints.py::TestChatEndpoint
```

### 5. Run specific test:
```bash
pytest tests/test_api_endpoints.py::TestChatEndpoint::test_chat_endpoint_exists
```

---

## 🎯 TEST COVERAGE

### ✅ API Endpoints (test_api_endpoints.py):
- `/api/chat/assistant` - Chat endpoint
- `/api/chat/assistant/stream` - Streaming
- `/api/tts/speak` - Text-to-speech
- `/api/tts/voices` - TTS voices list
- `/api/psyche/status` - Psyche state
- `/api/travel/search` - Travel search
- `/api/files/list` - Files management
- `/api/admin/stats` - Admin stats
- `/health` - Health check
- `/status` - Status endpoint

### ✅ Core Modules (test_core_modules.py):
- `core/config.py` - Configuration
- `core/auth.py` - Authentication
- `core/memory.py` - STM/LTM
- `core/llm.py` - LLM provider
- `core/semantic.py` - Embeddings
- `core/research.py` - Web research
- `core/tools.py` - Tools
- `core/writing.py` - Writing

### ✅ Integration (test_integration.py):
- Chat flow (single & multi-turn)
- Vision processing flow
- TTS generation flow
- Memory persistence
- Error handling
- Rate limiting

### ✅ Vision/TTS (test_vision_tts.py):
- Vision provider (OpenAI GPT-4o)
- TTS provider (ElevenLabs)
- Captcha solver (2Captcha)
- Proactive suggestions

---

## 📊 PRZYKŁADOWY OUTPUT

```bash
$ pytest

======================== test session starts =========================
collected 45 items

tests/test_api_endpoints.py::TestChatEndpoint::test_chat_endpoint_exists PASSED  [ 2%]
tests/test_api_endpoints.py::TestChatEndpoint::test_chat_requires_auth PASSED   [ 4%]
tests/test_api_endpoints.py::TestTTSEndpoint::test_tts_speak_endpoint PASSED    [ 6%]
tests/test_api_endpoints.py::TestHealthEndpoints::test_health_endpoint PASSED   [ 8%]
...

======================== 45 passed in 5.23s ==========================
```

---

## ⚙️ OPCJE PYTEST

### Verbose output:
```bash
pytest -v
```

### Stop on first failure:
```bash
pytest -x
```

### Run only failed tests:
```bash
pytest --lf
```

### Show print statements:
```bash
pytest -s
```

### Coverage report:
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
# Open htmlcov/index.html
```

---

## 🔧 FIXTURES DOSTĘPNE

- `client` - FastAPI test client
- `auth_headers` - Auth headers with token
- `test_message` - Sample chat message
- `test_image_base64` - Sample base64 image

### Użycie:
```python
def test_my_endpoint(client, auth_headers):
    response = client.get("/api/endpoint", headers=auth_headers)
    assert response.status_code == 200
```

---

## ⚠️ UWAGI

- Niektóre testy mogą failować bez API keys (OpenAI, ElevenLabs, etc.)
- To OK! Testy sprawdzają czy endpoints istnieją i odpowiadają
- Dla pełnego coverage dodaj API keys do `.env`

---

## 🚀 CI/CD

### GitHub Actions:
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio
      - run: pytest
```

---

**WSZYSTKO GOTOWE DO TESTOWANIA! 🔥**
