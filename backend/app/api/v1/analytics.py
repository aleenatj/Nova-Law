import io
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.services.analytics import (
    AnalyticsCaptureValidationError,
    build_analytics_report_excel,
    create_analytics_deletion_request,
    get_analytics_data,
    get_distinct_landing_pages,
    save_email_cta_analytics_event,
    save_frontend_analytics_capture,
)
from app.enums.analytics import AnalyticsEvents
from app.enums.events import EventType
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.analytics import (
    AnalyticsCampaignContext,
    AnalyticsEventContext,
    AnalyticsLandingPagesData,
    AnalyticsReportData,
    DeleteAnalyticsRequest,
    DeleteAnalyticsResponse,
    GetAnalyticsLandingPagesRequest,
    GetAnalyticsLandingPagesResponse,
    GetAnalyticsRequest,
    GetAnalyticsResponse,
    SubmitAnalyticsRequest,
    SubmitAnalyticsResponse,
)
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.event import Event
from app.utils.dependencies import get_db
from app.utils.encryption import decrypt_id
from app.utils.helpers import extract_status_messages
from app.core.security import get_current_active_user
from app.db.models.user import User
logger = logging.getLogger(__name__)

router = APIRouter()


def _parse_optional_encrypted_id(
    value: str | int | None,
    *,
    field_name: str,
) -> int | None:
    """Decrypt AES-hex ids from the client; plain integers or digit strings pass through."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    decrypted = decrypt_id(s, None)
    if decrypted is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"success": False, "message": f"Invalid {field_name}"}],
        )
    try:
        return int(decrypted)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"success": False, "message": f"Invalid {field_name}"}],
        ) from None


# def _raise_forbidden_error(detail: list[dict[str, object]]) -> None:
#     """Raise HTTPException for unauthorized access."""
#     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# def _raise_bad_request_error(detail: str) -> None:
#     """Raise HTTPException for bad request."""
#     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post("/analytics", response_model=SubmitAnalyticsResponse)
async def submit_analytics_data(
    request: SubmitAnalyticsRequest,
    db: Session = Depends(get_db),
) -> SubmitAnalyticsResponse:
    """Submit Analytics data for the user."""
    from app.core.security import validate_analytics_token
    from app.db.services.customer import get_customer_by_user_id
    from app.db.services.case import get_case_by_customer_id
    try:
        payload = None
        user_id_int = None
        case_id_int = None
        if request.event_name and request.event_name.strip():
            user_id_int = _parse_optional_encrypted_id(
                request.user_id, field_name="user_id"
            )
            case_id_int = _parse_optional_encrypted_id(
                request.case_id, field_name="case_id"
            )
            if request.event_name == AnalyticsEvents.EMAIL_CTA_CLICKED.value:
                token = request.token if request.token else None
                if token is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=[{"success": False, "message": "Invalid token"}],
                    )
                payload = validate_analytics_token(request.token)
                if payload is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=[{"success": False, "message": "Invalid token"}],
                    )
                if request.context is None:
                    request.context = AnalyticsEventContext()
                if request.context.campaign is None:
                    request.context.campaign = AnalyticsCampaignContext()
                request.context.campaign.source = "email"

            try:
                save_frontend_analytics_capture(
                    db,
                    event_name=request.event_name.strip(),
                    timestamp=request.timestamp,  # type: ignore[arg-type]
                    anonymous_id=request.anonymous_id,  # type: ignore[arg-type]
                    session_id=request.session_id,  # type: ignore[arg-type]
                    user_id=user_id_int,
                    case_id=case_id_int,
                    context=request.context.model_dump(exclude_none=True)
                    if request.context
                    else None,
                    properties_traits=dict(request.properties.traits),
                    properties_event_data=dict(request.properties.event_data),
                )
            except AnalyticsCaptureValidationError as err:
                raise HTTPException(
                    status_code=err.status_code,
                    detail=[
                        {"success": False, "message": err.message},
                    ],
                ) from err


            if request.event_name == AnalyticsEvents.EMAIL_CTA_CLICKED.value:
                
                event_type = payload.get("event_type")
                timestamp = datetime.now(timezone.utc).isoformat()
                payload["timestamp"] = timestamp
                payload["case_id"] = payload.get("case_id") if payload.get("case_id") is not None else case_id_int
                if user_id_int is not None:
                    customer = get_customer_by_user_id(db, user_id_int)
                    cases = customer.case_customers
                    if cases is not None:
                        case_customer = cases[0]
                        if case_customer is not None:
                            payload["case_id"] = case_customer.case_id

                if payload.get("case_id") is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=[{"success": False, "message": "Case ID is missing either in token payload or in request"}],
                    )

                if event_type is not None:
                    if event_type == EventType.EMAIL_CTA_CLICKED.value:
                        event_data = Event(
                            event_type=EventType.EMAIL_CTA_CLICKED,
                            payload=payload,
                            user_id=None,
                            current_user=None,
                        )
                        await event_dispatcher.dispatch_event(db, event_data)
                        success, messages = extract_status_messages(event_data.response)
                        if not success:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST, detail=messages
                            )
                        return SubmitAnalyticsResponse(success=True, message=messages, data={})

            return SubmitAnalyticsResponse(
                success=True,
                message=[
                    ResponseMessage(
                        success=True,
                        message="Analytics event recorded",
                    )
                ],
                data={},
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"success": False, "message": "Invalid event name"}],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in submit_analytics_data: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=[{"success": False, "message": "Failed to submit analytics data"}]) from e


@router.delete("/analytics", response_model=DeleteAnalyticsResponse)
async def delete_analytics_data(
    request: DeleteAnalyticsRequest,
    db: Session = Depends(get_db),
) -> DeleteAnalyticsResponse:
    """Queue an analytics deletion request."""
    try:
        try:
            row = create_analytics_deletion_request(
                db,
                subject_type=request.subject_type,
                subject_id=request.subject_id,
                reason=request.reason,
                status=request.status,
            )
        except AnalyticsCaptureValidationError as err:
            raise HTTPException(
                status_code=err.status_code,
                detail=[{"success": False, "message": err.message}],
            ) from err
        return DeleteAnalyticsResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True,
                    message="Analytics deletion request queued successfully",
                )
            ],
            data={"request_id": row.request_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in delete_analytics_data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"success": False, "message": "Failed to queue analytics deletion request"}],
        ) from e


@router.get("/analytics/landing-pages", response_model=GetAnalyticsLandingPagesResponse)
async def get_analytics_landing_pages(
    request: GetAnalyticsLandingPagesRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GetAnalyticsLandingPagesResponse:
    """Distinct landing page paths in the date range (navigator only)."""
    _ = current_user
    try:
        page_paths = get_distinct_landing_pages(
            db,
            request.start_date,
            request.end_date,
        )
        return GetAnalyticsLandingPagesResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True,
                    message="Landing pages fetched successfully",
                )
            ],
            data=AnalyticsLandingPagesData(page_paths=page_paths),
        )
    except Exception as e:
        logger.exception(f"Error in get_analytics_landing_pages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[
                {"success": False, "message": "Failed to fetch landing pages"},
            ],
        ) from e


@router.get("/analytics", response_model=GetAnalyticsResponse)
async def get_analytics_report(
    request: GetAnalyticsRequest = Depends(),
    db: Session = Depends(get_db),    
    current_user: User = Depends(get_current_active_user),
) -> GetAnalyticsResponse:
    """Analytics report data — end-to-end, resolve, alignment check, and high intent funnels."""
    try:
        raw = get_analytics_data(
            db,
            request.start_date,
            request.end_date,
            source=request.source,
            landing_page=request.landing_page,
            status=request.status,
            compare=request.compare,
            period=request.period,
        )
        data = AnalyticsReportData.model_validate(raw)
        return GetAnalyticsResponse(
            success=True,
            message=[
                ResponseMessage(success=True, message="Analytics data fetched successfully")
            ],
            data=data,
        )
    except Exception as e:
        logger.exception(f"Error in get_analytics_report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"success": False, "message": "Failed to fetch analytics data"}],
        ) from e


@router.get("/analytics-report")
async def download_analytics_report(
    request: GetAnalyticsRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download the analytics report as Excel (.xlsx)."""
    try:
        raw = get_analytics_data(
            db,
            request.start_date,
            request.end_date,
            source=request.source,
            landing_page=request.landing_page,
            status=request.status,
            compare=request.compare,
            period=request.period,
        )
        data = AnalyticsReportData.model_validate(raw)
        body, filename = build_analytics_report_excel(request, data)
        _ = current_user
        return StreamingResponse(
            io.BytesIO(body),
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in download_analytics_report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"success": False, "message": "Failed to download analytics report"}],
        ) from e
