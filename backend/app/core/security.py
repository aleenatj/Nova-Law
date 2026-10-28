from datetime import datetime, timedelta, timezone
from typing import Any
import json
import base64
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwe
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.permissions import check_any_permission
from app.db.models import User
from app.enums.user_role import UserRoleEnum
from app.utils.dependencies import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


def get_password_hash(password: str) -> str:
    """Hash a password."""
    result: str = pwd_context.hash(password)
    return result


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None, refresh_token_id: int | None = None
) -> str:
    """Create a JWE access token with optional refresh_token_id."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    to_encode.update({"exp": int(expire.timestamp())})

    # Add refresh_token_id to the token payload if provided
    if refresh_token_id is not None:
        to_encode.update({"refresh_token_id": refresh_token_id})

    # Create JWE token
    encoded_jwe = jwe.encrypt(
        plaintext=json.dumps(to_encode).encode("utf-8"),
        key=base64.b64decode(settings.JWE_SECRET_KEY),
        encryption=settings.ENCRYPTION_ALGORITHM,
        algorithm=settings.JWE_ALGORITHM
    )
    # Decode bytes to string if necessary
    if isinstance(encoded_jwe, bytes):
        encoded_jwe = encoded_jwe.decode("utf-8")

    return str(encoded_jwe)


def create_refresh_token(data: dict[str, Any], refresh_token_id: int | None = None) -> str:
    """Create a JWE refresh token with optional refresh_token_id."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": int(expire.timestamp()), "type": "refresh"})

    # Add refresh_token_id to the token payload if provided
    if refresh_token_id is not None:
        to_encode.update({"refresh_token_id": refresh_token_id})

    encoded_jwe: str = jwe.encrypt(
        plaintext=json.dumps(to_encode).encode("utf-8"),
        key=base64.b64decode(settings.JWE_SECRET_KEY),
        encryption=settings.ENCRYPTION_ALGORITHM,
        algorithm=settings.JWE_ALGORITHM
    )
    # Decode bytes to string if necessary
    if isinstance(encoded_jwe, bytes):
        encoded_jwe = encoded_jwe.decode("utf-8")
    return str(encoded_jwe)


def create_analytics_token(data: dict[str, Any]) -> str:
    """Create a JWE analytics token."""
    to_encode = data.copy()
    # expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ANALYTICS_TOKEN_EXPIRE_MINUTES)
    # to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwe = jwe.encrypt(
        plaintext=json.dumps(to_encode).encode("utf-8"),
        key=base64.b64decode(settings.ANALYTICS_JWE_SECRET_KEY),
        encryption=settings.ENCRYPTION_ALGORITHM,
        algorithm=settings.JWE_ALGORITHM
    )
    # Decode bytes to string if necessary
    if isinstance(encoded_jwe, bytes):
        encoded_jwe = encoded_jwe.decode("utf-8")
    return str(encoded_jwe)


def create_password_token(data: dict[str, Any], token_type: str, expire_minutes: int) -> str:
    """
    Create a JWE password token with specified type and expiry.

    Args:
        data: Token payload data
        token_type: Type of token (e.g., 'password_reset', 'initial_password')
        expire_minutes: Token expiry time in minutes

    Returns:
        Encoded JWE token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": int(expire.timestamp()), "type": token_type})
    
    # Create JWE token (encrypted)
    encoded_jwe: str = jwe.encrypt(
        plaintext=json.dumps(to_encode).encode("utf-8"),
        key=base64.b64decode(settings.JWE_SECRET_KEY),
        encryption=settings.ENCRYPTION_ALGORITHM,
        algorithm=settings.JWE_ALGORITHM
    )
    # Decode bytes to string if necessary
    if isinstance(encoded_jwe, bytes):
        encoded_jwe = encoded_jwe.decode("utf-8")
    return str(encoded_jwe)


def verify_token(token: str, check_expiration: bool = True) -> dict[str, Any] | None:
    """Verify and decode a JWE token."""
    try:
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        key = base64.b64decode(settings.JWE_SECRET_KEY)
        decrypted_bytes = jwe.decrypt(token, key)
        payload = json.loads(decrypted_bytes.decode("utf-8"))
        
        # Check token expiration if requested
        if check_expiration:
            expire = payload.get("exp")
            if expire is None or expire < int(datetime.now(timezone.utc).timestamp()):
                return None
        
        return payload

    except Exception as e:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current user from JWE token."""
    message = {"success": False, "message": "Bearer token missing or unknown"}
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        key = base64.b64decode(settings.JWE_SECRET_KEY)
        decrypted_bytes = jwe.decrypt(credentials.credentials, key)
        payload = json.loads(decrypted_bytes)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Check token expiration
        expire = payload.get("exp")
        if expire is None or expire < int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as err:
        raise credentials_exception from err

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError) as err:
        raise credentials_exception from err

    user = db.query(User).options(joinedload(User.user_roles)).filter(User.id == user_id_int).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    endpoint = request.url.path
    method = request.method

    role_ids = [user_role.role_id for user_role in current_user.user_roles]

    # Check if user has any roles assigned
    if not role_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "User has no roles assigned. Please contact an administrator.",
            },
        )

    user_role = [UserRoleEnum.from_id(role_ids[0]).display_name]

    if not check_any_permission(user_role, endpoint, method):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "You do not have permission to access this resource.",
            },
        )

    if current_user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Inactive user"},
        )
    return current_user


