import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.error_logging import (
    ErrorCategory,
    ErrorSeverity,
    log_api_error,
    log_error,
)


class AppError(Exception):
    """General application exception for structured error handling."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        status_code: int = 400,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


# --- Convenience Functions for Common Exceptions ---
def raise_bad_request(
    message: str = "Bad Request", error_code: str | None = None
) -> None:
    """Raise a 400 Bad Request exception."""
    raise AppError(
        message=message,
        error_code=error_code or "BAD_REQUEST",
        status_code=400,
    )


def raise_unauthorized(
    message: str = "Unauthorized", error_code: str | None = None
) -> None:
    """Raise a 401 Unauthorized exception."""
    raise AppError(
        message=message,
        error_code=error_code or "UNAUTHORIZED",
        status_code=401,
    )


def raise_forbidden(message: str = "Forbidden", error_code: str | None = None) -> None:
    """Raise a 403 Forbidden exception."""
    raise AppError(
        message=message,
        error_code=error_code or "FORBIDDEN",
        status_code=403,
    )


def raise_not_found(message: str = "Not Found", error_code: str | None = None) -> None:
    """Raise a 404 Not Found exception."""
    raise AppError(
        message=message,
        error_code=error_code or "NOT_FOUND",
        status_code=404,
    )


def raise_conflict(message: str = "Conflict", error_code: str | None = None) -> None:
    """Raise a 409 Conflict exception."""
    raise AppError(
        message=message,
        error_code=error_code or "CONFLICT",
        status_code=409,
    )


def raise_validation_error(
    message: str = "Validation Error",
    error_code: str | None = None,
) -> None:
    """Raise a 422 Validation Error exception."""
    raise AppError(
        message=message,
        error_code=error_code or "VALIDATION_ERROR",
        status_code=422,
    )


def raise_internal_error(
    message: str = "Internal Server Error",
    error_code: str | None = None,
) -> None:
    """Raise a 500 Internal Server Error exception."""
    raise AppError(
        message=message,
        error_code=error_code or "INTERNAL_SERVER_ERROR",
        status_code=500,
    )


# --- Custom Application Exception Handler ---
def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions with error logging and tracking."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": []
        },
    )


# --- HTTP Exception Handler ---
def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if exc.status_code != 422:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": extract_error_message(exc.detail),
                "data": []
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": []
        },
    )


def value_error_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": str(exc),
            "data": []
        },
    )

# --- Validation Exception Handler ---
def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Check if it's a content type issue
    # errors = exc.errors()
    # if any("body" in str(error.get("loc", [])) for error in errors):
    #     return JSONResponse(
    #         status_code=400,  # Change from 422 to 400 for content type issues
    #         content={
    #             "success": False,
    #             "message": "Request body must be valid JSON",
    #             "data": []
    #         },
    #     )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": exc.errors(),
            "data": []
        },
    )


# --- Success Response Wrapper ---
def success_response(
    data: dict, message: str = "Success", status_code: int = 200
) -> JSONResponse:
    """Standardized success response wrapper."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
        },
    )


# --- Client Error Handlers (4xx) ---
def bad_request_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": extract_error_message(exc.detail),
            "data": extract_data(exc.detail)
        },
    )


def unauthorized_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "success": False,
            "message": extract_error_message(exc.detail),
            "data": []
        },
    )


def forbidden_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "success": False,
            "message": extract_error_message(exc.detail),
            "data": []
        },
    )


def not_found_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "message": extract_error_message(exc.detail),
            "data": []
        },
    )


def not_acceptable_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        content={
            "success": False,
            "message": extract_error_message(exc.detail),
            "data": []
        },
    )


def conflict_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "message": extract_error_message(exc.detail),
            "data": extract_data(exc.detail)
        },
    )


def too_many_requests_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "message": "Too Many Requests",
            "data": []
        },
    )


# --- Server Error Handlers (5xx) ---
def internal_server_error_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": extract_error_message(exc.detail),
            "data": []
        },
    )


def bad_gateway_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "success": False,
            "message": "Bad Gateway",
            "data": []
        },
    )


def service_unavailable_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "message": "Service Unavailable",
            "data": []
        },
    )


