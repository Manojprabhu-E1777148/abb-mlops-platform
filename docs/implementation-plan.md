# MLOps Platform Implementation Plan

## Delivery strategy

Build and validate a backend vertical slice before connecting each Angular workflow. Preserve the existing FastAPI, SQLModel/SQLAlchemy, Alembic, Pytest, Angular standalone, Angular Material, RxJS, and Docker foundations. The estimates total approximately 12–16 hours, so slices 1–5 are P0; slices 6–10 are completed only after P0 is demonstrable and tested.

## Slice 1 — Backend foundation, persistence, and health

- **Goal:** Establish runnable configuration, migrations, standard errors/trace IDs, structured logs, health check, and isolated test fixture.
- **Files likely changed/created:** `backend/app/main.py`, `backend/app/database.py`, `backend/app/core/config.py`, `backend/app/routers/health.py`, `backend/alembic/`, `backend/tests/conftest.py`, `backend/tests/test_health.py`.
- **APIs included:** `GET /api/health` and `/health` alias.
- **Database entities included:** baseline audit/timestamp conventions; no MLOps workflow dependency.
- **Angular pages/components included:** none.
- **Tests included:** health returns 200; validation and error-envelope smoke tests; test database isolation.
- **Acceptance criteria:** app starts from environment configuration; health is public and returns UTC time; errors follow the standard envelope; migrations run on empty SQLite.
- **Estimated effort:** 1–1.5 hours.
- **Dependencies:** none.

## Slice 2 — Model registry APIs and persistence

- **Goal:** Deliver model creation, retrieval, and inventory list with uniqueness and audit data.
- **Files likely changed/created:** `backend/app/models/mlops.py`, `backend/app/schemas/models.py`, `backend/app/services/model_service.py`, `backend/app/routers/models.py`, Alembic revision, `backend/tests/test_models_api.py`.
- **APIs included:** `POST /api/models`, `GET /api/models`, `GET /api/models/{model_id}`; add basic `search`, pagination, and latest-stage summary only if time permits.
- **Database entities included:** `models` with unique name, description, tags, metadata, `created_at`, `updated_at`.
- **Angular pages/components included:** none.
- **Tests included:** create model successfully; duplicate name rejected; list/get; audit timestamp serialization.
- **Acceptance criteria:** model name uniqueness is enforced by database/service; responses use typed schemas; not-found/conflict errors are structured; routers remain thin.
- **Estimated effort:** 1–1.5 hours.
- **Dependencies:** Slice 1.

## Slice 3 — Version registration, approval, and lifecycle

- **Goal:** Add versioned model records, governance fields, safe approval, and lifecycle transitions.
- **Files likely changed/created:** model/version schemas and entities, `model_service.py` or `version_lifecycle_service.py`, `routers/models.py`, Alembic revision, `backend/tests/test_version_workflows.py`.
- **APIs included:** `POST/GET /api/models/{model_id}/versions`, `POST /api/models/{model_id}/versions/{version_id}/approve`, `POST /api/models/{model_id}/versions/{version_id}/lifecycle`.
- **Database entities included:** `model_versions` with unique `(model_id, version)`, description/tags/metadata, framework/algorithm, artifact/training reference, `approval_status`, `approved_by`, `approved_at`, lifecycle, audit fields.
- **Angular pages/components included:** none.
- **Tests included:** register two versions; duplicate version rejected; default PENDING/DRAFT; approve successfully; invalid lifecycle rejected.
- **Acceptance criteria:** only allowed lifecycle transitions succeed; approver/time are UTC and attributable; all version fields round-trip.
- **Estimated effort:** 1.5–2 hours.
- **Dependencies:** Slice 2 and current-user identity.

## Slice 4 — Deployment validation, idempotency, and events

- **Goal:** Create deployments with production-approval validation, deterministic state events, and duplicate safety.
- **Files likely changed/created:** deployment schemas/entities, `deployment_service.py`, `routers/deployments.py`, Alembic revision, `backend/tests/test_deployments_api.py`.
- **APIs included:** `POST /api/deployments`, `GET /api/deployments`, `GET /api/deployments/{deployment_id}`.
- **Database entities included:** `deployments`, `deployment_events`; add model ID, status times, failure reason, and event old/new status/type/actor fields to close gaps in current entities.
- **Angular pages/components included:** none.
- **Tests included:** unapproved production blocked; approved deployment succeeds; all transitions evented; same idempotency key returns original deployment with no additional event.
- **Acceptance criteria:** states follow REQUESTED → VALIDATING → DEPLOYING → SUCCEEDED/FAILED; header is required; database uniqueness protects races; status events are immutable and ordered.
- **Estimated effort:** 2–2.5 hours.
- **Dependencies:** Slice 3.

## Slice 5 — Failure simulation, retry, rollback, and workflow tests

- **Goal:** Finish the critical deployment control loop and prove it through API and service tests.
- **Files likely changed/created:** `deployment_service.py`, deployment schemas/router, Alembic revision if links/times are absent, `backend/tests/test_deployment_state_transitions.py`, `backend/tests/test_mlops_workflows.py`.
- **APIs included:** `POST /api/deployments/{deployment_id}/retry`, `POST /api/deployments/{deployment_id}/rollback`.
- **Database entities included:** deployment retry/rollback links and event records.
- **Angular pages/components included:** none.
- **Tests included:** simulated failure; retry failed deployment; reject retry otherwise; rollback successful production deployment; reject missing-prior rollback; complete register/approve/deploy/retry/rollback integration workflow.
- **Acceptance criteria:** retry creates a distinct linked attempt; failure has reason/completion time; rollback restores the immediately preceding successful production version and preserves source/rollback event history.
- **Estimated effort:** 1.5–2 hours.
- **Dependencies:** Slice 4; two successful production deployments are seeded in rollback tests.

