"""
Password Reset Event Handlers

This module contains the password reset event handler functions.
It demonstrates the event-driven architecture using enums for type safety.

All event handlers are decorated with @event and automatically registered.
"""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import email_service
from app.core.security import create_password_token
from app.db.services.auth import get_user_by_email
from app.db.services.user import get_user_by_id
from app.enums.events import EventType
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event
from app.schemas.v1.event import Event, EventResponseData
from app.utils.validators import validate_event_payload
from app.websocket.manager import WebSocketManager
from app.utils.formatters import extract_name_parts
from app.enums.base import NameExtractionOption

logger = logging.getLogger(__name__)


@event(EventType.PASSWORD_RESET_REQUESTED)
async def handle_password_reset_requested(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle password reset request: Generate token and reset link.
    """
    try:
        payload = event.payload
        required_keys = [{"forgot_password_request": ["email"]}]
        validation = validate_event_payload(payload, required_keys)
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        # Check if user exists
        user = get_user_by_email(db, payload["forgot_password_request"].email)
        if not user:
            raise ValueError(  # noqa: TRY301
                f"User not found for email: {payload['forgot_password_request'].email}"
            )

        if user.status != "Active":
            raise ValueError(  # noqa: TRY301
                f"User is not active: {payload['forgot_password_request'].email}"
            )

        token = create_password_token(data={"sub": str(user.id)}, token_type="password_reset", expire_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        event.payload["token"] = token
        event.payload["reset_link"] = reset_link
        event.payload["user_id"] = user.id
        event.payload["username"] = user.first_name + " " + user.last_name or "User"
        event.payload["email"] = user.email

        return EventResponseData(
            success=True,
            message="Password reset token generated successfully",
            data={"token": token, "reset_link": reset_link},
        )

    except Exception as e:
        logger.exception(f"Error in handle_password_reset_requested: {e}")
        raise


@event(EventType.SEND_PASSWORD_RESET_EMAIL)
async def send_password_reset_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send password reset email to user with reset link.
    """
    try:
        payload = event.payload
        required_keys = ["email", "reset_link"]
        validation = validate_event_payload(payload, required_keys)
        if not validation["status"]:
            raise ValueError("Email or reset link not found in payload")  # noqa: TRY301

        email = payload.get("email", "No email found")
        username = payload.get("username", "")
        username = extract_name_parts(username, NameExtractionOption.FIRST)
        reset_link = payload.get("reset_link", "No reset link found")

        # Send password reset email using the enhanced payload
        await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.PASSWORD_RESET,
            context={
                "username": username,
                "reset_link": reset_link,
                "header_subtitle": "Password Reset Request",
                "expiry_hours": (settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES or 15),
            },
        )

        return EventResponseData(
            success=True, message="Password reset email sent.", data={}
        )
    except Exception as e:
        logger.exception(f"Error in send_password_reset_email: {e}")
        raise


@event(EventType.INITIAL_PASSWORD_LINK_SENT)
async def handle_initial_password_link_sent(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle initial password setup for new lawyers and navigators.
    Generate token and send email with link to set password.
    Only sends email to Active users.
    """
    try:
        payload = event.payload
        required_keys = ["user_id"]
        validation = validate_event_payload(payload, required_keys)
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        # Get user by ID
        user_id = payload.get("user_id")
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError(  # noqa: TRY301
                f"User not found for ID: {user_id}"
            )

        # Only send email to Active users
        if user.status != "Active":
            logger.warning(
                f"Skipping initial password email for inactive user: {user.email}"
            )
            return EventResponseData(
                success=False,
                message="User is not active, email not sent",
                data={},
            )

        # Generate initial password token with 24-hour expiry
        token = create_password_token(data={"sub": str(user.id)}, token_type="initial_password", expire_minutes=settings.INITIAL_PASSWORD_TOKEN_EXPIRE_MINUTES)

        # Create link for setting initial password (frontend will handle this)
        set_password_link = f"{settings.FRONTEND_URL}/set-initial-password?token={token}"

        username = f"{user.first_name} {user.last_name}" or "User"
        username = extract_name_parts(username, NameExtractionOption.FIRST)

        # Get user role
        user_role = "User"
        if user.user_roles:
            role_id = user.user_roles[0].role_id
            user_role = UserRoleEnum.from_id(role_id).display_name
        
        if user_role == "Lawyer":
            user_role = "Expert"

        from app.utils.helpers import format_expiry_time
        expiry_time = format_expiry_time(settings.INITIAL_PASSWORD_TOKEN_EXPIRE_MINUTES)
        # Send initial password setup email
        await email_service.send_email(
            to_email=user.email,
            template=email_service.EmailTemplate.INITIAL_PASSWORD_SETUP,
            context={
                "username": username,
                "reset_link": set_password_link,
                "header_subtitle": "Set Your Password",
                "expiry_time": expiry_time["formatted"],
                "user_role": user_role,
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            should_display = False

        return EventResponseData(
            success=True,
            should_display=should_display,
            message="Initial password setup email sent successfully",
            data={"token": token, "set_password_link": set_password_link},
        )

    except Exception as e:
        logger.exception(f"Error in handle_initial_password_link_sent: {e}")
        raise


@event(EventType.RESEND_INITIAL_PASSWORD_EMAIL_AFTER_EXPIRY)
async def handle_resend_initial_password_email_after_expiry(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle resending initial password setup email.
    Generate token and send reminder email with link to set password.
    Only sends email to Active users with null password.
    """
    try:
        payload = event.payload
        required_keys = ["user"]
        validation = validate_event_payload(payload, required_keys)
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        # Get user by ID
        user = payload.get("user")
        if not user:
            raise ValueError(  # noqa: TRY301
                f"User not found for ID: {user.id}"
            )

        # Generate initial password token with 24-hour expiry
        token = create_password_token(data={"sub": str(user.id)}, token_type="initial_password", expire_minutes=settings.INITIAL_PASSWORD_TOKEN_EXPIRE_MINUTES)

        # Create link for setting initial password (frontend will handle this)
        set_password_link = f"{settings.FRONTEND_URL}/set-initial-password?token={token}"

        username = f"{user.first_name} {user.last_name}" or "User"
        username = extract_name_parts(username, NameExtractionOption.FIRST)

        # Get user role
        user_role = "User"
        if user.user_roles:
            role_id = user.user_roles[0].role_id
            user_role = UserRoleEnum.from_id(role_id).display_name
        
        if user_role == "Lawyer":
            user_role = "Expert"

        from app.utils.helpers import format_expiry_time
        expiry_time = format_expiry_time(settings.INITIAL_PASSWORD_TOKEN_EXPIRE_MINUTES)
        # Send resend initial password setup email
        await email_service.send_email(
            to_email=user.email,
            template=email_service.EmailTemplate.RESEND_INITIAL_PASSWORD_SETUP,
            context={
                "username": username,
                "reset_link": set_password_link,
                "header_subtitle": "Reminder: Set Your Password",
                "expiry_time": expiry_time["formatted"],
                "user_role": user_role,
            },
        )

        return EventResponseData(
            success=True,
            message="Resend initial password setup email sent successfully",
            data={"token": token, "set_password_link": set_password_link},
        )

    except Exception as e:
        logger.exception(f"Error in handle_resend_initial_password_email_after_expiry: {e}")
        raise