def gateway_timeout_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "success": False,
            "message": "Gateway Timeout",
            "data": []
        },
    )


# --- Generic Exception Handler (Fallback) ---
def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with error logging and tracking."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred",
            "data": []
        },
    )


# --- Exception Handler Registry ---
EXCEPTION_HANDLERS = {
    AppError: app_exception_handler,
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    HTTPException: http_exception_handler,
    Exception: generic_exception_handler,
}

# --- Status Code Specific Handlers ---
STATUS_CODE_HANDLERS = {
    400: bad_request_exception_handler,
    401: unauthorized_exception_handler,
    403: forbidden_exception_handler,
    404: not_found_exception_handler,
    406: not_acceptable_exception_handler,
    409: conflict_exception_handler,
    429: too_many_requests_exception_handler,
    422: validation_exception_handler,
    500: internal_server_error_exception_handler,
    502: bad_gateway_exception_handler,
    503: service_unavailable_exception_handler,
    504: gateway_timeout_exception_handler,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers to the FastAPI app."""
    # Register main exception handlers
    app.add_exception_handler(AppError, app_exception_handler)
    app.add_exception_handler(ValueError, value_error_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Register status code specific handlers
    for status_code, handler in STATUS_CODE_HANDLERS.items():
        app.add_exception_handler(status_code, handler)

    # Register HTTPException handler for 422 status code
    app.add_exception_handler(422, http_exception_handler)

def extract_error_message(detail: Any) -> str:
    """Extract error message from detail.

    Handles detail as list, dict, or other types.
    """
    if (
        isinstance(detail, list)
        and detail
        and isinstance(detail[0], dict)
        and "message" in detail[0]
    ):
        return str(detail[0]["message"])
    if isinstance(detail, dict):
        # Prefer 'message' key if present, else join all values as string
        if "message" in detail:
            return str(detail["message"])
        return ", ".join(str(v) for v in detail.values())
    return str(detail)

def extract_data(detail: Any) -> dict:
    """Extract data from detail.

    Handles detail as list, dict, or other types.
    """
    if isinstance(detail, dict) and "data" in detail:
        return detail["data"]
    if isinstance(detail, list) and detail and isinstance(detail[0], dict) and "data" in detail[0]:
        return detail[0]["data"]
    return []

def _map_status_code_to_severity(status_code: int) -> ErrorSeverity:
    """Map HTTP status codes to error severity levels."""
    if status_code >= 500:
        return ErrorSeverity.HIGH
    elif status_code >= 400:
        return ErrorSeverity.MEDIUM
    else:
        return ErrorSeverity.LOW


def _map_status_code_to_category(status_code: int) -> ErrorCategory:
    """Map HTTP status codes to error categories."""
    if status_code == 401:
        return ErrorCategory.AUTHENTICATION
    elif status_code == 403:
        return ErrorCategory.AUTHORIZATION
    elif status_code == 422:
        return ErrorCategory.VALIDATION
    elif status_code == 429:
        return ErrorCategory.RATE_LIMIT
    elif status_code >= 500:
        return ErrorCategory.SYSTEM
    else:
        return ErrorCategory.UNKNOWN


# ============================================================================
# MIDDLEWARE CLASSES - Centralized Error Handling & Monitoring
# ============================================================================


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error handling and logging.

    This middleware catches exceptions during request processing and logs them
    with error tracking IDs. Note: FastAPI exception handlers will still format
    the final response, but this middleware ensures errors are logged.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request and handle errors with comprehensive logging."""
        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Log slow requests
            response_time = time.time() - start_time
            if response_time > 5.0:  # Log requests taking more than 5 seconds
                log_error(
                    error=Exception(
                        f"Slow request: {request.url.path} took {response_time:.2f}s",
                    ),
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.SYSTEM,
                    context=None,
                )

            return response

        except Exception as e:
            # Log the error but re-raise to let exception handlers format response
            response_time = time.time() - start_time

            # Determine severity and category
            if isinstance(e, AppError):
                severity = _map_status_code_to_severity(e.status_code)
                category = _map_status_code_to_category(e.status_code)
            else:
                severity = ErrorSeverity.HIGH
                category = ErrorCategory.SYSTEM

            # Log error with additional context
            error_id = log_api_error(
                error=e,
                request=request,
                severity=severity,
                category=category,
                additional_context={
                    "response_time": response_time,
                    "request_path": str(request.url.path),
                    "request_method": request.method,
                },
            )

            # Store error_id in request state for exception handlers to use
            request.state.error_id = error_id

            # Re-raise to let FastAPI exception handlers format the response
            raise


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request performance and logging slow requests."""

    def __init__(self, app: Any, slow_request_threshold: float = 2.0) -> None:
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Monitor request performance and log slow requests."""
        start_time = time.time()

        try:
            response = await call_next(request)

            # Calculate response time
            response_time = time.time() - start_time

            # Log slow requests
            if response_time > self.slow_request_threshold:
                log_error(
                    error=Exception(
                        f"Slow request detected: {request.url.path} took {response_time:.2f}s",
                    ),
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.SYSTEM,
                    context=None,
                )

            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"

            return response

        except Exception:
            # Log performance issues even for failed requests
            response_time = time.time() - start_time
            log_error(
                error=Exception(
                    f"Request failed with performance issue: {request.url.path} took {response_time:.2f}s",
                ),
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.SYSTEM,
                context=None,
            )
            raise


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request context to state for error logging."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Add request context to state for better error tracking."""
        # Add request ID to state
        request.state.request_id = str(time.time())

        # Add request start time
        request.state.start_time = time.time()

        # Add request path for context
        request.state.request_path = str(request.url.path)

        # Add request method for context
        request.state.request_method = request.method

        # Add client IP for context
        request.state.client_ip = request.client.host if request.client else "unknown"

        # Add user agent for context
        request.state.user_agent = request.headers.get("user-agent", "unknown")

        try:
            response = await call_next(request)
            return response
        except Exception:
            # Ensure request context is available for error logging
            if not hasattr(request.state, "request_id"):
                request.state.request_id = str(time.time())
            raise


class ErrorRecoveryMiddleware(BaseHTTPMiddleware):
    """Middleware for graceful error recovery and cleanup."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Handle errors gracefully with cleanup."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error for recovery analysis
            log_error(
                error=e,
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.SYSTEM,
                context=None,
            )

            # Attempt graceful recovery based on error type
            if "database" in str(e).lower():
                # Database errors - could implement retry logic here
                log_error(
                    error=Exception("Database error recovery attempted"),
                    severity=ErrorSeverity.LOW,
                    category=ErrorCategory.DATABASE,
                    context=None,
                )
            elif "network" in str(e).lower():
                # Network errors - could implement circuit breaker here
                log_error(
                    error=Exception("Network error recovery attempted"),
                    severity=ErrorSeverity.LOW,
                    category=ErrorCategory.NETWORK,
                    context=None,
                )

            # Re-raise the exception for proper handling
            raise


class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate Content-Type header for POST/PUT/PATCH requests."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Validate Content-Type header for requests with body."""
        allowed_content_types = ["application/json", "multipart/form-data", "application/x-www-form-urlencoded"]

        # Only validate Content-Type for methods that typically have a request body
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "").lower()

            # Extract the media type (without charset or other parameters)
            media_type = content_type.split(";")[0].strip()

            # Check if Content-Type is set and valid for JSON APIs
            if media_type and media_type not in allowed_content_types:
                return JSONResponse(
                    status_code=415,
                    content={
                        "success": False,
                        "message": f"Content-Type '{media_type}' is not supported. Expected 'application/json' or 'multipart/form-data'.",
                        "error_code": "UNSUPPORTED_MEDIA_TYPE",
                        "data": [],
                    },
                )

        response = await call_next(request)
        return response


# ============================================================================
# REGISTRATION FUNCTIONS
# ============================================================================


def register_error_handling_middleware(app: Any) -> None:
    """Register all error handling middleware with the FastAPI app.

    This is the centralized function to register all middleware for
    error handling, monitoring, and request context tracking.
    """
    app.add_middleware(RequestContextMiddleware)
    # app.add_middleware(PerformanceMonitoringMiddleware)  # Uncomment if needed
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(ErrorRecoveryMiddleware)
    app.add_middleware(ContentTypeValidationMiddleware)
