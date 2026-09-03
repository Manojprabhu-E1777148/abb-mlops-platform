"""Replace projects with MLOps domain tables

Revision ID: 202603120004
Revises: 202603120003
Create Date: 2026-03-12 00:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202603120004"
down_revision: Union[str, Sequence[str], None] = "202603120003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_models_name", "models", ["name"])

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=False),
        sa.Column("framework", sa.String(length=100), nullable=False),
        sa.Column("algorithm", sa.String(length=200), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=False),
        sa.Column("training_data_reference", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("approval_status", sa.String(length=20), nullable=False),
        sa.Column("lifecycle_stage", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_id", "version", name="uq_model_versions_model_version"),
    )
    op.create_index("ix_model_versions_model_id", "model_versions", ["model_id"])

    op.create_table(
        "deployments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_version_id", sa.Uuid(), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("failure_simulated", sa.Boolean(), nullable=False),
        sa.Column("retry_of_deployment_id", sa.Uuid(), nullable=True),
        sa.Column("rollback_of_deployment_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["retry_of_deployment_id"], ["deployments.id"]),
        sa.ForeignKeyConstraint(["rollback_of_deployment_id"], ["deployments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_deployments_model_version_id", "deployments", ["model_version_id"])
    op.create_index("ix_deployments_environment", "deployments", ["environment"])

    op.create_table(
        "deployment_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("deployment_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployment_events_deployment_id", "deployment_events", ["deployment_id"])

    op.create_table(
        "model_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("prediction_latency_ms", sa.Float(), nullable=False),
        sa.Column("throughput_per_minute", sa.Float(), nullable=False),
        sa.Column("error_rate", sa.Float(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("drift_score", sa.Float(), nullable=False),
        sa.Column("availability", sa.Float(), nullable=False),
        sa.Column("last_successful_inference_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("monitoring_status", sa.String(length=30), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_id", name="uq_model_metrics_model_id"),
    )
    op.create_index("ix_model_metrics_model_id", "model_metrics", ["model_id"])

    inspector = sa.inspect(op.get_bind())
    if "projects" in inspector.get_table_names():
        op.drop_table("projects")


def downgrade() -> None:
    op.drop_table("model_metrics")
    op.drop_table("deployment_events")
    op.drop_table("deployments")
    op.drop_table("model_versions")
    op.drop_table("models")
