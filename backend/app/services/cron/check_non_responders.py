import json
from typing import Any
import logging

from app.core.error_logging import ErrorCategory, ErrorSeverity, log_error
from app.schemas.v1.event import Event
from app.enums.events import EventType
from app.events.dispatcher import event_dispatcher  
from app.db.database import SessionLocal
from app.utils.helpers import extract_status_messages

logger = logging.getLogger(__name__)


async def run_async(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """
    Find users who have not responded within 24 hours and notify admin.
    """

    logger.info("Running check-non-responders cron job")

    try:
        db = SessionLocal()
        event_type:EventType = EventType.EXPERT_NOT_INTERESTED
        payload: dict[str, Any] = {}

        # Create Event object
        event_data = Event(
            event_type=event_type,
            payload=payload,
            user_id=None,
            current_user=None,
        )

        # Always treat dispatch_event as async
        await event_dispatcher.dispatch_event(db, event_data)

        # Check success
        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        if not success:
            logger.error(f"Event dispatch failed: {messages}")
            return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Event dispatch failed"}),
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Event dispatched successfully"}),
        }


    except Exception as e:
       error_id = log_error(
           e,
           severity=ErrorSeverity.HIGH,
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
           "body": json.dumps({
               "status": "error",
               "error": "Internal server error",
               "error_code": "LAMBDA_ERROR",
               "error_id": error_id,
               "request_id": getattr(context, "aws_request_id", "unknown"),
               "function_name": getattr(context, "function_name", "unknown"),
           }),
       }

    finally:
        db.close()