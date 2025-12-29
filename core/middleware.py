#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Middleware Module - Cache & Rate Limiting
"""

import time
import hashlib
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

from .config import *
from .helpers import log_info, log_warning
from .metrics import (
    record_llm_cache_hit,
    record_llm_cache_miss,
    update_llm_cache_size,
)

# ═══════════════════════════════════════════════════════════════════
# CACHE CLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 1000

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class SimpleCache:
    """Prosty cache w pamięci z TTL"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.stats = CacheStats()
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                return None

            entry = self.cache[key]
            if time.time() - entry['timestamp'] > self.ttl:
                del self.cache[key]
                self.stats.misses += 1
                return None

            self.stats.hits += 1
            return entry['value']

    def put(self, key: str, value: Any) -> None:
        with self.lock:
            now = time.time()

            # Usuń stare wpisy jeśli cache pełny
            if len(self.cache) >= self.max_size:
                oldest_keys = sorted(
                    self.cache.keys(),
                    key=lambda k: self.cache[k]['timestamp']
                )[:100]  # usuń 100 najstarszych
                for old_key in oldest_keys:
                    del self.cache[old_key]

            self.cache[key] = {
                'value': value,
                'timestamp': now
            }
            self.stats.size = len(self.cache)

    def invalidate(self) -> None:
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'hit_rate': self.stats.hit_rate,
                'size': self.stats.size,
                'max_size': self.max_size
            }

class LLMCACHE(SimpleCache):
    """Cache dla odpowiedzi LLM"""

    def __init__(self):
        super().__init__(max_size=1000, ttl=7200)  # 2h TTL dla LLM

    def make_key(self, messages: list, **kwargs) -> str:
        """Utwórz klucz cache na podstawie wiadomości i parametrów"""
        content = json.dumps({
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 1200)
        }, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        value = super().get(key)
        if value is not None:
            record_llm_cache_hit()
        else:
            record_llm_cache_miss()
        return value

    def put(self, key: str, value: Any) -> None:
        super().put(key, value)
        update_llm_cache_size(len(self.cache))

    def invalidate(self) -> None:
        super().invalidate()
        update_llm_cache_size(0)

class SearchCache(SimpleCache):
    """Cache dla wyników wyszukiwania"""

    def __init__(self):
        super().__init__(max_size=500, ttl=3600)  # 1h TTL dla search

    def make_key(self, query: str, engine: str = 'duckduckgo') -> str:
        """Utwórz klucz cache dla wyszukiwania"""
        content = f"{query}:{engine}".lower()
        return hashlib.md5(content.encode()).hexdigest()

class GeneralCache(SimpleCache):
    """Ogólny cache dla różnych danych"""

    def __init__(self):
        super().__init__(max_size=200, ttl=1800)  # 30min TTL

# ═══════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RateLimitEntry:
    count: int = 0
    window_start: float = 0.0

class RateLimiter:
    """Rate limiter oparty na sliding window"""

    def __init__(self):
        self.limits = {
            'default': {'limit': 160, 'window': 60},  # 160/min
            'chat': {'limit': 100, 'window': 60},     # 100/min dla chat
            'search': {'limit': 50, 'window': 60},    # 50/min dla search
            'admin': {'limit': 30, 'window': 60},     # 30/min dla admin
        }
        self.requests: Dict[str, RateLimitEntry] = {}
        self.lock = threading.Lock()

    def is_allowed(self, key: str, endpoint_type: str = 'default') -> bool:
        """Sprawdź czy request jest dozwolony"""
        with self.lock:
            now = time.time()

            # Pobierz konfigurację dla typu endpointu
            config = self.limits.get(endpoint_type, self.limits['default'])
            limit = config['limit']
            window = config['window']

            # Wyczyść stare wpisy
            to_remove = []
            for req_key, entry in self.requests.items():
                if now - entry.window_start > window:
                    to_remove.append(req_key)

            for req_key in to_remove:
                del self.requests[req_key]

            # Sprawdź aktualne użycie
            if key not in self.requests:
                self.requests[key] = RateLimitEntry(count=1, window_start=now)
                return True

            entry = self.requests[key]

            # Jeśli okno czasowe się skończyło, resetuj
            if now - entry.window_start > window:
                entry.count = 1
                entry.window_start = now
                return True

            # Sprawdź limit
            if entry.count >= limit:
                return False

            entry.count += 1
            return True

    def get_usage(self, key: str, endpoint_type: str = 'default') -> Dict[str, Any]:
        """Pobierz aktualne użycie dla użytkownika"""
        with self.lock:
            now = time.time()
            config = self.limits.get(endpoint_type, self.limits['default'])

            if key not in self.requests:
                return {
                    'count': 0,
                    'limit': config['limit'],
                    'window': config['window'],
                    'remaining': config['limit'],
                    'last_call_ts': 0
                }

            entry = self.requests[key]

            # Jeśli okno się skończyło, zwróć 0
            if now - entry.window_start > config['window']:
                return {
                    'count': 0,
                    'limit': config['limit'],
                    'window': config['window'],
                    'remaining': config['limit'],
                    'last_call_ts': 0
                }

            return {
                'count': entry.count,
                'limit': config['limit'],
                'window': config['window'],
                'remaining': max(0, config['limit'] - entry.count),
                'last_call_ts': entry.window_start
            }

# ═══════════════════════════════════════════════════════════════════
# GLOBAL INSTANCES
# ═══════════════════════════════════════════════════════════════════

# Inicjalizuj globalne instancje
llm_cache = LLMCACHE()
search_cache = SearchCache()
general_cache = GeneralCache()
rate_limiter = RateLimiter()

log_info("Middleware initialized", "MIDDLEWARE")
