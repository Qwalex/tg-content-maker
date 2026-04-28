# TG Content Maker

Production-oriented implementation of Telegram multilingual copier:

- FastAPI backend with PostgreSQL persistence
- RQ worker with Redis queue for async pipeline jobs
- Next.js 16 admin frontend
- Alert webhook integration (`https://notify.qwalex.one/`)

## Required services

- PostgreSQL
- Redis

Quick start (all infra + API + worker):

```bash
docker compose up -d
```

## Environment

Copy `backend/.env.example` to `backend/.env` and fill values:

- `DATABASE_URL=postgresql+psycopg://...`
- `REDIS_URL=redis://...`
- `OPENROUTER_API_KEY=...`
- `TELEGRAM_API_ID=...`
- `TELEGRAM_API_HASH=...`
- `TELEGRAM_SESSION_STRING=...` (if used by your Telegram client integration)
- `INTERNAL_INGEST_TOKEN=...` (required, used by `/api/internal/source-events`)
- `AUTO_CREATE_SCHEMA=false` (recommended in production; use migrations)
- `CORS_ORIGINS=http://localhost:3000,https://your-frontend.up.railway.app`

Do not commit real secrets. Rotate leaked keys immediately.

## Run backend locally

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run worker locally

```bash
cd backend
python -m app.worker
```

## Run frontend locally

```bash
cd frontend
npm install
npm run dev
```

Frontend-to-backend routing:

- Browser calls use `/backend/*` and are proxied by Next rewrites.
- Set `RAILWAY_PRIVATE_DOMAIN` in the frontend Railway service to the backend private domain so server-side requests use Railway private networking.
- Optional fallback for local/public access: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

## Core endpoints

- `POST /api/sessions`
- `GET /api/sessions/{id}/qr`
- `POST /api/sessions/{id}/2fa`
- `POST /api/copiers`
- `POST /api/copiers/{id}/targets`
- `POST /api/internal/source-events` (enqueue source message processing)
- `GET /api/logs`
- `GET /api/jobs`
