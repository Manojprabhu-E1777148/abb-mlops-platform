from datetime import datetime, timezone
import logging
from uuid import UUID, uuid4

from sqlmodel import Session, select

from app.models.mlops import (
    ApprovalStatus,
    DeploymentCreate,
    DeploymentEventModel,
    DeploymentEventRead,
    DeploymentModel,
    DeploymentRead,
    DeploymentStatus,
    ModelMetricModel,
    ModelMetricRead,
    ModelModel,
    ModelVersionModel,
)
from app.services.model_service import MlopsConflictError, MlopsNotFoundError

logger = logging.getLogger(__name__)


def serialize_event(event: DeploymentEventModel) -> DeploymentEventRead:
    return DeploymentEventRead(
        id=event.id,
        status=event.status,
        message=event.message,
        created_at=event.created_at,
    )


def serialize_deployment(session: Session, deployment: DeploymentModel) -> DeploymentRead:
    events = session.exec(
        select(DeploymentEventModel)
        .where(DeploymentEventModel.deployment_id == deployment.id)
        .order_by(DeploymentEventModel.created_at)
    ).all()
    return DeploymentRead(
        id=deployment.id,
        model_version_id=deployment.model_version_id,
        environment=deployment.environment,
        status=deployment.status,
        idempotency_key=deployment.idempotency_key,
        failure_simulated=deployment.failure_simulated,
        retry_of_deployment_id=deployment.retry_of_deployment_id,
        rollback_of_deployment_id=deployment.rollback_of_deployment_id,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at,
        events=[serialize_event(event) for event in events],
    )


class DeploymentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_deployment(self, deployment_id: UUID) -> DeploymentModel:
        deployment = self.session.get(DeploymentModel, deployment_id)
        if deployment is None:
            raise MlopsNotFoundError("Deployment not found.")
        return deployment

    def _set_status(self, deployment: DeploymentModel, status: DeploymentStatus, message: str) -> None:
        deployment.status = status
        deployment.updated_at = datetime.now(timezone.utc)
        self.session.add(deployment)
        self.session.add(
            DeploymentEventModel(
                deployment_id=deployment.id,
                status=status,
                message=message,
            )
        )
        logger.info(
            "deployment_status_updated",
            extra={
                "structured_data": {
                    "deployment_id": str(deployment.id),
                    "model_version_id": str(deployment.model_version_id),
                    "environment": deployment.environment,
                    "status": status.value,
                }
            },
        )

    def _create_deployment(
        self,
        model_version: ModelVersionModel,
        environment: str,
        idempotency_key: str,
        simulate_failure: bool,
        retry_of_deployment_id: UUID | None = None,
    ) -> DeploymentModel:
        if environment.upper() == "PRODUCTION" and model_version.approval_status != ApprovalStatus.APPROVED:
            raise MlopsConflictError("Only APPROVED model versions can deploy to PRODUCTION.")

        deployment = DeploymentModel(
            model_version_id=model_version.id,
            environment=environment.upper(),
            idempotency_key=idempotency_key,
            failure_simulated=simulate_failure,
            retry_of_deployment_id=retry_of_deployment_id,
        )
        self.session.add(deployment)
        self.session.flush()
        self._set_status(deployment, DeploymentStatus.REQUESTED, "Deployment requested.")
        self._set_status(deployment, DeploymentStatus.VALIDATING, "Deployment validation started.")
        self._set_status(deployment, DeploymentStatus.DEPLOYING, "Deployment started.")
        if simulate_failure:
            self._set_status(deployment, DeploymentStatus.FAILED, "Deployment failed by simulation.")
        else:
            self._set_status(deployment, DeploymentStatus.SUCCEEDED, "Deployment succeeded.")
        return deployment

    def create_deployment(self, payload: DeploymentCreate, idempotency_key: str) -> DeploymentRead:
        existing = self.session.exec(
            select(DeploymentModel).where(DeploymentModel.idempotency_key == idempotency_key)
        ).first()
        if existing is not None:
            return serialize_deployment(self.session, existing)

        model_version = self.session.get(ModelVersionModel, payload.model_version_id)
        if model_version is None:
            raise MlopsNotFoundError("Model version not found.")
        deployment = self._create_deployment(
            model_version,
            payload.environment,
            idempotency_key,
            payload.simulate_failure,
        )
        self.session.commit()
        self.session.refresh(deployment)
        return serialize_deployment(self.session, deployment)

    def list_deployments(self) -> list[DeploymentRead]:
        deployments = self.session.exec(
            select(DeploymentModel).order_by(DeploymentModel.created_at.desc())
        ).all()
        return [serialize_deployment(self.session, deployment) for deployment in deployments]

    def get_deployment(self, deployment_id: UUID) -> DeploymentRead:
        return serialize_deployment(self.session, self._get_deployment(deployment_id))

    def retry_deployment(self, deployment_id: UUID) -> DeploymentRead:
        failed_deployment = self._get_deployment(deployment_id)
        if failed_deployment.status != DeploymentStatus.FAILED:
            raise MlopsConflictError("Only FAILED deployments can be retried.")
        model_version = self.session.get(ModelVersionModel, failed_deployment.model_version_id)
        if model_version is None:
            raise MlopsNotFoundError("Model version not found.")
        retry = self._create_deployment(
            model_version,
            failed_deployment.environment,
            str(uuid4()),
            False,
            retry_of_deployment_id=failed_deployment.id,
        )
        self.session.commit()
        self.session.refresh(retry)
        return serialize_deployment(self.session, retry)

    def rollback_deployment(self, deployment_id: UUID) -> DeploymentRead:
        deployment = self._get_deployment(deployment_id)
        if deployment.environment != "PRODUCTION" or deployment.status != DeploymentStatus.SUCCEEDED:
            raise MlopsConflictError("Only successful PRODUCTION deployments can be rolled back.")
        self._set_status(deployment, DeploymentStatus.ROLLED_BACK, "Production deployment rolled back.")
        self.session.commit()
        self.session.refresh(deployment)
        return serialize_deployment(self.session, deployment)


class MonitoringService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_metrics(self, model_id: UUID) -> ModelMetricRead:
        if self.session.get(ModelModel, model_id) is None:
            raise MlopsNotFoundError("Model not found.")
        metric = self.session.exec(
            select(ModelMetricModel).where(ModelMetricModel.model_id == model_id)
        ).first()
        if metric is None:
            now = datetime.now(timezone.utc)
            metric = ModelMetricModel(
                model_id=model_id,
                prediction_latency_ms=42.0,
                throughput_per_minute=1800.0,
                error_rate=0.01,
                quality_score=0.98,
                drift_score=0.03,
                availability=0.999,
                last_successful_inference_at=now,
                monitoring_status="HEALTHY",
            )
            self.session.add(metric)
            self.session.commit()
            self.session.refresh(metric)
        return ModelMetricRead(
            prediction_latency_ms=metric.prediction_latency_ms,
            throughput_per_minute=metric.throughput_per_minute,
            error_rate=metric.error_rate,
            quality_score=metric.quality_score,
            drift_score=metric.drift_score,
            availability=metric.availability,
            last_successful_inference_at=metric.last_successful_inference_at,
            monitoring_status=metric.monitoring_status,
            updated_at=metric.updated_at,
        )
