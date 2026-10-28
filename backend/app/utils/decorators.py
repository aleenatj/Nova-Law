"""Custom decorators for the Nova Law AI application."""

import asyncio
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

from app.enums.error import ErrorCode
from app.utils.constants import ERROR_MESSAGES

logger = logging.getLogger(__name__)


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time.

    Args:
    ----
        func: Function to decorate

    Returns:
    -------
        Decorated function

    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time

        logger.info(
            f"Function {func.__name__} executed in {execution_time:.4f} seconds",
        )
        return result

    return wrapper


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable], Callable]:
    """Decorator to retry function on specific exceptions.

    Args:
    ----
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry

    Returns:
    -------
        Decorated function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay} seconds...",
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.exception(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}",
                        )

            if last_exception:
                raise last_exception
            raise Exception("All retry attempts failed")

        return wrapper

    return decorator


def validate_input_types(**type_hints: type) -> Callable[[Callable], Callable]:
    """Decorator to validate input parameter types.

    Args:
    ----
        **type_hints: Type hints for function parameters

    Returns:
    -------
        Decorated function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate types
            for param_name, expected_type in type_hints.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
                            f"got {type(value).__name__}",
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_permissions(required_permissions: list[str]) -> Callable[[Callable], Callable]:
    """Decorator to require specific permissions.

    Args:
    ----
        required_permissions: List of required permissions

    Returns:
    -------
        Decorated function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # This would typically check the current user's permissions
            # For now, we'll just log the requirement
            logger.info(f"Checking permissions: {required_permissions}")

            # TODO: Implement actual permission checking logic
            # user_permissions = get_current_user_permissions()
            # if not all(perm in user_permissions for perm in required_permissions):
            #     raise HTTPException(
            #         status_code=status.HTTP_403_FORBIDDEN,
            #         detail=ERROR_MESSAGES["INSUFFICIENT_PERMISSIONS"]
            #     )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_result(ttl: int = 3600, key_prefix: str = "") -> Callable[[Callable], Callable]:
    """Decorator to cache function results.

    Args:
    ----
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key

    Returns:
    -------
        Decorated function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key (unused for now)
            _cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # TODO: Implement actual caching logic
            # cached_result = cache.get(_cache_key)
            # if cached_result is not None:
            #     return cached_result

            result = func(*args, **kwargs)

            # TODO: Store result in cache
            # cache.set(_cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def handle_database_errors(func: Callable) -> Callable:
    """Decorator to handle database-related errors gracefully.

    Args:
    ----
        func: Function to decorate

    Returns:
    -------
        Decorated function

    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Database error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "error": ERROR_MESSAGES["DATABASE_ERROR"],
                    "error_code": ErrorCode.DATABASE_ERROR,
                },
            ) from e

    return wrapper


def validate_response_schema(schema_class: type) -> Callable[[Callable], Callable]:
    """Decorator to validate function response against a Pydantic schema.

    Args:
    ----
        schema_class: Pydantic schema class to validate against

    Returns:
    -------
        Decorated function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            # Validate result against schema
            try:
                if isinstance(result, dict):
                    validated_result = schema_class(**result)
                else:
                    # Try model_validate first (Pydantic v2), fallback to parse_obj (Pydantic v1)
                    try:
                        validated_result = schema_class.model_validate(result)
                    except AttributeError:
                        # Fallback to Pydantic v1
                        validated_result = schema_class.parse_obj(result)

                return validated_result
            except Exception as e:
                logger.exception(f"Response validation error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "status": "error",
                        "error": "Response validation failed",
                        "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
                    },
                ) from e

        return wrapper

    return decorator


def rate_limit(requests_per_minute: int = 60) -> Callable[[Callable], Callable]:
    """Decorator to implement rate limiting.

    Args:
    ----
        requests_per_minute: Maximum requests per minute

    Returns:
    -------
        Decorated function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # TODO: Implement actual rate limiting logic
            # This would typically check against a database or in-memory store
            logger.info(
                f"Rate limiting check for {func.__name__}: {requests_per_minute} req/min",
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def async_retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable], Callable]:
    """Async decorator to retry function on specific exceptions.

    Args:
    ----
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry

    Returns:
    -------
        Decorated async function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay} seconds...",
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.exception(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}",
                        )

            if last_exception:
                raise last_exception
            raise Exception("All retry attempts failed")

        return wrapper

    return decorator


def deprecated(reason: str = "This function is deprecated") -> Callable[[Callable], Callable]:
    """Decorator to mark functions as deprecated.

    Args:
    ----
        reason: Reason for deprecation

    Returns:
    -------
        Decorated function

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import warnings

            warnings.warn(
                f"{func.__name__} is deprecated: {reason}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def singleton(cls: type) -> type:
    """Decorator to implement singleton pattern.

    Args:
    ----
        cls: Class to make singleton

    Returns:
    -------
        Singleton class

    """
    instances: dict[type, Any] = {}

    def get_instance(*args: Any, **kwargs: Any) -> Any:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
