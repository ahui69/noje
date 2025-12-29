"""
System Stats - Moduł do zbierania statystyk systemowych
======================================================

Moduł zawiera funkcje do:
- Zbierania statystyk systemu (CPU, pamięć, dysk)
- Monitorowania procesów
- Analizy bazy danych
- Śledzenia stanu psychiki AI

Główne funkcje:
- system_stats(): Zbiera kompleksowe statystyki systemu
"""

import os
import time
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def system_stats() -> Dict[str, Any]:
    """
    Zbiera kompleksowe statystyki systemowe

    Returns:
        Dict ze statystykami systemu, procesu, bazy danych i psychiki
    """
    stats = {
        "uptime_s": int(time.time()),
        "timestamp": time.time(),
    }

    # Statystyki procesu
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            stats["process"] = {
                "pid": os.getpid(),
                "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "memory_percent": round(process.memory_percent(), 2),
                "threads": process.num_threads(),
                "status": process.status(),
            }
        except Exception as e:
            stats["process"] = {"error": str(e)}
    else:
        stats["process"] = {"error": "psutil not available"}

    # Statystyki systemu
    if PSUTIL_AVAILABLE:
        try:
            stats["system"] = {
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_percent": round(psutil.cpu_percent(interval=0.1), 2),
                "memory_total_gb": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                "memory_available_gb": round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2),
                "memory_used_gb": round(psutil.virtual_memory().used / 1024 / 1024 / 1024, 2),
                "memory_percent": round(psutil.virtual_memory().percent, 2),
                "disk_total_gb": round(psutil.disk_usage('/').total / 1024 / 1024 / 1024, 2) if os.name != 'nt' else round(psutil.disk_usage('C:').total / 1024 / 1024 / 1024, 2),
                "disk_free_gb": round(psutil.disk_usage('/').free / 1024 / 1024 / 1024, 2) if os.name != 'nt' else round(psutil.disk_usage('C:').free / 1024 / 1024 / 1024, 2),
                "disk_percent": round(psutil.disk_usage('/').percent, 2) if os.name != 'nt' else round(psutil.disk_usage('C:').percent, 2),
            }
        except Exception as e:
            stats["system"] = {"error": str(e)}
    else:
        stats["system"] = {"error": "psutil not available"}

    # Próba dodania statystyk bazy danych (jeśli dostępne)
    try:
        # Importujemy funkcje z core.memory jeśli są dostępne
        from core.memory import _db
        conn = _db()
        c = conn.cursor()

        # Podstawowe statystyki bazy danych
        db_stats = {
            "path": getattr(conn, 'db_path', 'unknown'),
            "size_mb": 0,
        }

        # Próba pobrania rozmiaru pliku bazy danych
        try:
            if hasattr(conn, 'db_path') and conn.db_path:
                db_stats["size_mb"] = round(os.path.getsize(conn.db_path) / 1024 / 1024, 2)
        except:
            pass

        # Próba pobrania liczby rekordów w tabelach
        try:
            tables = ["facts", "memory", "memory_long", "psy_episode", "psy_reflection", "docs"]
            for table in tables:
                try:
                    count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    db_stats[f"{table}_count"] = count
                except:
                    pass
        except:
            pass

        conn.close()
        stats["database"] = db_stats

    except Exception as e:
        stats["database"] = {"error": str(e)}

    # Próba dodania statystyk psychiki (jeśli dostępne)
    try:
        from core.memory import psy_get
        psyche = psy_get()
        stats["psyche"] = {
            "mood": round(psyche.get("mood", 0.0), 2),
            "energy": round(psyche.get("energy", 0.6), 2),
            "focus": round(psyche.get("focus", 0.6), 2),
            "style": psyche.get("style", "neutral"),
            "last_updated": psyche.get("updated", time.time()),
        }
    except Exception as e:
        stats["psyche"] = {"error": str(e)}

    # Dodatkowe informacje o środowisku
    stats["environment"] = {
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "platform": os.sys.platform,
        "os_name": os.name,
        "working_directory": os.getcwd(),
    }

    return stats

def init_monitor() -> Dict[str, Any]:
    """
    Inicjalizuje monitoring systemu

    Returns:
        Status inicjalizacji
    """
    return {
        "ok": True,
        "message": "System monitoring initialized",
        "psutil_available": PSUTIL_AVAILABLE,
        "timestamp": time.time(),
    }

def record_api_call(endpoint: str, method: str = "GET", duration_ms: float = 0.0, status_code: int = 200) -> None:
    """
    Rejestruje wywołanie API dla celów monitorowania

    Args:
        endpoint: Ścieżka endpointu
        method: Metoda HTTP
        duration_ms: Czas wykonania w milisekundach
        status_code: Kod statusu HTTP
    """
    # Tutaj można dodać logowanie do bazy danych lub pliku
    # Na razie tylko placeholder
    pass

# Funkcje kompatybilności wstecznej
def get_system_stats() -> Dict[str, Any]:
    """Alias dla system_stats"""
    return system_stats()

def get_process_stats() -> Dict[str, Any]:
    """Zwraca tylko statystyki procesu"""
    stats = system_stats()
    return stats.get("process", {})

def get_memory_stats() -> Dict[str, Any]:
    """Zwraca tylko statystyki pamięci"""
    stats = system_stats()
    return {
        "system_memory": stats.get("system", {}),
        "process_memory": stats.get("process", {}),
    }