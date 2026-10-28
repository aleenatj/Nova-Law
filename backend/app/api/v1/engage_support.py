"""Engage support API: POST to submit (open), GET to list (authenticated), GET export CSV."""

import io
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.models import User
from app.db.services.engage_support import (
    ALLOWED_ORDER_FIELDS,
    create_engage_support,
    engage_support_to_schema,
    export_engage_support_csv,
    get_engage_support,
    has_saveable_data,
    parse_date_range,
    engage_support_send_email,
)
from app.schemas.v1.engage_support import (
    EngageSupportCreateRequest,
    EngageSupportCreateResponse,
    EngageSupportListData,
    EngageSupportListRequest,
    EngageSupportListResponse,
)
from app.utils.dependencies import get_db
from app.utils.validators import validate_order_params

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/engage-support/export")
def export_engage_support_csv_endpoint(
    list_request: EngageSupportListRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export engage support submissions to CSV. Navigator only."""
    validate_order_params(
        list_request.order_by,
        list_request.order_dir,
        ALLOWED_ORDER_FIELDS,
    )
    body, filename = export_engage_support_csv(db, list_request)
    return StreamingResponse(
        io.BytesIO(body),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/engage-support", response_model=EngageSupportCreateResponse)
async def create_support(
    request: EngageSupportCreateRequest,
    db: Session = Depends(get_db),
) -> EngageSupportCreateResponse:
    """Submit engage support request (open endpoint). Returns all saved data with encrypted id."""
    payload = {k: v for k, v in request.model_dump().items() if v is not None}
    if not has_saveable_data(payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "No data to be saved"},
        )

    try:
        support = create_engage_support(db, payload)
        await engage_support_send_email(support)
        return EngageSupportCreateResponse(
            success=True,
            message=[{"success": True, "message": "Support request submitted successfully"}],
            data=engage_support_to_schema(support),
        )
    except Exception:
        logger.exception("Failed to create engage support submission")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save support request",
        ) from None


@router.get("/engage-support", response_model=EngageSupportListResponse)
def list_engage_support(
    list_request: EngageSupportListRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EngageSupportListResponse:
    """List engage support submissions with pagination and date filtering. Navigator only."""
    validate_order_params(
        list_request.order_by,
        list_request.order_dir,
        ALLOWED_ORDER_FIELDS,
    )
    start_dt, end_dt = parse_date_range(list_request.start_date, list_request.end_date)
    results, total_count = get_engage_support(
        db,
        page=list_request.page,
        limit=list_request.limit,
        order_by=list_request.order_by,
        order_dir=list_request.order_dir,
        start_date=start_dt,
        end_date=end_dt,
        paginate=True,
    )
    items = [engage_support_to_schema(r) for r in results]
    return EngageSupportListResponse(
        success=True,
        message=[{"success": True, "message": "Engage support list retrieved"}],
        data=EngageSupportListData(
            total_count=total_count,
            records_in_page=len(items),
            items=items,
        ),
    )
