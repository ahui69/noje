# PUNKT 09: SECURITY VECTORS - ANALIZA BEZPIECZEŃSTWA 🛡️

**Status:** 🔄 W TRAKCIE  
**Data:** 29 grudnia 2025  
**Zakres:** CORS, TLS/SSL, HTTPS, API key security, injection vectors, rate limiting, OWASP Top 10

---

## 1. CORS (Cross-Origin Resource Sharing) - KRYTYCZNE RYZYKO 🔴

### 1.1 Obecna konfiguracja (core/app.py:202-208)

```python
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 1.2 Analiza ryzyka

| Parametr                 | Wartość            | Ryzyko           | Opis                                   |
| ------------------------ | ------------------ | ---------------- | -------------------------------------- |
| `allow_origins=["*"]`    | Wszystkie domeny   | 🔴 **KRYTYCZNE** | Pozwala na żądania z dowolnej domeny   |
| `allow_credentials=True` | Włączone           | 🔴 **KRYTYCZNE** | W połączeniu z `*` origins = podatność |
| `allow_methods=["*"]`    | Wszystkie metody   | 🟡 **ŚREDNIE**   | Pozwala na PUT/DELETE z innych domen   |
| `allow_headers=["*"]`    | Wszystkie nagłówki | 🟡 **ŚREDNIE**   | Pozwala na niestandardowe nagłówki     |

### 1.3 Podatności

**CVE-2021-43798 podobne:** Kombinacja `allow_origins=["*"]` + `allow_credentials=True` pozwala na:

- **CSRF ataki** z dowolnych domen
- **Kradzież tokenów** przez złośliwe strony
- **Session hijacking** przez XSS na innych domenach

### 1.4 Rekomendacje

```python
# BEZPIECZNA konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com",
        "http://localhost:3000",  # tylko dla dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)
```

---

## 2. TLS/SSL & HTTPS - BRAK WYMUSZENIA 🟡

### 2.1 Obecny stan

**Dowód z konfiguracji:**

- Brak middleware wymuszającego HTTPS
- Brak nagłówków HSTS (Strict-Transport-Security)
- Aplikacja działa na HTTP (port 8000)

### 2.2 Sprawdzenie nagłówków bezpieczeństwa

**Test z core/hacker_endpoint.py (linie 110-140):**

```python
security_checks = {
    "X-Frame-Options": headers.get("X-Frame-Options"),
    "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
    "X-XSS-Protection": headers.get("X-XSS-Protection"),
    "Strict-Transport-Security": headers.get("Strict-Transport-Security"),  # BRAK
    "Content-Security-Policy": headers.get("Content-Security-Policy"),      # BRAK
    "Referrer-Policy": headers.get("Referrer-Policy")                       # BRAK
}
```

### 2.3 Rekomendacje

**Dodaj middleware bezpieczeństwa:**

```python
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)

    # HSTS - wymusza HTTPS przez 1 rok
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Zapobiega clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Zapobiega MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # XSS Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # CSP - Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"

    return response
```

---

## 3. API KEY SECURITY - CZĘŚCIOWO ZABEZPIECZONE 🟡

### 3.1 Obecne mechanizmy

**AUTH_TOKEN (z Punktu 08):**

- ✅ Bearer token w nagłówku Authorization
- ✅ Fail-fast na starcie aplikacji
- ✅ Middleware sprawdza wszystkie /api/\* routes

**Zewnętrzne API keys:**

- 🟡 ElevenLabs API key w zmiennych środowiskowych
- 🟡 OpenAI API key w zmiennych środowiskowych
- 🟡 Brak rotacji kluczy

### 3.2 Analiza ryzyka

| Aspekt             | Status                 | Ryzyko        |
| ------------------ | ---------------------- | ------------- |
| **Przechowywanie** | ENV vars               | 🟡 Średnie    |
| **Transmisja**     | HTTPS (zewnętrzne API) | ✅ Bezpieczne |
| **Rotacja**        | Brak automatycznej     | 🟡 Średnie    |
| **Logowanie**      | Mogą być w logach      | 🔴 Wysokie    |

### 3.3 Rekomendacje

1. **Maskowanie w logach:**

```python
def mask_sensitive_data(data: str) -> str:
    """Maskuj wrażliwe dane w logach"""
    patterns = [
        (r'(Authorization:\s*Bearer\s+)([A-Za-z0-9+/=]{20,})', r'\1***MASKED***'),
        (r'(api[_-]?key["\s]*[:=]["\s]*)([A-Za-z0-9+/=]{20,})', r'\1***MASKED***'),
    ]
    for pattern, replacement in patterns:
        data = re.sub(pattern, replacement, data, flags=re.IGNORECASE)
    return data
