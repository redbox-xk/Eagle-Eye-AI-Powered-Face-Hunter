---
name: AURA-EAGLE stack decisions
description: Key architectural decisions and quirks for the AURA-EAGLE project
---

# AURA-EAGLE Stack

## Services
- Backend: FastAPI on port 8000 (`python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`)
- Frontend: Vite/React on port 5000 (`cd frontend && npm run dev` — port set in vite.config.ts)
- Vite proxies `/api` and `/ws` to `http://localhost:8000`

## Database
- PostgreSQL via Replit managed DB; `DATABASE_URL` env var contains `?sslmode=require`
- asyncpg does NOT accept `sslmode` as a query param — must strip it from the URL and pass `ssl=ctx` via `connect_args`
- Fix is in `backend/core/database.py` → `_build_async_url()` strips the query string and `_ssl_required` flag passes a custom SSL context

## WebSocket
- ws.ts connects at module load; React listener must call `setConnected(ws.connected)` on mount to catch already-open connections (event fires before component mounts)

**Why:** asyncpg uses its own SSL negotiation and rejects SQLAlchemy-forwarded `sslmode` kwarg — discovered at first boot.
