#!/bin/sh
# Запуск FastAPI на alwaysdata (тип сайта «User program»).
# alwaysdata передаёт IP и PORT через переменные окружения.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VENV=${VENV:-"$ROOT/../venv"}

exec "$VENV/bin/uvicorn" main:app \
  --app-dir "$ROOT/fastapi_random_planets" \
  --host "${IP:-127.0.0.1}" \
  --port "${PORT:?PORT is not set}" \
  --root-path "${ROOT_PATH:-/fastapi}" \
  --proxy-headers
