"""Updated main.py with comprehensive API versioning support.

This file demonstrates how to integrate the versioning system while maintaining
backward compatibility with existing endpoints.
"""

import time
import warnings
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.api.v1 import (
    analytics,
    audit_log,
    auth,
    cal,
    case,
    contact_us,
    customer,
    engage,
    engage_feedback,
    engage_support,
    kyc,
    law_firm,
    lawyer,
    lawyer_onboarding,
    navigator,
    payment,
    resolve,
    status,
    timeline,
    triage,
    upload,
    user,
)
from app.core.config import settings
from app.core.error_handling import (
    register_error_handling_middleware,
    register_exception_handlers,
)
from app.core.logging import setup_logging
from app.core.versioning import version_manager
from app.middleware.audit import AuditContextMiddleware
from app.middleware.versioning import (
    DeprecationWarningMiddleware,
    VersionDetectionMiddleware,
    VersionValidationMiddleware,
)

# from app.monitoring.error_monitoring import start_error_monitoring
from app.monitoring.version_tracking import version_tracker

# TODO: Remove this warning suppression when LangChain updates BaseMessage to Pydantic V2
warnings.filterwarnings(
    "ignore",
    message="Mixing V1 models and V2 models.*",
    category=UserWarning,
    module="pydantic._internal._generate_schema",
)


# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        # # Security headers required to prevent data leakage and basic XSS vectors:
        # # - Referrer-Policy: prevents full URLs from being sent to other sites
        # # - Content-Security-Policy: restricts where scripts/resources can load from
        # # These are added to satisfy security scanners and harden API responses
        # # even though this service primarily returns JSON.        
        # response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


# --- Enhanced Rate Limiting Middleware with Version Tracking ---
RATE_LIMIT = 100  # requests
RATE_PERIOD = 60  # seconds
rate_limit_store: defaultdict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = [t for t in rate_limit_store[ip] if now - t < RATE_PERIOD]
        window.append(now)
        rate_limit_store[ip] = window

        if len(window) > RATE_LIMIT:
            return Response("Too Many Requests", status_code=HTTP_429_TOO_MANY_REQUESTS)

        # Track request for version monitoring
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time

        # Extract version and endpoint for tracking
        version = getattr(request.state, "api_version", "unknown")
        endpoint = request.url.path

        # Track the request
        version_tracker.track_request(
            version=version,
            endpoint=endpoint,
            client_id=ip,
            success=response.status_code < 400,
            response_time=response_time,
        )

        return response


# --- Setup structlog ---
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Nova Law AI Backend ⚖️",
    description="Multi-agent AI system backend with comprehensive API versioning",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Add audit context middleware (should be early in the chain)
app.add_middleware(AuditContextMiddleware)

# Add versioning middleware (order matters)
app.add_middleware(VersionDetectionMiddleware)
app.add_middleware(VersionValidationMiddleware)
app.add_middleware(DeprecationWarningMiddleware)

# Add security and observability middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)

# Add CORS and TrustedHost middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Register all exception handlers
register_exception_handlers(app)

# Register error handling middleware
register_error_handling_middleware(app)

