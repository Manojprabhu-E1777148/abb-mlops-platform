# ABB MLOps Platform Instructions

## Technology Stack
- Python 3.11+
- FastAPI
- SQLAlchemy
- pyodbc
- SQL Server LocalDB
- Angular
- Angular Material
- TypeScript
- Pytest

## Project Structure
- Backend: backend/
- Frontend: frontend/mlops-ui/
- Database scripts: database/
- Documentation: docs/

## Development Rules
- Keep API routers thin.
- Put business rules in service classes.
- Use Pydantic schemas for API request and response validation.
- Use SQLAlchemy for database queries.
- Use UTC timestamps.
- Do not hard-code credentials or connection strings.
- Read configuration from environment variables.
- Add tests for important MLOps workflows.
- Do not change unrelated files.
- Run relevant tests after implementation.

## API Error Format
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}

## MLOps Rules
1. Model names must be unique.
2. Version numbers must be unique within one model.
3. New versions begin with PENDING approval and DRAFT lifecycle.
4. Only APPROVED versions can deploy to PRODUCTION.
5. A FAILED deployment may be retried.
6. Retry creates a new deployment attempt and preserves history.
7. Only a successful PRODUCTION deployment can be rolled back.
8. An Idempotency-Key must not create duplicate deployments.
9. Every deployment status update must create a deployment event.
