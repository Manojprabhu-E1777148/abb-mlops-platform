# ABB MLOps Platform API

Initial FastAPI backend exposing a health endpoint.

## Prerequisites

- Python 3.11 or later

## Install dependencies

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the application

```powershell
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000` by default.

## Verify the health endpoint

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

The endpoint returns HTTP 200 with `status`, `service`, and a UTC ISO 8601 `timestampUtc`.