# Include API routers with versioning
app.include_router(status.router, prefix="/api/v1", tags=["status"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
# app.include_router(email.router, prefix="/api/v1", tags=["email"])
app.include_router(kyc.router, prefix="/api/v1/customer", tags=["customer"])
app.include_router(triage.router, prefix="/api/v1", tags=["triage"])
# app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(payment.router, prefix="/api/v1/payment", tags=["payment"])
app.include_router(cal.router, prefix="/api/v1/cal", tags=["cal"])

app.include_router(resolve.router, prefix="/api/v1", tags=["resolve"])
app.include_router(engage.router, prefix="/api/v1", tags=["engage"])
app.include_router(engage_feedback.router, prefix="/api/v1", tags=["engage-feedback"])
app.include_router(engage_support.router, prefix="/api/v1", tags=["engage-support"])
app.include_router(timeline.router, prefix="/api/v1", tags=["timeline"])
app.include_router(user.router, prefix="/api/v1", tags=["users"])
app.include_router(navigator.router, prefix="/api/v1", tags=["navigator"])
app.include_router(customer.router, prefix="/api/v1", tags=["customer"])
app.include_router(case.router, prefix="/api/v1", tags=["case"])
app.include_router(law_firm.router, prefix="/api/v1", tags=["law-firms"])
app.include_router(lawyer.router, prefix="/api/v1", tags=["lawyers"])
app.include_router(lawyer_onboarding.router, prefix="/api/v1", tags=["B2C-experts"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(audit_log.router, prefix="/api/v1", tags=["audit-log"])
app.include_router(contact_us.router, prefix="/api/v1", tags=["contact-us"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])

@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler."""
    # Start error monitoring when the app starts
    # start_error_monitoring(check_interval_seconds=60)
    pass


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler."""
    # Stop error monitoring when the app shuts down
    # from app.monitoring.error_monitoring import stop_error_monitoring

    # stop_error_monitoring()
    pass


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with version information."""
    return {
        "message": "Nova Law AI Backend",
        "version": "1.0.0",
        "api_versions": {
            "supported": [v.value for v in version_manager.supported_versions],
            "latest": version_manager.get_latest_version().value,
            "default": version_manager.default_version.value,
        },
        "documentation": "/api/docs" if settings.DEBUG else None,
    }


# @app.get("/health")
# async def health_check():
#     """Basic health check endpoint."""
#     return {"status": "healthy"}


@app.get("/api/versions")
async def get_api_versions() -> dict[str, Any]:
    """Get information about supported API versions."""
    return {
        "supported_versions": [v.value for v in version_manager.supported_versions],
        "deprecated_versions": [v.value for v in version_manager.deprecated_versions],
        "latest_version": version_manager.get_latest_version().value,
        "recommended_version": version_manager.get_recommended_version().value,
        "default_version": version_manager.default_version.value,
    }


@app.get("/api/versions/{version}/info")
async def get_version_info(version: str) -> dict[str, Any]:
    """Get detailed information about a specific API version."""
    if not version_manager.is_supported(version):
        return {
            "error": "Unsupported version",
            "message": f"Version {version} is not supported",
            "supported_versions": [v.value for v in version_manager.supported_versions],
        }

    deprecation_info = version_manager.get_deprecation_info(version)

    return {
        "version": version,
        "supported": True,
        "deprecated": version_manager.is_deprecated(version),
        "deprecation_info": deprecation_info,
        "endpoints": {
            "auth": f"/api/{version}/auth",
            "users": f"/api/{version}/users",
            "agents": f"/api/{version}/agents",
            "user_roles": f"/api/{version}/user-roles",
            "status": f"/api/{version}/status",
        },
    }


# @app.get("/api/monitoring/usage")
# async def get_usage_stats(days: int = 30):
#     """Get API usage statistics."""
#     return version_tracker.get_usage_report(days=days)


# @app.get("/api/monitoring/migrations")
# async def get_migration_progress():
#     """Get migration progress information."""
#     return version_tracker.get_migration_report()


# @app.get("/api/monitoring/alerts")
# async def get_alerts():
#     """Get current alerts for version management."""
#     from app.monitoring.version_tracking import alert_manager

#     return alert_manager.check_alerts(version_tracker)


# @app.get("/api/monitoring/errors")
# async def get_error_statistics():
#     """Get error statistics and monitoring information."""
#     from app.monitoring.error_monitoring import get_active_alerts, get_error_summary

#     return {
#         "error_summary": get_error_summary(hours=24),
#         "active_alerts": [alert.dict() for alert in get_active_alerts()],
#         "timestamp": datetime.utcnow().isoformat(),
#     }


# @app.post("/api/monitoring/alerts/{alert_id}/resolve")
# async def resolve_alert(alert_id: str, resolution_message: str = "Manually resolved"):
#     """Resolve an alert."""
#     from app.monitoring.error_monitoring import resolve_alert as resolve_alert_func

#     resolve_alert_func(alert_id, resolution_message)
#     return {"message": "Alert resolved successfully", "alert_id": alert_id}


# Example of how to add version-specific endpoints
@app.get("/api/v1/version-specific")
async def v1_specific_endpoint() -> dict[str, Any]:
    """Example of a v1-specific endpoint."""
    return {
        "message": "This is a v1-specific endpoint",
        "version": "v1",
        "features": ["legacy_support", "basic_functionality"],
    }


# Future: v2-specific endpoint example
# @app.get("/api/v2/version-specific")
# async def v2_specific_endpoint():
#     """Example of a v2-specific endpoint."""
#     return {
#         "message": "This is a v2-specific endpoint",
#         "version": "v2",
#         "features": ["enhanced_security", "advanced_features", "better_performance"]
#     }


if __name__ == "__main__":
    import uvicorn

    from app.core.config import settings

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
