# OPSYRO foundation

## Application boundaries

- `frontend/` is the Next.js App Router creator workspace. It owns presentation and will call the backend through an explicit API contract.
- `backend/` is the Django API foundation. PostgreSQL is configured as the persistent data store. Django Channels is installed; Redis is selected when `REDIS_URL` is supplied and the in-memory channel layer is used for local development otherwise.
- Twitch authorization, extension entry points, session workflows, and audience signal models are not implemented in Phase 1.

## Initial visual tokens

The light theme uses a warm neutral canvas (`#F7F7F5`), white surfaces, ink text (`#171923`), muted slate (`#737784`), deep indigo-violet (`#5146D8`), periwinkle (`#A9A2FF`), and amber (`#F0B45B`). Semantic success, warning, and destructive colors are defined alongside the palette in `frontend/app/globals.css`. Tailwind semantic color names map to those CSS variables in `frontend/tailwind.config.ts`.

Spacing is based on a 4px unit. Workspace layouts use larger increments for page sections and tighter increments for navigation and metadata. Border color is reserved for structural separation.

## API and realtime direction

The API currently exposes only `GET /api/health/`. Product endpoints will be added alongside their domain models and serializers. Any future Channels consumer must authenticate the creator, authorize access to the requested session, and publish only session-scoped payloads. Redis is a transport layer; PostgreSQL remains the source of truth.