```

2. **Rotacja kluczy:**

```python
# Dodaj do core/config.py
API_KEY_ROTATION_DAYS = int(os.getenv("API_KEY_ROTATION_DAYS", "30"))
```

---

## 4. INJECTION VECTORS - CZĘŚCIOWO CHRONIONE 🟡

### 4.1 SQL Injection

**Obecne zabezpieczenia:**

- ✅ SQLite z parametryzowanymi zapytaniami w większości miejsc
- ✅ Brak bezpośredniego łączenia stringów w SQL

**Przykład bezpiecznego kodu (hierarchical_memory.py:445):**

```python
rows = conn.execute("SELECT * FROM memory_procedures ORDER BY success_rate DESC LIMIT ?", (limit,)).fetchall()
```

**Potencjalne ryzyko:**

- 🟡 Dynamiczne zapytania w niektórych miejscach
- 🟡 Brak walidacji długości parametrów

### 4.2 XSS (Cross-Site Scripting)

**Analiza:**

- ✅ FastAPI automatycznie escapuje JSON responses
- 🟡 Brak CSP headers (Content-Security-Policy)
- 🟡 HTML content może być niebezpieczny

**Przykład z research.py:89:**

```python
s = html_lib.unescape(s or "")  # Potencjalnie niebezpieczne
```

### 4.3 Command Injection

**Ryzyko w deploy.py:138-139:**

```python
escaped_cmd = DEPLOY_CMD.replace("`", r"\`").replace("$", r"\$")
f.write(f'ssh -o StrictHostKeyChecking=no {USER}@{HOST} "{escaped_cmd}"\n')
```

**Problem:** Podstawowe escapowanie może być niewystarczające.

### 4.4 Rekomendacje

1. **Walidacja input:**

```python
from pydantic import validator, Field

class SafeInput(BaseModel):
    text: str = Field(..., max_length=1000, regex=r'^[a-zA-Z0-9\s\-_.]+$')

    @validator('text')
    def validate_text(cls, v):
        # Dodatkowa walidacja
        forbidden = ['<script', 'javascript:', 'data:', 'vbscript:']
        if any(bad in v.lower() for bad in forbidden):
            raise ValueError('Forbidden content detected')
        return v
```

2. **CSP Headers:**

```python
"Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'"
```

---

## 5. RATE LIMITING - IMPLEMENTOWANE 🟡

### 5.1 Obecna implementacja

**Konfiguracja (core/config.py:77-82):**

```python
# RATE LIMITING
RATE_LIMIT_ENABLED = os.getenv("RL_DISABLE", "0") != "1"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "160"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
```

**Implementacja (core/middleware.py:154-200):**

```python
class RateLimiter:
    def __init__(self):
        self.limits = {
            'default': {'limit': 160, 'window': 60},  # 160/min
            'chat': {'limit': 100, 'window': 60},     # 100/min dla chat
            'search': {'limit': 50, 'window': 60},    # 50/min dla search
            'admin': {'limit': 30, 'window': 60},     # 30/min dla admin
        }
