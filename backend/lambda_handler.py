"""Simplified AWS Lambda Handler for Nova Law AI Backend."""

import json
import logging
import asyncio
from typing import Any

from mangum import Mangum

from app.core.error_logging import ErrorCategory, ErrorSeverity, log_error
from app.main import app
from app.db.database import SessionLocal
from app.db.services.auth import get_user_by_id
from app.schemas.v1.event import Event
from app.enums.events import EventType
from app.events.dispatcher import event_dispatcher
from app.utils.helpers import extract_status_messages
from app.services.cron.dispatcher import dispatch_cron_job

# Mangum adapter for FastAPI ASGI app
handler = Mangum(app, lifespan="off")


def run_async(coro):
   """Run async coroutine safely in AWS Lambda."""
   try:
       loop = asyncio.get_running_loop()
   except RuntimeError:
       # No running loop, create a new one
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)
   return loop.run_until_complete(coro)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
   """Main Lambda handler (synchronous, safe for async calls)."""

   try:
       # Detect EventBridge (CloudWatch Events) invocation
       # EventBridge events can have:
       # 1. source == "aws.events" (standard EventBridge event)
       # 2. Input JSON passed directly (when Input is specified in target config)
       # 3. detail-type == "Scheduled Event" (alternative detection)
       event_source = event.get("source")
       detail_type = event.get("detail-type")
       has_job_field = "job" in event
       has_request_context = "requestContext" in event
       
       # Check if this is an EventBridge scheduled event
       # When Input is specified in EventBridge target, it replaces the entire event payload
       # So we check for job field AND absence of API Gateway requestContext
       # Also check for EventBridge-specific fields
       is_eventbridge = (
           event_source == "aws.events" or
           detail_type == "Scheduled Event" or
           (has_job_field and not has_request_context) or  # Has job but no API Gateway context
           ("version" in event and "id" in event and event_source is None and not has_request_context)  # EventBridge structure without source
       )
       
       if is_eventbridge:
           # Route to scheduled job handler
           logger = logging.getLogger(__name__)
           logger.info("EventBridge event detected", extra={
               "source": event_source,
               "detail_type": detail_type,
               "has_job": has_job_field,
               "has_request_context": has_request_context,
               "event_keys": list(event.keys())[:10]  # First 10 keys for debugging
           })
           return run_async(dispatch_cron_job(event, context))
       
       # Handle custom event actions
       action = event.get("action", None)
       if action == "run_event":
           # Run async event handler safely
           return run_async(event_handler(event, context))
       else:
           # Pass normal requests to FastAPI via Mangum (API Gateway)
           return handler(event, context)

   except Exception as e:
       # Log unexpected errors
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


async def event_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
   """Async event handler for dispatching events."""

   db = SessionLocal()
   logger = logging.getLogger(__name__)

   try:
       event_type: EventType = event["event_type"]
       payload: dict[str, Any] = event["event_payload"]
       user_id: int | None = event.get("user_id", None)
       current_user_id: int | None = event.get("current_user_id", None)

       # Fetch user synchronously from DB
       current_user = get_user_by_id(db, current_user_id) if current_user_id else None

       # Create Event object
       event_data = Event(
           event_type=event_type,
           payload=payload,
           user_id=user_id,
           current_user=current_user,
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


def health_check(event: dict[str, Any], context: Any) -> dict[str, Any]:
   """Health check Lambda handler."""

   try:
       return {
           "statusCode": 200,
           "headers": {"Content-Type": "application/json"},
           "body": json.dumps({
               "status": "healthy",
               "service": "Nova Law AI Backend",
               "environment": "aws_lambda",
               "function_name": getattr(context, "function_name", "unknown"),
               "request_id": getattr(context, "aws_request_id", "unknown"),
           }),
       }
   except Exception as e:
       error_id = log_error(
           e,
           ErrorSeverity.HIGH,
           category=ErrorCategory.SYSTEM,
           lambda_context=context,
       )
       return {
           "statusCode": 503,
           "headers": {"Content-Type": "application/json"},
           "body": json.dumps({
               "status": "unhealthy",
               "error": "Health check failed",
               "error_id": error_id,
           }),
       }