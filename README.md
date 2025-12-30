# noje

## Start backend (FastAPI)
1. Utwórz środowisko: `python3 -m venv .venv && source .venv/bin/activate`.
2. Zainstaluj zależności: `pip install --upgrade pip && pip install -r requirements.txt`.
3. Ustaw wymagane zmienne: minimum `LLM_API_KEY` (klucz do dostawcy LLM); opcjonalnie `REDIS_URL` jeśli używasz pamięci redisowej.
4. Upewnij się, że katalog `static/` istnieje (jest potrzebny do startu FastAPI; repo zawiera `static/README.md`).
5. Uruchom serwer: `uvicorn app:app --host 0.0.0.0 --port 8080` (dev dodaj `--reload`).
6. Sprawdź, co realnie się wczytało: `python audit_runtime_routes.py` (drukuje listę ładujących się routerów i pełny wykaz ścieżek).
7. Endpointy `/health` (app) i `/health` z modułu Prometheus zwracają ten sam, spójny payload (status, wersja, ENV, metryki) – monitorowanie działa identycznie niezależnie od źródła.

### Szybki start (backend + build frontendu)
- Uruchom: `./start.sh` (tworzy `.venv`, instaluje zależności Pythona, buduje frontend Vite, startuje uvicorn na porcie 8080).
- Skrypt budując frontend ustawia `VITE_API_BASE=http://$HOST:$PORT`, więc UI i API domyślnie działają na tym samym porcie.
- Opcjonalne zmienne: `PORT` (domyślnie 8080), `HOST` (domyślnie 0.0.0.0), `SKIP_FRONTEND=1` (pomija budowę frontu, wymaga gotowego `frontend/dist`).
- Zmienne środowiskowe frontendu (odczytywane podczas buildu): `VITE_API_BASE` (adres backendu), `VITE_AUTH_TOKEN` (domyślny Bearer do UI), `VITE_DEFAULT_MODEL` (np. nazwę modelu z `/v1/models`), `VITE_STREAM_DEFAULT` (`true`/`false`), `VITE_SAVE_DRAFTS` (`true`/`false`).

## Nowy frontend (React + Vite)
1. Przejdź do `frontend/`.
2. Zainstaluj zależności: `npm install`.
3. Uruchom dev server: `npm run dev` (domyślnie `http://localhost:5173`).
4. Zaloguj się tokenem Bearer (`AUTH_TOKEN` z backendu) na `/login`, następnie korzystaj z `/app/chat` (SSE) i `/app/settings`.

### Kluczowe endpointy używane przez frontend
- `/api/chat/assistant` (POST) i `/api/chat/assistant/stream` (POST, SSE) – chat z historią.
- `/api/chat/sessions`, `/api/chat/sessions/{session_id}`, `/api/chat/sessions/{session_id}/title`, `/api/chat/sessions/{session_id}/delete` – zarządzanie sesjami.
- `/api/files/upload` + `/api/files/list` – upload i lista plików (Bearer wymagany).
- `/api/stt/transcribe`, `/api/tts/speak` – audio (opcjonalnie w UI, status w panelu).

## Gdzie jest pełny audyt
Kompletny raport i plan napraw znajdziesz w `AUDYT_MRD.md` w katalogu głównym repozytorium.
