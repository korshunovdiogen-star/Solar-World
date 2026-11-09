#!/bin/sh
# alwaysdata передаёт IP и PORT через переменные окружения.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENV=${VENV:-"$ROOT/../venv"}

echo "FastAPI start: ROOT=$ROOT VENV=$VENV IP=${IP:-} PORT=${PORT:-}"

exec "$VENV/bin/uvicorn" main:app \
  --app-dir "$ROOT/fastapi_random_planets" \
  --host "${IP:-${HOST:-0.0.0.0}}" \
  --port "${PORT:?PORT is not set}" \
  --root-path "${ROOT_PATH:-/fastapi}" \
  --proxy-headers
