from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, JSON, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LifecycleStage(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"


class DeploymentStatus(str, Enum):
    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    DEPLOYING = "DEPLOYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class ModelModel(SQLModel, table=True):
    __tablename__ = "models"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String(200), unique=True, index=True, nullable=False))
    description: str
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))


class ModelVersionModel(SQLModel, table=True):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("model_id", "version", name="uq_model_versions_model_version"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: UUID = Field(foreign_key="models.id", nullable=False, index=True)
    version: str = Field(sa_column=Column(String(100), nullable=False))
    framework: str = Field(sa_column=Column(String(100), nullable=False))
    algorithm: str = Field(sa_column=Column(String(200), nullable=False))
    artifact_uri: str
    training_data_reference: str
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, sa_column=Column(String(20), nullable=False))
    lifecycle_stage: LifecycleStage = Field(default=LifecycleStage.DRAFT, sa_column=Column(String(20), nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))


class DeploymentModel(SQLModel, table=True):
    __tablename__ = "deployments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_version_id: UUID = Field(foreign_key="model_versions.id", nullable=False, index=True)
    environment: str = Field(sa_column=Column(String(50), nullable=False, index=True))
    status: DeploymentStatus = Field(default=DeploymentStatus.REQUESTED, sa_column=Column(String(20), nullable=False))
    idempotency_key: str = Field(sa_column=Column(String(255), unique=True, nullable=False))
    failure_simulated: bool = False
    retry_of_deployment_id: UUID | None = Field(default=None, foreign_key="deployments.id")
    rollback_of_deployment_id: UUID | None = Field(default=None, foreign_key="deployments.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))


class DeploymentEventModel(SQLModel, table=True):
    __tablename__ = "deployment_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    deployment_id: UUID = Field(foreign_key="deployments.id", nullable=False, index=True)
    status: DeploymentStatus = Field(sa_column=Column(String(20), nullable=False))
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))


class ModelMetricModel(SQLModel, table=True):
    __tablename__ = "model_metrics"
    __table_args__ = (UniqueConstraint("model_id", name="uq_model_metrics_model_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: UUID = Field(foreign_key="models.id", nullable=False, index=True)
    prediction_latency_ms: float
    throughput_per_minute: float
    error_rate: float
    quality_score: float
    drift_score: float
    availability: float
    last_successful_inference_at: datetime
    monitoring_status: str = Field(sa_column=Column(String(30), nullable=False))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))


class ModelCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class ModelVersionCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1, max_length=100)
    framework: str = Field(min_length=1, max_length=100)
    algorithm: str = Field(min_length=1, max_length=200)
    artifact_uri: str = Field(min_length=1)
    training_data_reference: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    approval_status: ApprovalStatus
    lifecycle_stage: LifecycleStage | None = None


class DeploymentCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    model_version_id: UUID
    environment: str = Field(min_length=1, max_length=50)
    simulate_failure: bool = False


class ModelRead(SQLModel):
    id: UUID
    name: str
    description: str
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ModelVersionRead(SQLModel):
    id: UUID
    model_id: UUID
    version: str
    framework: str
    algorithm: str
    artifact_uri: str
    training_data_reference: str
    tags: list[str]
    metadata: dict[str, Any]
    approval_status: ApprovalStatus
    lifecycle_stage: LifecycleStage
    created_at: datetime
    updated_at: datetime


class ModelVersionComparisonRead(SQLModel):
    left_version: ModelVersionRead
    right_version: ModelVersionRead
    differences: dict[str, dict[str, Any]]


class DeploymentEventRead(SQLModel):
    id: UUID
    status: DeploymentStatus
    message: str
    created_at: datetime


class DeploymentRead(SQLModel):
    id: UUID
    model_version_id: UUID
    environment: str
    status: DeploymentStatus
    idempotency_key: str
    failure_simulated: bool
    retry_of_deployment_id: UUID | None
    rollback_of_deployment_id: UUID | None
    created_at: datetime
    updated_at: datetime
    events: list[DeploymentEventRead] = Field(default_factory=list)


class ModelMetricRead(SQLModel):
    prediction_latency_ms: float
    throughput_per_minute: float
    error_rate: float
    quality_score: float
    drift_score: float
    availability: float
    last_successful_inference_at: datetime
    monitoring_status: str
    updated_at: datetime