## Slice 6 — Monitoring and version comparison

- **Goal:** Provide realistic representative metrics and same-model version comparisons.
- **Files likely changed/created:** metric entity/schema, `monitoring_service.py`, comparison service or `model_service.py`, model router, seed utility, Alembic revision, `backend/tests/test_monitoring_and_comparison.py`, backend README.
- **APIs included:** `GET /api/models/{model_id}/metrics?version_id=`, `GET /api/models/{model_id}/versions/compare`.
- **Database entities included:** `monitoring_metrics` keyed/indexed by model/version/measured time.
- **Angular pages/components included:** none.
- **Tests included:** metrics response; comparison fields/metrics; reject cross-model comparison; status threshold tests.
- **Acceptance criteria:** all required metrics return with monitoring status and measurement time; README/API mark data as representative/demo; comparison has a deterministic difference shape.
- **Estimated effort:** 1–1.5 hours.
- **Dependencies:** Slice 3; Slice 5 if metrics are seeded after successful deployments.

## Slice 7 — Angular shell, API layer, and shared states

- **Goal:** Make the Angular shell navigable and safely connected to the documented API.
- **Files likely changed/created:** `frontend/mlops-ui/src/app/app.routes.ts`, app shell files, `mlops-api.service.ts`, API models, HTTP interceptor/error mapper, shared loading/empty/error components, Material imports, environment configuration, component specs.
- **APIs included:** typed client coverage for completed backend endpoints.
- **Database entities included:** none.
- **Angular pages/components included:** app shell/navigation; shared UI states; API/error layer.
- **Tests included:** error-envelope mapping; loading/error/empty shared state rendering; idempotency header generation.
- **Acceptance criteria:** routes render; API base URL is configuration-driven, not hard-coded; server failure is surfaced and no success message appears on failed calls.
- **Estimated effort:** 1–1.5 hours.
- **Dependencies:** Slice 1–5 APIs available; frontend currently resides under `backend/frontend/mlops-ui/`, so normalize or document the actual path before edits.

## Slice 8 — Angular model inventory and version details

- **Goal:** Deliver model discovery and version governance operations.
- **Files likely changed/created:** inventory/details components, version registration/approval/lifecycle forms, comparison dialog, routes, API models/service, specs, styles.
- **APIs included:** model, version, approval, lifecycle, comparison, and summary-metrics endpoints.
- **Database entities included:** none.
- **Angular pages/components included:** Model Inventory; Model Version Details; version registration and comparison dialogs.
- **Tests included:** populated/empty/error inventory; detail loading; approval/register form validation; compare selection/result/error.
- **Acceptance criteria:** operators can search/list and navigate to details; metadata and governance status are visible; successful operations refresh data and failed operations remain visibly failed.
- **Estimated effort:** 1.5–2 hours.
- **Dependencies:** Slice 3, Slice 6, Slice 7.

## Slice 9 — Angular deployment, event timeline, and monitoring dashboard

- **Goal:** Deliver operating views for deployment management and demo observability.
- **Files likely changed/created:** deployments component/form, event-timeline component, monitoring dashboard, filters, API service/models, Material styles, specs.
- **APIs included:** deployment create/list/detail/retry/rollback and metrics.
- **Database entities included:** none.
- **Angular pages/components included:** Deployment View, Event Timeline, Monitoring Dashboard.
- **Tests included:** request form validation; failure display; retry/rollback eligibility; timeline ordering; metric status presentation; loading/empty/error/populated states.
- **Acceptance criteria:** deployment filters work where practical; status/history are clear; retry and rollback are enabled only when eligible; dashboard contains every required metric and demo-data notice.
- **Estimated effort:** 2–2.5 hours.
- **Dependencies:** Slice 4–7.

## Slice 10 — Delivery packaging and final review

- **Goal:** Make the vertical slice reproducible and assessable.
- **Files likely changed/created:** root `docker-compose.yml`, backend/frontend Dockerfiles as needed, root/`backend/README.md`, `.github/workflows/backend-tests.yml`, optional frontend workflow, `.env.example`, architecture/API/traceability docs.
- **APIs included:** none; validate all completed endpoints through Swagger and smoke flow.
- **Database entities included:** migrations only.
- **Angular pages/components included:** none beyond build packaging.
- **Tests included:** backend `pytest`; Angular unit tests/build; Compose startup/health smoke check; CI steps.
- **Acceptance criteria:** a reviewer can configure environment variables, start Compose, apply migrations, run tests, access UI/API docs, and understand demo-data limitations.
- **Estimated effort:** 1–1.5 hours.
- **Dependencies:** all desired feature slices.

## P0 completion gate

Before starting optional UI breadth or delivery polish, demonstrate: create model, register two versions, approve one, reject unapproved production deployment, deploy approved version, simulate/retry failure, rollback a valid production deployment, return an idempotent duplicate result, and pass the required backend workflow tests.