async def validate_password_token(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
    allowed_token_types: list[str],
) -> User:
    """
    Validate password token (reset or initial password).

    Args:
        credentials: HTTP authorization credentials
        db: Database session
        allowed_token_types: List of allowed token types (e.g., ['password_reset', 'initial_password'])

    Returns:
        User object if token is valid

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    message = {"success": False, "message": "Bearer token missing or unknown"}
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Link expired or invalid. Please request a new one.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = payload.get("type")
    if not token_type:
        raise credentials_exception

    if token_type not in allowed_token_types:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    expire = payload.get("exp")
    if expire is None or expire < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Link expired, please request a new one.",
            },
        )

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError) as err:
        raise credentials_exception from err

    user = db.query(User).filter(User.id == user_id_int).first()
    if user is None:
        raise credentials_exception

    if user.status != "Active":
        raise credentials_exception

    return user


async def validate_reset_password_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """Validate reset password token. Wrapper for backward compatibility."""
    return await validate_password_token(credentials, db, ["password_reset"])


async def validate_initial_password_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """Validate initial password token. Accepts initial_password token types."""
    return await validate_password_token(
        credentials, db, ["initial_password"]
    )


async def validate_and_authorize_user(
    request: Request,
    current_user: User,
) -> User:
    """
    Common authorization logic for password token endpoints.

    Args:
        request: FastAPI request object
        current_user: User from token validation

    Returns:
        Authorized user

    Raises:
        HTTPException: If user doesn't have permission
    """
    endpoint = request.url.path
    method = request.method

    role_ids = [user_role.role_id for user_role in current_user.user_roles]
    if len(role_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "You do not have permission to access this resource.",
            },
        )

    user_role = [UserRoleEnum.from_id(role_ids[0]).display_name]

    if not check_any_permission(user_role, endpoint, method):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "You do not have permission to access this resource.",
            },
        )

    return current_user  # Return it for further use


async def get_current_user_if_provided(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    """Get current user only if valid token is provided."""
    if credentials is None:
        return None
    
    # Reuse existing get_current_user logic but catch exceptions
    try:
        user = await get_current_user(credentials, db)
        return await get_current_active_user(request, user)
    except HTTPException as e:
        raise e


async def permission_required_reset_password(
    request: Request,
    current_user: User = Depends(validate_reset_password_token),
) -> User:
    """Permission check for reset-password endpoint. Only accepts password_reset tokens."""
    return await validate_and_authorize_user(request, current_user)


async def permission_required(
    request: Request,
    current_user: User = Depends(validate_initial_password_token),
) -> User:
    """Permission check for set-initial-password endpoint. Accepts both token types."""
    return await validate_and_authorize_user(request, current_user)


def validate_analytics_token(
    token: str,
) -> dict[str, Any] | None:
    """Validate analytics token."""
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    key = base64.b64decode(settings.ANALYTICS_JWE_SECRET_KEY)
    decrypted_bytes = jwe.decrypt(token, key)
    try:
        payload = json.loads(decrypted_bytes.decode("utf-8"))
        return payload
    except Exception as e:
        return None