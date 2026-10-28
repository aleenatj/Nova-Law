"""AWS Lambda Handler for Database Migrations.

This Lambda function handles database migrations using Alembic.
It can be triggered manually or as part of the deployment workflow.
"""

import json
from typing import Any

from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.core.error_logging import ErrorCategory, ErrorSeverity, log_error
from app.db.database import engine


def run_migrations() -> dict[str, Any]:
    """Run database migrations using Alembic.

    Returns:
        Dictionary with migration results
    """
    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")

        # Set the database URL from settings, handling special characters
        database_url = settings.database_url
        # Escape any special characters that might cause interpolation issues
        database_url = database_url.replace("%", "%%")

        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        # Run the migration
        command.upgrade(alembic_cfg, "head")

        return {
            "success": True,
            "message": "Database migrations completed successfully",
            "current_revision": "head",
        }

    except Exception as e:
        return {"success": False, "error": str(e), "error_type": type(e).__name__}


def verify_database_connection() -> dict[str, Any]:
    """Verify database connection is working.

    Returns:
        Dictionary with connection status
    """
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        return {"success": True, "message": "Database connection verified successfully"}

    except Exception as e:
        return {"success": False, "error": str(e), "error_type": type(e).__name__}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda handler for database migrations.

    Args:
        event: Lambda event containing migration parameters
        context: Lambda context

    Returns:
        API Gateway response with migration results
    """
    try:
        # Log the event for debugging
        # print(f"Migration Lambda triggered with event: {json.dumps(event)}")

        # Determine action from event
        action = event.get("action", "migrate")

        if action == "verify":
            result = verify_database_connection()
        elif action == "migrate":
            result = run_migrations()
        else:
            result = {
                "success": False,
                "error": f"Unknown action: {action}",
                "supported_actions": ["migrate", "verify"],
            }

        # Log the result
        # print(f"Migration result: {json.dumps(result)}")

        # Return success response
        if result.get("success"):
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "X-Function-Name": getattr(context, "function_name", "unknown"),
                    "X-Request-ID": getattr(context, "aws_request_id", "unknown"),
                },
                "body": json.dumps(
                    {
                        "status": "success",
                        "action": action,
                        "result": result,
                        "request_id": getattr(context, "aws_request_id", "unknown"),
                        "function_name": getattr(context, "function_name", "unknown"),
                    }
                ),
            }
        else:
            # Return error response
            error_id = log_error(
                error=Exception(result.get("error", "Unknown migration error")),
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DATABASE,
                lambda_context=context,
            )

            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "X-Error-ID": error_id,
                    "X-Function-Name": getattr(context, "function_name", "unknown"),
                    "X-Request-ID": getattr(context, "aws_request_id", "unknown"),
                },
                "body": json.dumps(
                    {
                        "status": "error",
                        "action": action,
                        "error": result.get("error", "Unknown error"),
                        "error_type": result.get("error_type", "UnknownError"),
                        "error_id": error_id,
                        "request_id": getattr(context, "aws_request_id", "unknown"),
                        "function_name": getattr(context, "function_name", "unknown"),
                    }
                ),
            }

    except Exception as e:
        # Log unexpected errors
        error_id = log_error(
            error=e,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            lambda_context=context,
        )

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Error-ID": error_id,
                "X-Function-Name": getattr(context, "function_name", "unknown"),
                "X-Request-ID": getattr(context, "aws_request_id", "unknown"),
            },
            "body": json.dumps(
                {
                    "status": "error",
                    "error": "Internal server error during migration",
                    "error_code": "MIGRATION_LAMBDA_ERROR",
                    "error_id": error_id,
                    "request_id": getattr(context, "aws_request_id", "unknown"),
                    "function_name": getattr(context, "function_name", "unknown"),
                }
            ),
        }


# Health check handler for migration Lambda
def migration_health_check(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Health check for migration Lambda."""
    try:
        # Test database connection
        connection_result = verify_database_connection()

        if connection_result["success"]:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "status": "healthy",
                        "service": "Nova Law Migration Lambda",
                        "database_connection": "connected",
                        "environment": "aws_lambda",
                        "function_name": getattr(context, "function_name", "unknown"),
                        "request_id": getattr(context, "aws_request_id", "unknown"),
                    }
                ),
            }
        else:
            return {
                "statusCode": 503,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "status": "unhealthy",
                        "service": "Nova Law Migration Lambda",
                        "database_connection": "disconnected",
                        "error": connection_result.get(
                            "error", "Unknown database error"
                        ),
                        "function_name": getattr(context, "function_name", "unknown"),
                        "request_id": getattr(context, "aws_request_id", "unknown"),
                    }
                ),
            }

    except Exception as e:
        error_id = log_error(
            e,
            ErrorSeverity.HIGH,
            ErrorCategory.SYSTEM,
            lambda_context=context,
        )

        return {
            "statusCode": 503,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "status": "unhealthy",
                    "error": "Health check failed",
                    "error_id": error_id,
                }
            ),
        }
