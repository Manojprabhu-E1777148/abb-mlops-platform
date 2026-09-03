# ABB MLOps Platform API

The backend uses SQLite by default for local development. Application data is saved to `backend/projects.db`; schema changes are managed by Alembic. Tests use isolated temporary SQLite databases.

## Prerequisites

- Python 3.11 or later
- Docker Desktop for the PostgreSQL Compose workflow

## Install dependencies

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run locally with SQLite

Create `backend/.env` from `.env.example`, replace the JWT and demo-user password placeholders with local values, apply migrations, and start the API. Leave `DATABASE_URL` unset to use `backend/projects.db`:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
alembic upgrade head
python -m app.seed_demo_users
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`. Verify the service with `Invoke-WebRequest http://127.0.0.1:8000/api/health`. `DATABASE_URL`, `LOG_LEVEL`, and `ENVIRONMENT` are read from the environment or `backend/.env`. LocalDB is intended for Windows local development only, not production deployment.

## Run PostgreSQL with Docker Compose

From the repository root, provide a JWT secret and start the services:

```powershell
$env:JWT_SECRET_KEY = "replace-with-a-long-random-secret"
docker compose up --build
```

Compose starts a private PostgreSQL service, waits for its health check, runs `alembic upgrade head`, and exposes the FastAPI service at `http://localhost:8000`. PostgreSQL data persists in the `postgres_data` named volume.

To use different local PostgreSQL credentials, set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` before running Compose. The backend receives its PostgreSQL `DATABASE_URL` explicitly from Compose.

## Run migrations

For the default SQLite database:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Alembic reads `DATABASE_URL` through the application settings. Leave it unset for the default SQLite database, or set it to another supported connection URL. Do not commit `backend/.env`.

## Run tests

Tests use an isolated temporary SQLite database and do not require LocalDB or Docker:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

## Stop services

```powershell
docker compose down
```

To also remove the PostgreSQL data volume, run `docker compose down --volumes`.
