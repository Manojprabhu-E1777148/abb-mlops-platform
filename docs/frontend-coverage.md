# Frontend Coverage

## Routes

- `/login` provides the existing token login workflow.
- `/` and unknown paths redirect to `/models`.
- `/models`, `/models/:modelId`, `/deployments`, and `/monitoring` require a stored token.

## API-backed screens

- Models provide loading, empty, error, populated inventory, detail navigation, and an administrator-only create action.
- Model details display metadata and registered version approval/lifecycle values, with administrator-only registration and approval actions.
- Deployments display environment, status, version identifier, and backend event history; administrators can create, retry eligible failures, and roll back eligible production successes.
- Monitoring lets the user select a registered model and displays the backend-provided metric snapshot.

## Integration constraints

The UI calls `http://localhost:8000/api` directly. The FastAPI application permits CORS for `http://localhost:4200`; the backend and valid login credentials are required for authenticated testing. Lifecycle transitions and global monitoring are not available backend APIs and are not represented as UI actions.
