"""Centralized Error Logging System for Nova Law AI Backend.

Simplified logging setup:
- Logs to stdout/stderr in AWS Lambda and prod/stage (CloudWatch captures this automatically).
- Logs to rotating files in local development.
- Uses Python standard logging module.
"""

import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog
from fastapi import Request
from pydantic import BaseModel

from app.enums import ErrorCategory, ErrorSeverity


class ErrorContext(BaseModel):
    """Context information for error logging."""

    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    endpoint: str | None = None
    method: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    api_version: str | None = None
    aws_request_id: str | None = None
    function_name: str | None = None
    function_version: str | None = None
    memory_limit_mb: int | None = None
    remaining_time_ms: int | None = None
    cold_start: bool | None = None
    additional_data: dict[str, Any] | None = None


class ErrorLogEntry(BaseModel):
    """Structured error log entry."""

    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: str
    message: str
    details: str | None = None
    stack_trace: str | None = None
    context: ErrorContext
    performance_data: dict[str, Any] | None = None


def setup_logger() -> logging.Logger:
    """Setup logger with clean, readable format without color codes."""
    logger = logging.getLogger("nova_law_ai")
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Simple, clean format: DATE | LEVEL | MODULE | MESSAGE
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Build handler
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("APP_ENV", "").lower() in (
        "prod",
        "stage",
    ):
        handler = logging.StreamHandler(sys.stdout)
    else:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        handler = RotatingFileHandler(  # type: ignore[assignment]
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logger()
# Configure structlog to delegate to standard logging with plain formatting
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)
struct_logger = structlog.get_logger("nova_law_ai")


