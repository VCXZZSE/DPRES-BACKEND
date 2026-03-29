# DPRES Backend (FastAPI + PostgreSQL)

This is the backend starter scaffold for DPRES authentication and institution-domain validation.

## 1) Setup

```bash
cd dpres-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your PostgreSQL credentials.

## 2) Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:
- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/auth/ping`

## Production Deployment Notes

This backend is a long-running FastAPI service and is typically deployed to Render, Railway, Fly.io, or a VM/container host.

Set production env values:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`
- `FRONTEND_ORIGINS` (must include your Vercel frontend URL)

Example:

```env
FRONTEND_ORIGINS=https://your-frontend-app.vercel.app
```

Then set frontend Vercel env:

```env
VITE_AUTH_API_URL=https://your-backend-domain/api/auth
```

### SDMA Admin Login

Use `POST /api/auth/login-sdma-admin` with:

```json
{
  "email": "admin@sdma.gov.in",
  "password": "your-seeded-admin-password"
}
```

Credentials are validated against the `users` table (role must be `sdma_admin`).

Seed SDMA admin user (one-time):

```bash
PYTHONPATH=. ./venv/bin/python scripts/seed_sdma_admin.py --email admin@sdma.gov.in --name "SDMA Administrator"
```

## 2.1) Seed Developer Login (optional but recommended)

Run this once to create a persistent developer student account for sign-in testing:

```bash
PYTHONPATH=. ./venv/bin/python scripts/seed_developer_login.py
```

Default credentials:
- email: `developer@edu.in`
- password: `DevPass@123`

## 3) Initialize Alembic (first time)

```bash
alembic init alembic
```

Then edit:
- `alembic.ini` -> set `sqlalchemy.url` (or leave placeholder)
- `alembic/env.py`:
  - import: `from app.database import Base`
  - import models module so metadata is loaded: `import app.models`
  - set: `target_metadata = Base.metadata`
  - set DB URL from environment if preferred.

## 4) Create first migration

```bash
alembic revision --autogenerate -m "create auth and institution tables"
alembic upgrade head
```

## Current Scaffold Files

- `app/core/config.py` -> environment settings
- `app/database.py` -> SQLAlchemy engine/session/base
- `app/models.py` -> institutions/users/sessions/reset/verification models
- `app/main.py` -> FastAPI app + CORS + router wiring
- `app/routes/auth.py` -> auth route placeholder

## Next Build Step (Phase 3/4)

Implement:
1. `security.py` (password hashing + JWT)
2. domain validation service (email domain in institution.allowed_domains)
3. routes:
   - `POST /api/auth/register-student`
   - `POST /api/auth/login-student`
   - `POST /api/auth/forgot-password`
   - `POST /api/auth/reset-password`
   - `GET /api/auth/me`
