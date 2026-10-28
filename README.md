# OPSYRO

OPSYRO is an audience intelligence product for making viewer curiosity visible and actionable. This repository is at **Phase 1: product foundation**. It currently contains the initial creator workspace shell and Django API configuration; sessions, authentication, Twitch, and signal collection are not implemented yet.

## Requirements

- Node.js 20 or newer and npm
- Python 3.11 or newer
- PostgreSQL 15 or newer
- Redis is optional for local development; the backend uses an in-memory Channels layer when `REDIS_URL` is unset

## Local setup

1. Copy `.env.example` to `.env` and set a local Django secret and PostgreSQL credentials.
2. Create a PostgreSQL database matching the configured `POSTGRES_DB` value.
3. Start the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

4. In another terminal, start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

The workspace runs at `http://localhost:3000`; the API health endpoint is `http://127.0.0.1:8000/api/health/`.

## Configuration

Environment variables are listed in `.env.example`. `.env` is ignored by Git. `DJANGO_SECRET_KEY` has a development fallback for initial setup; production must provide a unique secret and set `DJANGO_DEBUG=false`. Configure Redis with `REDIS_URL` when testing a multi-process Channels deployment.

## Foundation checks

```powershell
cd frontend
npm run typecheck
npm run build
cd ..\backend
python manage.py check
```

See [docs/architecture.md](docs/architecture.md) for the initial architecture and design tokens.
