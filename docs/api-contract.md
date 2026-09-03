# MLOps Platform API Contract

Base URL: `/api`. JSON requests/responses use UTC ISO-8601 timestamps and UUID resource IDs. Protected endpoints require `Authorization: Bearer <token>`; mutations require the existing administrator role. OpenAPI is served by FastAPI at `/docs`.

## Common conventions

### Standard error response

```json
{
  "error": {
	"code": "MODEL_VERSION_NOT_APPROVED",
	"message": "Model version 1.0.0 must be approved before Production deployment.",
	"details": []
  },
  "trace_id": "example-trace-id"
}
```

`details` is a list for validation errors and an object/empty list for domain errors. The backend creates or propagates `trace_id` for each error. Standard codes include `VALIDATION_ERROR` (422), `NOT_FOUND` (404), `DUPLICATE_MODEL_NAME`, `DUPLICATE_MODEL_VERSION`, `INVALID_LIFECYCLE_TRANSITION`, `MODEL_VERSION_NOT_APPROVED`, `INVALID_DEPLOYMENT_STATE`, `ROLLBACK_NOT_AVAILABLE` (409), and `INTERNAL_ERROR` (500).

### Resource examples

```json
{
  "id": "3f0e59dc-f92a-4bf3-9bfd-7d469c4aaf65",
  "name": "Pump Failure Predictor",
  "description": "Predicts centrifugal-pump failures.",
  "tags": ["plant-a", "critical"],
  "metadata": {"owner_team": "Reliability"},
  "created_at": "2026-03-12T10:00:00Z",
  "updated_at": "2026-03-12T10:00:00Z"
}
```

```json
{
  "id": "6f569fba-b6e9-4a4f-b444-93a7c2c4d3ae",
  "model_id": "3f0e59dc-f92a-4bf3-9bfd-7d469c4aaf65",
  "version": "1.0.0",
  "description": "Initial approved release.",
  "tags": ["baseline"],
  "metadata": {"features": 42},
  "framework": "scikit-learn",
  "algorithm": "RandomForestClassifier",
  "artifact_uri": "s3://models/pump/1.0.0",
  "training_data_reference": "s3://datasets/pump/2026-03",
  "approval_status": "APPROVED",
  "approved_by": "admin@example.com",
  "approved_at": "2026-03-12T10:05:00Z",
  "lifecycle_stage": "APPROVED",
  "created_at": "2026-03-12T10:01:00Z",
  "updated_at": "2026-03-12T10:05:00Z"
}
```

## Model APIs

### POST `/models`

**Purpose:** Create a logical model. **Request:**
```json
{"name":"Pump Failure Predictor","description":"Predicts pump failures.","tags":["plant-a"],"metadata":{"owner_team":"Reliability"}}
```
**Response:** `201 Created` with the model resource. **Validation:** name 3–200 characters and globally unique; non-empty description; unknown fields rejected. **Errors:** `409 DUPLICATE_MODEL_NAME`, `422 VALIDATION_ERROR`, `401/403` authorization error.

### GET `/models?search=&stage=&page=1&page_size=25`

**Purpose:** List models for inventory. **Response:** `200 OK` with `{"items":[<model>],"total":1,"page":1,"page_size":25}` (an array is an acceptable interim response until pagination is added). **Validation:** page >= 1; page size 1–100; search is trimmed; stage is a lifecycle enum. **Errors:** `422 VALIDATION_ERROR`, `401`. Filtering is optional only where time-boxed; the response must still support the inventory.

### GET `/models/{model_id}`

**Purpose:** Retrieve one model. **Response:** `200 OK` with the model resource. **Validation:** `model_id` is UUID. **Errors:** `404 NOT_FOUND`, `422 VALIDATION_ERROR`, `401`.

### POST `/models/{model_id}/versions`

**Purpose:** Register a version; service assigns `PENDING` and `DRAFT`. **Request:**
```json
{"version":"1.0.0","description":"Initial release.","tags":["baseline"],"metadata":{"features":42},"framework":"scikit-learn","algorithm":"RandomForestClassifier","artifact_uri":"s3://models/pump/1.0.0","training_data_reference":"s3://datasets/pump/2026-03"}
```
**Response:** `201 Created` with the version resource. **Validation:** non-empty version/framework/algorithm/artifact/training reference; version unique within model; clients cannot set initial approval/lifecycle. **Errors:** `404 NOT_FOUND`, `409 DUPLICATE_MODEL_VERSION`, `422 VALIDATION_ERROR`, `403`.

### GET `/models/{model_id}/versions`

**Purpose:** List model versions. **Response:** `200 OK` with `{"items":[<version>],"total":1}` or an interim array. **Validation:** UUID model ID. **Errors:** `404 NOT_FOUND`, `422`, `401`.

### POST `/models/{model_id}/versions/{version_id}/approve`

**Purpose:** Approve a version. **Request:** `{}`. **Response:** `200 OK` with updated version, including `approval_status: "APPROVED"`, `approved_by`, and `approved_at`. **Validation:** both resources must match; archived versions cannot be approved; approval is idempotent only for an already-approved version. **Errors:** `404 NOT_FOUND`, `409 INVALID_LIFECYCLE_TRANSITION`, `403`.

### POST `/models/{model_id}/versions/{version_id}/lifecycle`