class CentralizedErrorLogger:
    """Unified error logging system with simplified CloudWatch integration via stdout."""

    def __init__(self) -> None:
        self.logger = logger
        self.structlogger = struct_logger
        self.error_counters: dict[str, int] = {}
        self.severity_counters: dict[ErrorSeverity, int] = dict.fromkeys(
            ErrorSeverity, 0
        )
        self.category_counters: dict[ErrorCategory, int] = dict.fromkeys(
            ErrorCategory, 0
        )
        self._lambda_context: Any = None

    def _is_lambda_environment(self) -> bool:
        return bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

    def set_lambda_context(self, lambda_context: Any) -> None:
        self._lambda_context = lambda_context

    def log_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: ErrorContext | None = None,
        request: Request | None = None,
        performance_data: dict[str, Any] | None = None,
        lambda_context: Any | None = None,
    ) -> str:
        error_id = str(uuid4())

        if lambda_context:
            self.set_lambda_context(lambda_context)

        if request and not context:
            context = self._extract_context_from_request(request)
        elif not context:
            context = ErrorContext()

        if self._is_lambda_environment():
            context = self._add_lambda_context(context)

        error_entry = ErrorLogEntry(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            severity=severity,
            category=category,
            error_type=type(error).__name__,
            message=str(error),
            details=self._get_error_details(error),
            stack_trace=self._get_stack_trace(error),
            context=context,
            performance_data=performance_data,
        )

        # Log structured with structlog, also fallback to standard logging
        self._log_structured_error(error_entry)

        # Also print to stderr on critical
        if error_entry.severity == ErrorSeverity.CRITICAL:
            print(f"CRITICAL ERROR: {error_entry.error_id}", file=sys.stderr)

        self._update_counters(error_entry)

        return error_id

    def _log_structured_error(self, error_entry: ErrorLogEntry) -> None:
        log_data = {
            "error_id": error_entry.error_id,
            "severity": error_entry.severity.value,
            "category": error_entry.category.value,
            "error_type": error_entry.error_type,
            "message": error_entry.message,
            "timestamp": error_entry.timestamp.isoformat(),
            "context": error_entry.context.dict(),
        }
        if error_entry.details:
            log_data["details"] = error_entry.details
        if error_entry.performance_data:
            log_data["performance"] = error_entry.performance_data

        # Use structlog (which outputs to standard logging)
        if error_entry.severity == ErrorSeverity.CRITICAL:
            self.structlogger.critical("Critical error occurred", **log_data)
        elif error_entry.severity == ErrorSeverity.HIGH:
            self.structlogger.error("High severity error", **log_data)
        elif error_entry.severity == ErrorSeverity.MEDIUM:
            self.structlogger.warning("Medium severity error", **log_data)
        else:
            self.structlogger.info("Low severity error", **log_data)

    def log_info(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.logger.info(message, extra=context or {})

    def log_debug(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.logger.debug(message, extra=context or {})

    def log_performance_metrics(
        self,
        operation: str,
        duration_ms: float,
        memory_used_mb: float | None = None,
        additional_metrics: dict[str, Any] | None = None,
    ) -> None:
        self.logger.info(
            "Performance metrics",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "memory_used_mb": memory_used_mb,
                "additional_metrics": additional_metrics,
            },
        )

    def log_cold_start(self, function_name: str, duration_ms: float) -> None:
        self.logger.info(
            f"Cold start detected: {function_name}, duration: {duration_ms:.2f}ms"
        )

    def _extract_context_from_request(self, request: Request) -> ErrorContext:
        user_id = getattr(request.state, "user_id", None)
        session_id = getattr(request.state, "session_id", None)
        api_version = getattr(request.state, "api_version", None)
        return ErrorContext(
            user_id=user_id,
            session_id=session_id,
            request_id=str(uuid4()),
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            api_version=api_version,
        )

    def _add_lambda_context(self, context: ErrorContext) -> ErrorContext:
        if self._lambda_context:
            context.aws_request_id = getattr(
                self._lambda_context, "aws_request_id", None
            )
            context.function_name = getattr(self._lambda_context, "function_name", None)
            context.function_version = getattr(
                self._lambda_context, "function_version", None
            )
            context.memory_limit_mb = getattr(
                self._lambda_context, "memory_limit_in_mb", None
            )
            context.remaining_time_ms = getattr(
                self._lambda_context, "get_remaining_time_in_millis", lambda: None
            )()
            context.cold_start = getattr(self._lambda_context, "cold_start", False)
        else:
            context.aws_request_id = os.getenv("_X_AMZN_TRACE_ID")
            context.function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME")
            context.function_version = os.getenv("AWS_LAMBDA_FUNCTION_VERSION")
            context.memory_limit_mb = int(
                os.getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "0")
            )
        return context

    def _get_error_details(self, error: Exception) -> str | None:
        try:
            if hasattr(error, "detail"):
                return str(error.detail)
            elif hasattr(error, "args") and error.args:
                return str(error.args[0])
            return None
        except Exception:
            return None

    def _get_stack_trace(self, error: Exception) -> str | None:
        try:
            return "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
        except Exception:
            return None

    def _update_counters(self, error_entry: ErrorLogEntry) -> None:
        error_type = error_entry.error_type
        self.error_counters[error_type] = self.error_counters.get(error_type, 0) + 1
        self.severity_counters[error_entry.severity] += 1
        self.category_counters[error_entry.category] += 1

    def get_error_statistics(self) -> dict[str, Any]:
        return {
            "total_errors": sum(self.error_counters.values()),
            "error_types": self.error_counters,
            "severity_distribution": {
                sev.value: count for sev, count in self.severity_counters.items()
            },
            "category_distribution": {
                cat.value: count for cat, count in self.category_counters.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def reset_counters(self) -> None:
        self.error_counters.clear()
        self.severity_counters = dict.fromkeys(ErrorSeverity, 0)
        self.category_counters = dict.fromkeys(ErrorCategory, 0)


# Global error logger instance
error_logger = CentralizedErrorLogger()


def log_error(
    error: Exception,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    context: ErrorContext | None = None,
    request: Request | None = None,
    performance_data: dict[str, Any] | None = None,
    lambda_context: Any | None = None,
) -> str:
    return error_logger.log_error(
        error=error,
        severity=severity,
        category=category,
        context=context,
        request=request,
        performance_data=performance_data,
        lambda_context=lambda_context,
    )


def log_api_error(
    error: Exception,
    request: Request,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.API,
    additional_context: dict[str, Any] | None = None,
) -> str:
    context = error_logger._extract_context_from_request(request)
    if additional_context:
        context.additional_data = additional_context

    return log_error(
        error=error,
        severity=severity,
        category=category,
        context=context,
    )


def log_database_error(
    error: Exception,
    operation: str,
    table: str | None = None,
    query: str | None = None,
    context: ErrorContext | None = None,
) -> str:
    if not context:
        context = ErrorContext()

    additional_data = {
        "operation": operation,
        "table": table,
        "query": query,
    }
    context.additional_data = additional_data

    return log_error(
        error=error,
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.DATABASE,
        context=context,
    )


def log_performance_metrics(
    operation: str,
    duration_ms: float,
    memory_used_mb: float | None = None,
    additional_metrics: dict[str, Any] | None = None,
) -> None:
    error_logger.log_performance_metrics(
        operation,
        duration_ms,
        memory_used_mb,
        additional_metrics,
    )


def log_cold_start(function_name: str, duration_ms: float) -> None:
    error_logger.log_cold_start(function_name, duration_ms)


def log_info(message: str, context: dict[str, Any] | None = None) -> None:
    error_logger.log_info(message, context)


def log_debug(message: str, context: dict[str, Any] | None = None) -> None:
    error_logger.log_debug(message, context)


def get_error_statistics() -> dict[str, Any]:
    return error_logger.get_error_statistics()


def is_lambda_environment() -> bool:
    return error_logger._is_lambda_environment()
