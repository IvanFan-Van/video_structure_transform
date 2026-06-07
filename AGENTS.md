# AGENTS.md

## Repo structure — three independent packages (not a unified monorepo)

Each package has its own package manager and toolchain. There is no root workspace config, lockfile, or CI.

| Package | Dir | Package manager | Language | Key framework |
|---------|-----|-----------------|----------|---------------|
| backend | `backend/` | **uv** | Python 3.12 | FastAPI + SQLModel |
| frontend | `frontend/` | **pnpm** | TypeScript 5 | React 18 + Vite 5 |
| videos | `videos/` | **pnpm** | TypeScript 5 | Remotion 4 |

## Backend (Python)

### Run & develop

```bash
# Start the server on 127.0.0.1:8000
cd backend && uv run src/main.py

# Create .env from template (required for JWT + AI API)
cp .env.example .env
```

### Env vars (backend/.env)

- `API_KEY`, `MODEL`, `BASE_URL` — AI/LLM provider config
- `SECRET_KEY`, `ALGORITHM` (default HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30) — JWT

### Lint & test

```bash
cd backend
uv run ruff check .          # lint (rules: I, UP, E, F, W, C90)
uv run pytest tests/          # run all tests
uv run pytest tests/test_video.py  # run a single file
```

Tests require a sample video at `backend/tests/videos/1.mp4`. The conftest fixture skips if missing.

### Architecture (MVC)

```
src/
  main.py          FastAPI app, lifespan (creates DB tables), exception handlers
  database.py      SQLite engine (sqlite:///database.db), get_session generator
  deps.py          FastAPI dependencies (auth, asset ownership)
  schemas.py       Pydantic request models
  prompts.py       LLM prompt templates (~600 lines)
  utils.py         bcrypt + JWT helpers
  models/          SQLModel tables (User, Asset, UserOAuth)
  routers/         Route handlers (auth, pipeline, task, asset)
  services/        Business logic
  repositories/    Data layer
  tasks/           In-memory async task system (TaskRegistry, not Celery)
  lib/             Low-level: audio.py, video.py, schemas/ subpackage
```

### Key quirks

- **API response format** is custom JSend-like: `{status: "success"|"fail"|"error", data?|message?}` — not standard FastAPI defaults.
- **SQLite** database auto-created on startup (no migration tool). Delete `backend/database.db` to reset.
- **Tasks are in-memory only** (not persisted, no Celery/RQ). Lost on restart. Status streamed via SSE (`/task/{id}/stream`).
- **Storage** is local filesystem at `backend/storage/` (gitignored). Subdirs: `videos/`, `audios/`, `images/`.
- **Auth**: JWT via `python-jose` (HS256), bcrypt (12 rounds), `OAuth2PasswordBearer`.

## Frontend (React + Vite)

```bash
cd frontend
pnpm dev       # Vite dev server
pnpm build     # tsc && vite build
pnpm preview   # vite preview
```

- React 18, React Router v7, Zustand 5 for state
- SSE via `@microsoft/fetch-event-source` for real-time task progress

## Videos (Remotion)

```bash
cd videos
pnpm dev       # remotion studio
pnpm build     # remotion bundle
pnpm lint      # eslint src && tsc
```

- Remotion 4.0.470, React 19, Tailwind CSS 4
- Lint uses `@remotion/eslint-config-flat` + prettier 3.8.1

## VSCode

`.vscode/settings.json` points Python interpreter to `backend/.venv/Scripts/python.exe`.

## .gitignore

Only `.agents/` is gitignored at root. Backend has its own `.gitignore` for `storage/`, `database.db`, etc.
