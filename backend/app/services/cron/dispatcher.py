from typing import Any
import json
import logging

from app.services.cron.check_non_responders import run_async as check_non_responders

logger = logging.getLogger(__name__)

async def dispatch_cron_job(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Dispatch cron jobs based on the `job` field from EventBridge input.
    
    EventBridge passes the Input JSON as the event payload, so the job name
    should be available at event.get("job") or event.get("detail", {}).get("job").
    """

    # Try to get job name from event (EventBridge Input) or detail field
    job_name = event.get("job") or event.get("detail", {}).get("job")

    if not job_name:
        logger.error("No job name provided in cron event", extra={"event_keys": list(event.keys())})
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "error",
                "message": "No job name provided in cron event",
                "event_keys": list(event.keys())
            })
        }
        
    logger.info("Cron dispatcher triggered", extra={"job": job_name})

    if job_name == "check-non-responders":
        return await check_non_responders(event=event, context=context)

    logger.error(f"Unknown cron job: {job_name}")
    return {
        "statusCode": 400,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "error",
            "message": f"Unknown cron job: {job_name}"
        })
    }
