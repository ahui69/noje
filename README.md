# noje

## Start backend (FastAPI)
1. Utwórz środowisko: `python3 -m venv .venv && source .venv/bin/activate`.
2. Zainstaluj zależności: `pip install --upgrade pip && pip install -r requirements.txt`.
3. Ustaw wymagane zmienne: minimum `LLM_API_KEY` (klucz do dostawcy LLM); opcjonalnie `REDIS_URL` jeśli używasz pamięci redisowej.
4. Upewnij się, że katalog `static/` istnieje (jest potrzebny do startu FastAPI; repo zawiera `static/README.md`).
5. Uruchom serwer: `uvicorn app:app --host 0.0.0.0 --port 8080` (dev dodaj `--reload`).
6. Sprawdź, co realnie się wczytało: `python audit_runtime_routes.py` (drukuje listę ładujących się routerów i pełny wykaz ścieżek).

## Gdzie jest pełny audyt
Kompletny raport i plan napraw znajdziesz w `AUDYT_MRD.md` w katalogu głównym repozytorium.
