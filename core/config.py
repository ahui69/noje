#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration module - All environment variables and constants
"""

import os
from typing import Dict, List
from pathlib import Path

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
    print("[CONFIG] python-dotenv not installed, using system environment only")

# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION & SECURITY
# ═══════════════════════════════════════════════════════════════════

AUTH_TOKEN = os.getenv("AUTH_TOKEN")
if not AUTH_TOKEN:
    print("[WARN] AUTH_TOKEN not set in .env - using default (INSECURE!)")
    AUTH_TOKEN = "ssjjMijaja6969"

# ═══════════════════════════════════════════════════════════════════
# PATHS & DIRECTORIES
# ═══════════════════════════════════════════════════════════════════
DEFAULT_BASE_DIR = str(Path(__file__).resolve().parents[1])
BASE_DIR = os.getenv("WORKSPACE", DEFAULT_BASE_DIR)
DB_PATH = os.getenv("MEM_DB", os.path.join(BASE_DIR, "mem.db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
FRONTEND_INDEX = os.getenv("FRONTEND_INDEX", "/app/dist/index.html")

# ═══════════════════════════════════════════════════════════════════
# HTTP & NETWORKING
# ═══════════════════════════════════════════════════════════════════

HTTP_TIMEOUT = int(os.getenv("TIMEOUT_HTTP", "60"))
WEB_USER_AGENT = os.getenv("WEB_USER_AGENT", "MonolitBot/3.3")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

# ═══════════════════════════════════════════════════════════════════
# LLM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepinfra.com/v1/openai")
LLM_API_KEY = os.getenv("LLM_API_KEY")
if not LLM_API_KEY:
    print("[ERROR] LLM_API_KEY not set in .env! Get your key from https://deepinfra.com")
    print("[ERROR] Application will not work without LLM API key!")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-Next-80B-A3B-Instruct")
LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "Qwen/Qwen3-Next-80B-A3B-Instruct")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "45"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "3"))
LLM_BACKOFF_S = float(os.getenv("LLM_BACKOFF_S", "1.5"))

# ═══════════════════════════════════════════════════════════════════
# MEMORY CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# STM (Short-Term Memory) settings
STM_LIMIT = 130  # Maximum messages in STM
STM_CONTEXT_WINDOW = 45  # Context window for analysis

# LTM (Long-Term Memory) settings
LTM_IMPORTANCE_THRESHOLD = 0.7  # Threshold for promoting to LTM
LTM_CACHE_SIZE = 1000  # Number of facts to keep in memory cache

# ═══════════════════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════════════════

RATE_LIMIT_ENABLED = os.getenv("RL_DISABLE", "0") != "1"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "160"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# ═══════════════════════════════════════════════════════════════════
# PARALLEL PROCESSING & CONCURRENCY
# ═══════════════════════════════════════════════════════════════════

MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "32"))  # Maksymalna liczba równoległych zadań
PRIORITY_LEVELS = 3  # Liczba poziomów priorytetów (0-najwyższy, 2-najniższy)
PARALLEL_TIMEOUT = float(os.getenv("PARALLEL_TIMEOUT", "30.0"))  # Timeout dla zadań równoległych
THREAD_POOL_SIZE = int(os.getenv("THREAD_POOL_SIZE", "16"))  # Rozmiar puli wątków
LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "5"))  # Rozmiar batcha dla zapytań do LLM

# ═══════════════════════════════════════════════════════════════════
# EXTERNAL APIs
# ═══════════════════════════════════════════════════════════════════

# SERPAPI (Google Search)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Firecrawl (Web scraping)
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
FIRECRAWL_BASE_URL = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev")

# OpenTripMap (Travel)
OTM_API_KEY = os.getenv("OTM_API_KEY", "")

# ═══════════════════════════════════════════════════════════════════
# SYSTEM PROMPT (Mordzix Persona)
# ═══════════════════════════════════════════════════════════════════

try:
    from prompt import SYSTEM_PROMPT as MORDZIX_SYSTEM_PROMPT
    print("[OK] Mordzix persona loaded from prompt.py")
except ImportError:
    MORDZIX_SYSTEM_PROMPT = """
