# OPSYRO

OPSYRO is an audience intelligence product for making viewer curiosity visible and actionable. The repository now includes a public site, browser demo, authenticated creator workspace, persisted audience signals, question grouping, scoped realtime updates, creator responses and feedback, experiment tracking, and a standalone Twitch Extension viewer bundle with server-side JWT verification. Twitch account setup and public deployment are not configured, so the project does not claim a live Twitch integration or production deployment.

## Requirements

- Node.js 20+ and npm
- Python 3.11+ and pip
- Docker Desktop for local PostgreSQL and Redis, or compatible services already running

## Local setup

1. Copy `.env.example` to `.env`; values are development placeholders.
2. Copy `frontend/.env.example` to `frontend/.env.local` if you need to override API/WebSocket origins.
3. Start local services:

   ```powershell
   docker compose up -d postgres redis
   ```

4. Start Django in one terminal:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

5. Start Next.js in another terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Open `http://localhost:3000`. The API health endpoint is `http://localhost:8000/api/health/`.

## Product workflows

- Public site: `/`; isolated sample: `/demo`.
- Register and sign in: `/register`, `/sign-in`.
- Creator workspace: `/workspace`. Create a session, optionally set its numeric Twitch channel ID, start it, and open the details.
- For a live local session, use **Viewer preview** to submit a signal. Review attention and grouped questions, draft and publish a reply, then submit viewer feedback.
- Experiment log: `/workspace/experiments`. Record a hypothesis and change, link owned sessions, track planned/active/completed status, and save an outcome note.
- Twitch Extension: see [docs/twitch-extension.md](docs/twitch-extension.md). The project includes the viewer bundle and server-side signature/expiry verification, but needs a Twitch Extension secret and developer-console setup to run inside Twitch.

The browser preview and Twitch Extension keep a random per-tab participant key and do not submit a Twitch username. These are pseudonymous signals, not a guarantee of anonymity. Signals and feedback remain stored until database cleanup; account deletion and retention controls are not implemented.

## API and security

- Authentication: `/api/auth/` uses CSRF-protected Django sessions.
- Creator sessions: `/api/sessions/` exposes owner-scoped session lifecycle, attention, question groups, and summary endpoints.
- Audience signals: `POST /api/signals/` accepts a live session token, bounded normalized coordinates, intent, question text, and idempotency key; submissions are rate limited.
- Responses and feedback: `/api/responses/` manages owner-only drafts and publication; `/api/feedback/` accepts viewer helpfulness and exposes published replies with aggregate counts.
- Experiments: `/api/experiments/` stores owner-scoped learning logs linked only to the creator’s own sessions.
- Twitch: `/api/twitch/extension/session/` verifies the Extension JWT with the server secret and resolves a live session by channel ID. The browser never receives the secret.
- Creator WebSocket: `/ws/sessions/{id}/` requires the owner’s authenticated session cookie; event payloads omit participant keys.

PostgreSQL is the persistent source of truth. Redis can back Channels and shared throttling when `REDIS_URL` is set; without it, development uses process-local memory. Deployment setup is in [docs/deployment.md](docs/deployment.md). The Render Blueprint and Vercel config are templates requiring project-specific origins, account setup, and secret values.

`.env`, `frontend/.env.local`, virtual environments, `node_modules`, and build output are ignored by Git. Never put real credentials in example files.

## Checks

```powershell
cd frontend
npm run typecheck
npm run build
cd ..\backend
python manage.py check --settings=config.test_settings
python manage.py test apps.accounts apps.sessions apps.signals apps.responses apps.feedback apps.experiments apps.twitch --settings=config.test_settings
cd ..\twitch-extension
npm run build
```

Backend tests use in-memory SQLite; normal development uses PostgreSQL. See [docs/architecture.md](docs/architecture.md) for boundaries and design tokens.
