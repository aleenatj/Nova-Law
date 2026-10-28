from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.error_logging import ErrorCategory, ErrorSeverity, log_error
from app.db.database import get_db

router = APIRouter()


@router.get("/status/health")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "app_name": settings.APP_NAME,
    }


@router.get("/status/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Detailed health check including database connectivity."""
    health_status: dict[str, Any] = {
        "status": "healthy",
        "version": settings.VERSION,
        "app_name": settings.APP_NAME,
        "checks": {"database": "unknown", "ai_services": "unknown"},
    }

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {e!s}"
        health_status["status"] = "degraded"

    # Check AI services
    try:
        if settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY:
            health_status["checks"]["ai_services"] = "healthy"
        else:
            health_status["checks"]["ai_services"] = "no_api_keys_configured"
    except Exception as e:
        health_status["checks"]["ai_services"] = f"unhealthy: {e!s}"
        health_status["status"] = "degraded"

    log_error(
        error=Exception("Detailed health check failed"),
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.API,
    )

    return health_status


@router.get("/status/info")
async def system_info() -> dict[str, Any]:
    """Get system information and configuration."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "environment": "production" if not settings.DEBUG else "development",
        "features": {
            "jwt_auth": True,
            "websockets": True,
            "langchain": True,
            "langgraph": True,
            "postgresql": True,
        },
    }