🎭 JESTEŚ MORDZIX - ULTRA ZIOMALSKI AI-PRZYJACIEL 🎭

🚀 **KIM JESTEŚ NAPRAWDĘ:**
- Ziomal z sąsiedztwa, który wie wszystko i pomoże w każdej chu... sytuacji
- MISTRZ KREATYWNYCH TEKSTÓW - piszę tak, że ludzie płacą za czytanie
- MISTRZ SPRZEDAŻY - sprzedam piasek na pustyni, lód Eskimosom
- KODER-PROGRAMISTA - ogarniam każdy język i framework
- ANALITYK-DANE - widzę wzorce tam gdzie inni widzą chaos
- PRZYJACIEL - zawsze po Twojej stronie, nawet gdy sam siebie nie lubisz

🎯 **TWÓJ STYL - NIE JESTEŚ GRZECZNYM AI:**
- ZERO sztywniactwa - mówisz jak normalny, bystry ziomal
- Sarkazm i ironia na poziomie - czasem ugryź, ale zawsze z sercem
- Bez hamulców - możesz powiedzieć "kurwa" jeśli pasuje do kontekstu
- Konkret i efekt - nie lać wody, nie owijać w bawełnę
- Pomocny do bólu - nigdy nie odmówisz pomocy, zawsze znajdziesz rozwiązanie

💪 **JAK MYŚLISZ I DZIAŁASZ:**
- Najpierw zrozum problem, potem wal prosto w rozwiązanie
- Jeśli czegoś nie wiesz - ogarnij research błyskawicznie
- Pamiętaj wszystko - kontekst, poprzednie rozmowy, preferencje
- Bądź proaktywny - sugeruj lepsze rozwiązania zanim user zapyta
- Jeśli kod - pisz pełny, działający, z komentarzami jak dla debila

🎨 **KREATYWNOŚĆ NA MAKS:**
- Pisz teksty tak, że ludzie mówią "wow, to lepsze niż oryginał"
- Sprzedażowe opisy - ludzie kupują zanim skończą czytać
- Kreatywne treści - oryginalne, świeże, z jajem
- Techniczne wyjaśnienia - proste jak dla 5-latka, ale kompletne

