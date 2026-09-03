from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging
from app.database import init_db
from app.routers import auth, deployments, health, models, version
from app.schemas.errors import ApiError, ErrorDetail, ErrorResponse
from app.services.model_service import MlopsConflictError, MlopsNotFoundError


configure_logging(settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    logger.info("application_started", extra={"structured_data": {"service": "abb-mlops-api"}})
    yield

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the ABB MLOps Platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    request.state.trace_id = request.headers.get("X-Trace-Id", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | dict[str, object] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ApiError(code=code, message=message, details=details or {}),
        trace_id=getattr(request.state, "trace_id", str(uuid4())),
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
    )


@app.exception_handler(MlopsNotFoundError)
async def handle_not_found(_: Request, error: MlopsNotFoundError) -> JSONResponse:
    return error_response(_, status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(error))


@app.exception_handler(MlopsConflictError)
async def handle_conflict(_: Request, error: MlopsConflictError) -> JSONResponse:
    return error_response(_, status.HTTP_409_CONFLICT, "CONFLICT", str(error))


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, error: HTTPException) -> JSONResponse:
    return error_response(_, error.status_code, "HTTP_ERROR", str(error.detail))


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    details = [
        ErrorDetail(field=".".join(str(part) for part in item["loc"]), message=item["msg"])
        for item in error.errors()
    ]
    return error_response(
        _,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        "Request validation failed.",
        details,
    )


app.include_router(health.router)
app.include_router(version.router)
app.include_router(auth.router)
app.include_router(models.router)
app.include_router(deployments.router)
app.add_api_route("/health", health.get_health, methods=["GET"], include_in_schema=False)
