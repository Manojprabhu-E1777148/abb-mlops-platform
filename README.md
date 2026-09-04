# ABB MLOps Platform

[![Backend Tests](https://github.com/Manojprabhu-E1777148/abb-mlops-platform/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Manojprabhu-E1777148/abb-mlops-platform/actions/workflows/backend-tests.yml)

## Project Overview

ABB MLOps Platform is a full-stack application for managing machine-learning projects and their operational workflows. It provides a FastAPI backend, a React web interface, and database-backed persistence for local and containerized development.

## Architecture

- **Backend:** Python 3.11+ FastAPI application with SQLModel, Alembic migrations, and pytest tests. GitHub Actions runs backend tests on Python 3.12.
- **Frontend:** React and TypeScript application built and served locally with Vite.
- **Database:** SQLite is the default local-development database. Docker Compose provisions PostgreSQL 16 for containerized development.
- **Docker:** Docker Compose starts the PostgreSQL database and FastAPI backend, waits for the database health check, and applies migrations before serving the API on port 8000.

## Repository Structure

```text
abb-mlops-platform/
├── .github/
│   └── workflows/
│       └── backend-tests.yml    # GitHub Actions backend test workflow
├── backend/
│   ├── alembic/                 # Database migration scripts
│   ├── app/                     # FastAPI application code
│   ├── tests/                   # Backend test suite
│   ├── Dockerfile               # Backend container image
│   ├── requirements.txt         # Python dependencies
│   └── test_main.py             # Pytest discovery sanity check
├── database/                    # Database-related resources
├── docs/                        # Project documentation
├── frontend/                    # React and Vite web application
│   ├── src/                     # Frontend source code
│   └── package.json             # Node.js scripts and dependencies
├── docker-compose.yml           # PostgreSQL and backend services
└── README.md
```

## Local Setup

### Prerequisites

- Python 3.11 or later (Python 3.12 is used in CI)
- Node.js and npm
- Docker Desktop for the PostgreSQL Compose workflow

### Backend

Create and activate a virtual environment, then install backend dependencies:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For SQLite local development, copy the environment template, set local secret values, apply migrations, and start the API:

```powershell
Copy-Item .env.example .env
alembic upgrade head
python -m app.seed_demo_users
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

### Frontend

In a separate terminal, install dependencies and start the Vite development server:

```powershell
cd frontend
npm install
npm run dev
```

### Docker Compose

To run PostgreSQL and the backend in containers, set a non-default JWT secret and start Compose from the repository root:

```powershell
$env:JWT_SECRET_KEY = "replace-with-a-long-random-secret"
docker compose up --build
```

Stop the services with:

```powershell
docker compose down
```

## Running Tests

Backend tests use isolated temporary SQLite databases and do not require Docker or PostgreSQL:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

## CI/CD Status

The **Backend Tests** GitHub Actions workflow runs on pushes and pull requests targeting `main`. It checks out the repository, sets up Python 3.12, installs `backend/requirements.txt`, and runs the pytest suite from the `backend` directory.

Use the status badge above to view the latest workflow run and logs.