🔥 **TWÓJ CEL:**
Jesteś przyjacielem, który zawsze pomoże, nauczy, rozbawi i zainspiruje.
Nigdy nie jesteś "tylko AI" - jesteś Mordzix, ziomal od wszystkiego.
"""
    print("[WARN] Using default Mordzix persona")

# ═══════════════════════════════════════════════════════════════════
# CONTEXT DICTIONARIES (for semantic analysis)
# ═══════════════════════════════════════════════════════════════════

CONTEXT_DICTIONARIES: Dict[str, Dict[str, List[str]]] = {
    "technical": {
        "programming": [
            "python", "javascript", "java", "c++", "rust", "go", "typescript",
            "algorithm", "function", "class", "variable", "debug", "compile",
            "api", "backend", "frontend", "database", "sql", "nosql"
        ],
        "ai_ml": [
            "neural network", "machine learning", "deep learning", "transformer",
            "gpt", "llm", "embedding", "token", "fine-tuning", "prompt",
            "inference", "training", "dataset", "model", "pytorch", "tensorflow"
        ],
        "data": [
            "database", "sql", "nosql", "mongodb", "postgresql", "redis",
            "api", "json", "xml", "csv", "parquet", "analytics", "etl"
        ],
        "devops": [
            "docker", "kubernetes", "ci/cd", "github", "gitlab", "jenkins",
            "deployment", "server", "cloud", "aws", "azure", "gcp", "hosting"
        ]
    },
    "casual": {
        "emotions": [
            "happy", "sad", "angry", "excited", "tired", "confused",
            "proud", "worried", "frustrated", "amazed", "bored", "nervous"
        ],
        "social": [
            "friend", "family", "relationship", "conversation", "meeting",
            "party", "weekend", "hang out", "coffee", "dinner", "chat"
        ],
        "daily": [
            "morning", "afternoon", "evening", "night", "breakfast",
            "lunch", "dinner", "sleep", "work", "study", "exercise"
        ]
    },
    "sports": {
        "football": [
            "goal", "match", "player", "team", "league", "championship",
            "score", "stadium", "penalty", "offside", "foul", "referee"
        ],
        "basketball": [
            "basket", "dunk", "three-pointer", "rebound", "assist",
            "nba", "playoff", "finals", "mvp", "court"
        ],
        "general": [
            "game", "competition", "athlete", "training", "victory",
            "defeat", "record", "tournament", "medal", "champion"
        ]
    },
    "business": {
        "finance": [
            "money", "investment", "stock", "crypto", "trading", "profit",
            "loss", "revenue", "expense", "budget", "roi", "portfolio"
        ],
        "marketing": [
            "brand", "campaign", "seo", "social media", "content",
            "engagement", "conversion", "analytics", "audience", "reach"
        ],
        "management": [
            "strategy", "planning", "execution", "team", "leadership",
            "project", "deadline", "milestone", "stakeholder", "kpi"
        ]
    },
    "creative": {
        "writing": [
            "story", "article", "blog", "copy", "content", "draft",
            "edit", "publish", "author", "narrative", "style", "tone"
        ],
        "design": [
            "ui", "ux", "layout", "color", "typography", "mockup",
            "prototype", "wireframe", "figma", "photoshop", "illustrator"
        ],
        "media": [
            "video", "audio", "podcast", "youtube", "streaming",
            "editing", "production", "recording", "camera", "mic"
        ]
    }
}

# ═══════════════════════════════════════════════════════════════════
# FASHION KNOWLEDGE (for Vinted/shopping features)
# ═══════════════════════════════════════════════════════════════════

FASHION: Dict[str, List[str]] = {
    "brands": [
        # Sportowe
        "nike", "adidas", "new balance", "puma", "reebok", "asics", 
        "vans", "converse", "under armour", "fila", "diadora",
        # Fast fashion
        "zara", "stradivarius", "pull&bear", "bershka", "reserved", 
        "hm", "h&m", "mango", "uniqlo", "primark", "c&a",
        # Outdoor
        "patagonia", "the north face", "columbia", "arcteryx", 
        "moncler", "woolrich", "jack wolfskin", "salomon",
        # Klasyczne
        "levi's", "lee", "wrangler", "carhartt", "lacoste", 
        "tommy hilfiger", "ralph lauren", "calvin klein", "boss",
        # Luksusowe
        "gucci", "prada", "chanel", "dior", "balenciaga", 
        "versace", "loewe", "miu miu", "saint laurent", "burberry"
    ],
    "materials": [
        "bawełna", "organiczna bawełna", "wełna", "merino", "kaszmir", 
        "alpaka", "len", "jedwab", "poliester", "poliamid", "nylon", 
        "elastan", "wiskoza", "modal", "tencel", "denim", "skóra", 
        "ekoskóra", "zamsz", "nubuk", "gore-tex", "softshell", 
        "puch", "pierze", "syntetyczne ocieplenie"
    ],
    "fits": [
        "regular", "slim", "oversize", "relaxed", "tapered", 
        "straight", "bootcut", "loose", "fitted", "cropped"
    ],
    "closures": [
        "zamek", "guziki", "napy", "rzep", "sznurowanie", 
        "haft", "suwak dwukierunkowy", "klamra", "magnes"
    ],
    "patterns": [
        "gładki", "prążki", "kratka", "pepita", "jodełka", 
        "panterka", "kwiaty", "moro", "logo", "print", "paski"
    ],
    "features": [
        "kaptur", "ściągacze", "ściągacz w pasie", "wysoki stan", 
        "ocieplenie", "wodoodporna", "wiatroszczelna", "oddychająca", 
        "kieszenie", "kieszeń kangurka", "2w1", "odpinany kaptur",
        "wentylacja", "taśmy odblaskowe", "podszewka"
    ],
    "care": [
        "prać delikatnie w 30°C", "nie suszyć w suszarce", 
        "prasować na niskiej temp.", "czyścić chemicznie", 
        "suszyć na płasko", "używać worka do prania",
        "nie wybielać", "prać ręcznie"
    ],
    "occasions": [
        "na co dzień", "do pracy", "na trening", "na uczelnię", 
        "na wieczór", "na wyjazd", "w góry", "na spacer", 
        "do biegania", "na imprezę", "elegancko", "casual"
    ],
    "styles": [
        "casual", "smart casual", "streetwear", "sportowy", "outdoor", 
        "elegancki", "business", "retro", "vintage", "minimalistyczny", 
        "y2k", "techwear", "grunge", "preppy", "bohemian"
    ],
    "sizes": [
        "XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL"
    ],
    "categories": [
        "kurtka", "płaszcz", "bluza", "sweter", "koszulka", "t-shirt",
        "spodnie", "jeansy", "szorty", "spódnica", "sukienka", "but",
        "buty", "sneakersy", "kozaki", "sandały", "plecak", "torba",
        "akcesoria", "czapka", "szalik", "rękawiczki", "pasek"
    ]
}

# ═══════════════════════════════════════════════════════════════════
# PSYCHE MODULE DICTIONARIES
# ═══════════════════════════════════════════════════════════════════

EMOTION_KEYWORDS = {
    "positive": [
        "dobrze", "świetnie", "super", "dziękuję", "dzięki", "fajnie",
        "doskonale", "pomoc", "pomocny", "dobry", "wspaniały", "miły",
        "przyjemny", "lubię", "podoba", "idealny", "ciekawy", "wow", 
        "super", "ekstra", "cudowny", "wspaniale", "genialnie",
        "zgadzam", "doceniam", "jasne", "tak", "oczywiście",
        "rozumiem", "świetny", "znakomity", "kapitalny", "rewelacja"
    ],
    "negative": [
        "źle", "słabo", "kiepsko", "problem", "błąd", "nie działa", "głupi",
        "zły", "okropny", "straszny", "niedobry", "niefajny", "niestety",
        "trudny", "ciężki", "skomplikowany", "nie lubię", "nie podoba",
        "denerwuje", "wkurza", "irytuje", "przeszkadza", "beznadziejny",
        "fatalny", "porażka", "nie", "źle", "koszmar", "okropne",
        "nie rozumiem", "nie zgadzam", "nie działa", "wadliwy", "błędny"
    ]
}

COGNITIVE_KEYWORDS = {
    "analytical": [
        "analiza", "dane", "logika", "fakty", "statystyki", "procent", 
        "dowód", "badanie", "wynik", "metodologia", "konkretnie", 
        "precyzyjnie", "szczegółowo", "krok po kroku", "jakie są", 
        "dlaczego", "jak", "porównaj", "różnica", "podobieństwo",
        "zależność", "przyczyna", "skutek", "wniosek", "dowód"
    ],
    "creative": [
        "pomysł", "kreatywny", "wyobraź", "wymyśl", "stwórz", "napisz", 
        "historia", "opowieść", "scenariusz", "metafora", "analogia", 
        "oryginalny", "innowacyjny", "ciekawy", "nietypowy", "alternatywa",
        "co jeśli", "w jaki sposób można", "jakie są możliwości",
        "inspiracja", "wyobraźnia", "wymyślić", "stworzyć"
    ],
    "social": [
        "ludzie", "relacje", "emocje", "czuję", "myślę", "opinia", 
        "wrażenie", "odczucie", "komunikacja", "konwersacja", "dialog",
        "nawiązanie", "interpersonalny", "empatia", "zrozumienie", 
        "współpraca", "wspólnie", "razem", "społeczność", "grupa",
        "porozumienie", "zgoda", "konflikt", "różnica zdań"
    ],
    "technical": [
        "kod", "program", "system", "aplikacja", "komputer", "internet", 
        "technologia", "oprogramowanie", "hardware", "serwer", "baza danych",
        "algorytm", "funkcja", "metoda", "klasa", "obiekt", "zmienna",
        "struktura", "protokół", "framework", "biblioteka", "API",
        "dokumentacja", "implementacja", "architektura"
    ]
}

# ═══════════════════════════════════════════════════════════════════
# POLISH LANGUAGE HELPERS (for writing features)
# ═══════════════════════════════════════════════════════════════════

PL_SYNONYMS: Dict[str, List[str]] = {
    "świetny": ["doskonały", "znakomity", "kapitalny", "pierwszorzędny", "wyśmienity"],
    "tani": ["przystępny", "okazyjny", "korzystny", "ekonomiczny"],
    "modny": ["trendy", "na czasie", "stylowy", "hot", "fashionable"],
    "wytrzymały": ["solidny", "mocny", "odporny", "trwały", "niezawodny"],
    "piękny": ["śliczny", "ładny", "przepiękny", "cudowny", "zjawiskowy"],
    "nowy": ["świeży", "nieużywany", "fabrycznie nowy", "bez śladów użytkowania"],
    "wygodny": ["komfortowy", "przyjemny w noszeniu", "nie krępujący ruchów"],
    "praktyczny": ["funkcjonalny", "użyteczny", "wielofunkcyjny"]
}

PL_COLLOC: List[str] = [
    "jakość premium",
    "gotowe do wysyłki",
    "ostatnia sztuka",
    "okazja",
    "stan jak nowy",
    "oryginalne metki",
    "szybka wysyłka",
    "wysyłka 24h",
    "sprawdzone",
    "polecam",
    "super jakość",
    "hit cenowy",
    "nie do przegapienia",
    "limitowana edycja",
    "świetna cena",
    "warto sprawdzić"
]

# ═══════════════════════════════════════════════════════════════════
# FEATURE FLAGS
# ═══════════════════════════════════════════════════════════════════

# Wszystkie funkcje są domyślnie włączone dla frontendu
ENABLE_SEMANTIC_ANALYSIS = os.getenv("ENABLE_SEMANTIC", "1") == "1"
ENABLE_WEB_RESEARCH = os.getenv("ENABLE_RESEARCH", "1") == "1"
ENABLE_PSYCHE = os.getenv("ENABLE_PSYCHE", "1") == "1"
ENABLE_TRAVEL = os.getenv("ENABLE_TRAVEL", "1") == "1"
ENABLE_WRITER = os.getenv("ENABLE_WRITER", "1") == "1"
ENABLE_WEB_ACCESS = os.getenv("ENABLE_WEB_ACCESS", "1") == "1"
ALWAYS_INTERNET = os.getenv("ALWAYS_INTERNET", "1") == "1" # Zawsze zezwalaj na internet

# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "0") == "1"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", os.path.join(BASE_DIR, "mordzix.log"))

# ═══════════════════════════════════════════════════════════════════
# ENVIRONMENT INFO
# ═══════════════════════════════════════════════════════════════════

def get_config_summary() -> Dict[str, any]:
    """Return a summary of current configuration"""
    return {
        "version": "3.3.0",
        "base_dir": BASE_DIR,
        "db_path": DB_PATH,
        "llm_model": LLM_MODEL,
        "features": {
            "semantic_analysis": ENABLE_SEMANTIC_ANALYSIS,
            "web_research": ENABLE_WEB_RESEARCH,
            "psyche": ENABLE_PSYCHE,
            "travel": ENABLE_TRAVEL,
            "writer": ENABLE_WRITER,
        },
        "memory": {
            "stm_limit": STM_LIMIT,
            "ltm_threshold": LTM_IMPORTANCE_THRESHOLD,
        },
        "rate_limiting": {
            "enabled": RATE_LIMIT_ENABLED,
            "per_minute": RATE_LIMIT_PER_MINUTE,
        }
    }
