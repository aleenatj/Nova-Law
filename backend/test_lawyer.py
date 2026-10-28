"""Build lawyer/case payload and trigger EXPERT_NOT_INTERESTED_NN_EMAIL (one email per lawyer to navigators)."""
import asyncio
import sys

from pydantic_core.core_schema import custom_error_schema
from sqlalchemy.orm import joinedload

from app.db.database import SessionLocal
from app.db.models.lawyer import Lawyer
from app.db.models.case import Case
from app.db.services.case import get_case_by_id
from app.enums.events import EventType
from app.events.subscribers.timeline import handle_case_engage_cus_card
from app.schemas.v1.event import Event
from app.websocket.manager import WebSocketManager

from datetime import datetime, timezone
def main() -> None:
    db = SessionLocal()
    try:
        lawyer_list = []
        for lawyer_id in (1, 2):
            lawyer = (
                db.query(Lawyer)
                .options(joinedload(Lawyer.user))
                .filter(Lawyer.id == lawyer_id)
                .first()
            )
            if lawyer is not None:
                lawyer_list.append(lawyer)

        if not lawyer_list:
            print("No lawyers found for id 1 or 2.")
            sys.exit(1)

        case = get_case_by_id(db, 1)
        if case is None:
            print("Case id 1 not found.")
            sys.exit(1)

        cases = [
            {
                "lawyers": lawyer_list,
                "case": case,
            }   
        ]
        customer_name = "John"
        # payload = {"cases": cases}
        payload = {
            "case": case,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_number": case.case_no,
            "lawyer": lawyer_list[0],
            "amount_requested": 2500,
            "current_user": lawyer_list[0].user,
            "customer_first_name": customer_name,
        }

        event = Event(event_type=EventType.CASE_ENGAGE_CUS_CARD, payload=payload)

        result = asyncio.run(
            handle_case_engage_cus_card(
                db=db,
                event=event,
                websocket_manager=WebSocketManager(),
            )
        )
        print("Result:", result.success, result.message)
        if result.data:
            print("Cards sent:", len(result.data))
    finally:
        db.close()


if __name__ == "__main__":
    main()
