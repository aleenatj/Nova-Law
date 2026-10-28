"""
Audit context middleware for FastAPI.

This middleware extracts user context from requests and sets it for audit logging.
"""

import json
import base64
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import Request
from jose import jwe
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.audit import clear_audit_context, set_audit_context

logger = structlog.get_logger()


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract user context from requests for audit logging.
    
    This middleware:
    1. Extracts user ID from JWT token (if present)
    2. Captures IP address from request
    3. Captures User-Agent header
    4. Sets the audit context for the duration of the request
    5. Clears the context after the request completes
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and set audit context."""
        # Extract user info
        user_id = await self._extract_user_id(request)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:500]  # Limit length
        
        # Build metadata
        metadata = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else None,
        }
        
        # Set audit context
        token = set_audit_context(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Always clear context after request
            clear_audit_context(token)
    
    async def _extract_user_id(self, request: Request) -> int | None:
        """
        Extract user ID from the JWT token in the Authorization header.
        
        Returns None if:
        - No Authorization header present
        - Invalid token format
        - Token decryption fails
        - Token doesn't contain user ID
        """
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None
        
        # Check for Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        token = parts[1]
        
        try:
            # Decrypt JWE token
            key = base64.b64decode(settings.JWE_SECRET_KEY)
            decrypted_bytes = jwe.decrypt(token, key)
            payload = json.loads(decrypted_bytes)
            
            # Extract user ID from 'sub' claim
            user_id_str = payload.get("sub")
            if user_id_str is not None:
                return int(user_id_str)
        except Exception:
            # Silently fail - this is just for audit context
            # The actual authentication middleware will handle auth errors
            pass
        
        return None
    
    def _get_client_ip(self, request: Request) -> str | None:
        """
        Get the client IP address from the request.
        
        Handles proxied requests by checking X-Forwarded-For header.
        """
        # Check for forwarded IP (from reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs; take the first one
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header (nginx)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return None


def setup_audit_middleware(app: Any) -> None:
    """
    Setup the audit context middleware on a FastAPI app.
    
    Usage:
        from app.middleware.audit import setup_audit_middleware
        
        app = FastAPI()
        setup_audit_middleware(app)
    """
    app.add_middleware(AuditContextMiddleware)

