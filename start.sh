#!/usr/bin/env bash
# AURA-EAGLE unified start script
set -e

cd "$(dirname "$0")"

echo "▶ Building frontend…"
cd frontend && npm run build --silent
cd ..

echo "▶ Starting AURA-EAGLE on :5000"
exec python -m uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port 5000 \
  --workers 1 \
  --log-level warning