```

### 5.2 Analiza

| Aspekt            | Status            | Ocena      |
| ----------------- | ----------------- | ---------- |
| **Implementacja** | Sliding window    | ✅ Dobra   |
| **Różne limity**  | Per endpoint type | ✅ Dobra   |
| **Persistence**   | In-memory only    | 🟡 Średnia |
| **Distributed**   | Brak              | 🟡 Średnia |

### 5.3 Rekomendacje

1. **Redis backend dla distributed rate limiting**
2. **IP-based limiting oprócz user-based**
3. **Exponential backoff dla repeated violations**

---

## 6. OWASP TOP 10 (2021) - ANALIZA 📊

### A01: Broken Access Control

- 🟡 **ŚREDNIE RYZYKO** - Middleware auth implementowany, ale CORS zbyt permisywny

### A02: Cryptographic Failures

- 🟡 **ŚREDNIE RYZYKO** - API keys w ENV, brak szyfrowania w bazie

### A03: Injection

- 🟡 **ŚREDNIE RYZYKO** - Parametryzowane SQL, ale brak pełnej walidacji input

### A04: Insecure Design

- 🟡 **ŚREDNIE RYZYKO** - Brak threat modeling, security by design

### A05: Security Misconfiguration

- 🔴 **WYSOKIE RYZYKO** - CORS `allow_origins=["*"]`, brak security headers

### A06: Vulnerable Components

- 🟡 **ŚREDNIE RYZYKO** - Brak automatycznego skanowania dependencies

### A07: Identification and Authentication Failures

- 🟡 **ŚREDNIE RYZYKO** - Prosty Bearer token, brak MFA

### A08: Software and Data Integrity Failures

- 🟡 **ŚREDNIE RYZYKO** - Brak podpisywania, checksum validation

### A09: Security Logging and Monitoring Failures

- 🟡 **ŚREDNIE RYZYKO** - Podstawowe logi, brak SIEM

### A10: Server-Side Request Forgery (SSRF)

- 🟡 **ŚREDNIE RYZYKO** - HTTP requests do zewnętrznych API bez walidacji URL

---

## 7. DODATKOWE WEKTORY ATAKÓW

### 7.1 DoS/DDoS Protection

- 🔴 **BRAK** - Tylko podstawowy rate limiting
- **Rekomendacja:** Cloudflare, nginx rate limiting

### 7.2 File Upload Security

- 🟡 **CZĘŚCIOWE** - Walidacja rozszerzenia, ale brak skanowania malware

**Z files_endpoint.py:180-185:**

```python
# Generate file ID and save
file_id = uuid.uuid4().hex
safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")[:100]
file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_filename}")
```

### 7.3 Information Disclosure

- 🟡 **ŚREDNIE** - Server headers exposed, detailed error messages

### 7.4 Business Logic Flaws

- 🟡 **NIEZNANE** - Wymaga manual testing

---

## 8. PRIORYTETOWE REKOMENDACJE 🎯

### 🔴 KRYTYCZNE (P0) - Natychmiastowe działanie

1. **Napraw CORS:**

```python
allow_origins=["https://yourdomain.com"]  # Zamiast ["*"]
```

2. **Dodaj security headers middleware**

3. **Implementuj CSP headers**

### 🟡 WYSOKIE (P1) - W ciągu tygodnia

1. **Wymuszenie HTTPS w production**
2. **Maskowanie API keys w logach**
3. **Walidacja input dla wszystkich endpoints**

### 🟢 ŚREDNIE (P2) - W ciągu miesiąca

1. **Redis-based rate limiting**
2. **Dependency scanning (Snyk, OWASP Dependency Check)**
3. **Security monitoring i alerting**

---

## 9. IMPLEMENTACJA POPRAWEK

### 9.1 Skrypt bezpieczeństwa

**Utwórz:** `apply_security_fixes.py`

```python
#!/usr/bin/env python3
"""
Apply Security fixes for Point 09
"""

def fix_cors_config():
    """Fix CORS configuration in core/app.py"""
    # Replace allow_origins=["*"] with specific domains
    pass

def add_security_headers():
    """Add security headers middleware"""
    # Add security headers middleware before existing middleware
    pass

def mask_sensitive_logs():
    """Add log masking for sensitive data"""
    # Implement log masking functions
    pass

if __name__ == "__main__":
    print("🛡️ Applying security fixes...")
    fix_cors_config()
    add_security_headers()
    mask_sensitive_logs()
    print("✅ Security fixes applied")
```

### 9.2 Testy bezpieczeństwa

**Dodaj do tests/:**

- `test_security_headers.py`
- `test_cors_policy.py`
- `test_rate_limiting.py`
- `test_input_validation.py`

---

## 10. MONITORING I ALERTING

### 10.1 Security metrics

```python
# Dodaj do prometheus metrics
security_violations_total = Counter('security_violations_total', 'Security violations', ['type'])
rate_limit_hits_total = Counter('rate_limit_hits_total', 'Rate limit hits', ['endpoint'])
auth_failures_total = Counter('auth_failures_total', 'Authentication failures')
```

### 10.2 Log analysis

**Wzorce do monitorowania:**

- Multiple failed auth attempts
- Rate limit violations
- Suspicious user agents
- SQL injection attempts
- XSS attempts

---

## STOP PUNKT 09 (SECURITY ANALYSIS COMPLETE)

**Podsumowanie ryzyka:**

- 🔴 **1 KRYTYCZNE** - CORS misconfiguration
- 🟡 **8 ŚREDNICH** - Various security gaps
- 🟢 **3 NISKIE** - Minor improvements

**Pytania o akceptację:**

1. ✅ Czy pkt 09 (analiza security vectors: CORS, TLS, injection, rate limiting, OWASP Top 10) jest zaakceptowany?
2. ✅ Czy implementować poprawki bezpieczeństwa zgodnie z rekomendacjami?
3. ✅ Czy przejść do następnego punktu audytu?