**Purpose:** Transition lifecycle stage. **Request:** `{"lifecycle_stage":"STAGING"}`. **Response:** `200 OK` updated version. **Validation:** stage is `DRAFT|VALIDATED|APPROVED|STAGING|PRODUCTION|ARCHIVED`; only documented transitions are allowed; `APPROVED` stage requires approval status `APPROVED`. **Errors:** `404 NOT_FOUND`, `409 INVALID_LIFECYCLE_TRANSITION`, `422`, `403`.

### GET `/models/{model_id}/versions/compare?left_version_id={uuid}&right_version_id={uuid}`

**Purpose:** Compare two versions of the route model. **Response:** `200 OK`:
```json
{"left_version":{"version":"1.0.0"},"right_version":{"version":"1.1.0"},"differences":{"algorithm":{"left":"RandomForestClassifier","right":"XGBoost"}},"metrics":{"left":{"drift_score":0.08},"right":{"drift_score":0.04}}}
```
**Validation:** IDs are UUIDs; both versions must belong to `{model_id}`. **Errors:** `404 NOT_FOUND`, `409 VERSION_MODEL_MISMATCH`, `422`, `401`.

### GET `/models/{model_id}/metrics?version_id={uuid}`

**Purpose:** Get the latest representative monitoring snapshot for a model or version. **Response:** `200 OK`:
```json
{"model_id":"3f0e59dc-f92a-4bf3-9bfd-7d469c4aaf65","model_version_id":"6f569fba-b6e9-4a4f-b444-93a7c2c4d3ae","prediction_latency_ms":42.5,"throughput_per_minute":330,"error_rate_percent":0.4,"quality_score":0.94,"drift_score":0.08,"availability_percent":99.9,"last_successful_inference_at":"2026-03-12T10:20:00Z","monitoring_status":"HEALTHY","measured_at":"2026-03-12T10:21:00Z","data_source":"representative_demo"}
```
**Validation:** IDs must exist and version must belong to model. **Errors:** `404 NOT_FOUND` or `MONITORING_DATA_UNAVAILABLE`, `422`, `401`.

## Deployment APIs

### POST `/deployments`

**Purpose:** Create and synchronously simulate a deployment. **Headers:** required `Idempotency-Key: <1-255 character value>`. **Request:**
```json
{"model_version_id":"6f569fba-b6e9-4a4f-b444-93a7c2c4d3ae","environment":"PRODUCTION","simulate_failure":false}
```
**Response:** `201 Created` with the deployment below; duplicate key returns `200 OK` with the originally created resource and no new events.
```json
{"id":"8ab2b41f-7da5-4e31-88fc-fc2b3255578d","model_id":"3f0e59dc-f92a-4bf3-9bfd-7d469c4aaf65","model_version_id":"6f569fba-b6e9-4a4f-b444-93a7c2c4d3ae","environment":"PRODUCTION","status":"SUCCEEDED","idempotency_key":"pump-prod-001","simulate_failure":false,"requested_at":"2026-03-12T10:25:00Z","started_at":"2026-03-12T10:25:01Z","completed_at":"2026-03-12T10:25:02Z","failure_reason":null,"retry_of_deployment_id":null,"rolled_back_from_deployment_id":null,"created_at":"2026-03-12T10:25:00Z","updated_at":"2026-03-12T10:25:02Z","events":[{"old_status":null,"new_status":"REQUESTED","event_type":"STATUS_CHANGED","message":"Deployment requested.","actor":"admin@example.com","created_at":"2026-03-12T10:25:00Z"}]}
```
**Validation:** environment is `DEV|TEST|STAGING|PRODUCTION`; version exists; approved version required for production. **Errors:** `400 IDEMPOTENCY_KEY_REQUIRED`, `404 NOT_FOUND`, `409 MODEL_VERSION_NOT_APPROVED`, `422`, `403`.

### GET `/deployments?status=&environment=&model_id=&model_version_id=&page=&page_size=`

**Purpose:** List/filter deployments. **Response:** `200 OK` with paged items or an interim array. **Validation:** enum filters and UUID filters must be valid. **Errors:** `422`, `401`.

### GET `/deployments/{deployment_id}`

**Purpose:** Return deployment details with ordered event history. **Response:** `200 OK` with the deployment response shown above. **Validation:** UUID. **Errors:** `404 NOT_FOUND`, `422`, `401`.

### POST `/deployments/{deployment_id}/retry`

**Purpose:** Retry a failed deployment. **Request:** `{}`. **Response:** `201 Created` with a new deployment whose `retry_of_deployment_id` is the failed deployment. **Validation:** source must currently be `FAILED`; retry receives a server-generated idempotency key and creates its own full event sequence. **Errors:** `404 NOT_FOUND`, `409 INVALID_DEPLOYMENT_STATE`, `403`.

### POST `/deployments/{deployment_id}/rollback`

**Purpose:** Restore the immediately previous successful production deployment for the same model/environment. **Request:** `{}`. **Response:** `201 Created` with the linked rollback deployment; source deployment is `ROLLED_BACK` and both actions are evented. **Validation:** source must be successful production deployment and an eligible preceding production deployment must exist. **Errors:** `404 NOT_FOUND`, `409 ROLLBACK_NOT_AVAILABLE`, `403`.

## Health API

### GET `/health` and GET `/api/health`

**Purpose:** Unauthenticated liveness/status check. **Request:** none. **Response:** `200 OK`:
```json
{"status":"Healthy","service":"ABB MLOps Platform API","timestampUtc":"2026-03-12T10:00:00Z"}
```
**Validation/errors:** none expected; `500 INTERNAL_ERROR` only for unexpected failures.