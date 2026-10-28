# OPSYRO architecture

## Application boundaries

- `frontend/` contains the Next.js App Router public site, demo, and authenticated creator workspace. Typed API calls and the reconnecting WebSocket hook live in `frontend/lib/`.
- `backend/apps/accounts/` uses Django session authentication with CSRF protection.
- `backend/apps/sessions/` owns creator sessions, lifecycle transitions, and optional Twitch channel IDs. Creator queries and WebSocket subscriptions are owner-scoped.
- `backend/apps/signals/` validates pseudonymous per-tab keys, idempotency, intent, questions, and normalized 0–1 coordinates. Creator serializers omit participant and idempotency IDs.
- `backend/apps/questions/` groups similar question wording within a media region using normalized tokens and a small synonym map; it does not claim semantic AI clustering.
- `backend/apps/responses/` stores creator drafts and published answers. Only drafts can be edited.
- `backend/apps/feedback/` stores one helpfulness signal per participant and response. Public endpoints return published replies and aggregate counts.
- `backend/apps/experiments/` stores hypothesis, planned change, owned session links, lifecycle, and outcome notes for creator learning logs.
- `backend/apps/twitch/` verifies Extension JWT signatures, expiry, role, and channel claims using the server-side shared secret. It resolves only live sessions whose channel ID matches the signed claim.
- `twitch-extension/` is a compact TypeScript iframe viewer app, separate from Next.js. Its Extension secret remains on the backend.
- PostgreSQL persists product data. Redis can back Channels and the shared throttle cache. Without `REDIS_URL`, local development uses in-memory Channels and a process-local cache.
- `/demo` is an isolated browser-only sample. `/view/{share_token}` is the backend-connected local audience preview. The Twitch Extension uses Twitch-issued JWT verification and is a separate integration boundary.

## Design tokens

The light theme uses a warm neutral canvas (`#F7F7F5`), white surfaces, ink text (`#171923`), muted slate (`#737784`), deep indigo-violet (`#5146D8`), periwinkle (`#A9A2FF`), and amber (`#F0B45B`). Semantic status colors are defined in `frontend/app/globals.css`; Tailwind names map to CSS variables in `frontend/tailwind.config.ts`. Spacing follows a 4px unit.

## API and realtime

Current endpoints include `/api/health/`, `/api/auth/`, owner-scoped `/api/sessions/`, `/api/responses/`, and `/api/experiments/`, rate-limited `/api/signals/` and `/api/feedback/`, Twitch Extension session resolution at `/api/twitch/extension/session/`, and a session WebSocket at `/ws/sessions/{id}/`.

Signal and feedback writes persist before notifications are broadcast. WebSockets authorize the Django session cookie and creator ownership. Events include `signal.created`, `cluster.updated`, `response.created`, `feedback.updated`, and `session.status_changed`; payloads contain no participant keys. Attention-map cells use 10×10 normalized bins with text summaries for nonvisual access.

Question grouping is deterministic and scoped to the selected region. Twitch OAuth, Helix metadata, EventSub, Extension secret rotation overlap, console registration/review, and production deployment remain unconfigured. See `docs/twitch-extension.md` and `docs/deployment.md`.
