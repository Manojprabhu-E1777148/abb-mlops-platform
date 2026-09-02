# ABB MLOps Platform API

The backend uses SQLite by default for local development and tests. Set `DATABASE_URL` to use PostgreSQL; production PostgreSQL schema changes are managed by Alembic.

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

Leave `DATABASE_URL` unset to use `backend/projects.db`. Set a JWT secret before starting the API:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
$env:JWT_SECRET_KEY = "replace-with-a-long-random-secret"
uvicorn app.main:app --reload
```

SQLite tables are created automatically at application startup. The API listens on `http://127.0.0.1:8000`.

## Run PostgreSQL with Docker Compose

From the repository root, provide a JWT secret and start the services:

```powershell
$env:JWT_SECRET_KEY = "replace-with-a-long-random-secret"
docker compose up --build
```

Compose starts a private PostgreSQL service, waits for its health check, runs `alembic upgrade head`, and exposes the FastAPI service at `http://localhost:8000`. PostgreSQL data persists in the `postgres_data` named volume.

To use different local PostgreSQL credentials, set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` before running Compose. The backend receives its PostgreSQL `DATABASE_URL` explicitly from Compose.

## Run migrations

For a PostgreSQL database available from the host, create `backend/.env` from `.env.example`, update its values, and run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Alembic reads `DATABASE_URL` through the application settings. Do not commit `backend/.env`.

## Run tests

Tests use an isolated temporary SQLite database and do not require Docker or PostgreSQL:

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
