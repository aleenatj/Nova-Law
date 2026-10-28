"""Versioning middleware for Nova Law API.

This middleware detects API versions from requests and adds version-related
headers to responses, including deprecation notices.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.versioning import version_detector, version_manager


class VersionDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware for detecting API version and adding version headers."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Detect version from request
        version = version_detector.detect_version(request)
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version headers to response
        self._add_version_headers(response, version)

        return response

    def _add_version_headers(self, response: Response, version: str) -> None:
        """Add version-related headers to response."""
        # Add API version header
        response.headers["X-API-Version"] = version

        # Add deprecation headers if version is deprecated
        deprecation_info = version_manager.get_deprecation_info(version)
        if deprecation_info:
            response.headers["Deprecation"] = "true"
            if deprecation_info.get("end_of_life"):
                response.headers["Sunset"] = deprecation_info["end_of_life"].strftime(
                    "%Y-%m-%d",
                )

        # Add latest version header
        latest_version = version_manager.get_latest_version()
        response.headers["X-Latest-API-Version"] = latest_version.value

        # Add version support header
        supported_versions = [v.value for v in version_manager.supported_versions]
        response.headers["X-Supported-Versions"] = ", ".join(supported_versions)


class VersionValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating API version support."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Get detected version
        version = getattr(request.state, "api_version", None)

        if version and not version_manager.is_supported(version):
            # Return error for unsupported versions
            return Response(
                content={
                    "error": "Unsupported API version",
                    "message": f"Version {version} is not supported",
                    "supported_versions": [
                        v.value for v in version_manager.supported_versions
                    ],
                    "recommended_version": version_manager.get_recommended_version().value,
                },
                status_code=400,
                media_type="application/json",
            )

        return await call_next(request)


class DeprecationWarningMiddleware(BaseHTTPMiddleware):
    """Middleware for adding deprecation warnings."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Process request
        response = await call_next(request)

        # Add deprecation warning if needed
        version = getattr(request.state, "api_version", None)
        if version:
            deprecation_info = version_manager.get_deprecation_info(version)
            if deprecation_info:
                self._add_deprecation_warning(response, deprecation_info)

        return response

    def _add_deprecation_warning(self, response: Response, deprecation_info: dict[str, Any]) -> None:
        """Add deprecation warning to response."""
        warning_msg = f'299 - "API version {deprecation_info["version"]} is deprecated'

        if deprecation_info.get("days_until_eol"):
            warning_msg += (
                f", will be removed in {deprecation_info['days_until_eol']} days"
            )

        warning_msg += f'. Please migrate to version {version_manager.get_recommended_version().value}."'

        # Add warning header
        response.headers["Warning"] = warning_msg
