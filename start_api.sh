#!/usr/bin/env bash
set -euo pipefail

cd /root/mrd
mkdir -p /root/mrd/logs

PID="$(ss -ltnp 2>/dev/null | awk '/:8080/ {print $NF}' | head -n1 | sed -E 's/.*pid=([0-9]+).*/\1/')"
if [[ -n "${PID:-}" && "${PID}" =~ ^[0-9]+$ ]]; then
  kill -9 "$PID" || true
fi

set -a
source /root/mrd/.env
set +a

export PYTHONPATH="/root/mrd:${PYTHONPATH:-}"

nohup python3 -m uvicorn app:app --app-dir /root/mrd --host 0.0.0.0 --port 8080 > /root/mrd/logs/uvicorn.log 2>&1 &
disown

ok=0
for i in $(seq 1 60); do
  code="$(curl -sS --connect-timeout 0.2 --max-time 0.5 -o /tmp/health.json -w '%{http_code}' http://127.0.0.1:8080/health 2>/dev/null || true)"
  if [[ "$code" == "200" ]]; then
    ok=1
    break
  fi
  sleep 0.2
done

if [[ "$ok" != "1" ]]; then
  echo "[ERR] /health not ready"
  tail -n 200 /root/mrd/logs/uvicorn.log || true
  exit 1
fi

python3 - <<'PY'
import json
d=json.load(open("/tmp/health.json","r",encoding="utf-8"))
print("health:", d.get("status"), "version:", d.get("version"))
print("env flags:", d.get("env"))
PY
