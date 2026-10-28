"""Email service for sending emails via AWS SES SMTP with Jinja2 templating support."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from structlog import get_logger

from app.core.config import settings
from app.enums.email import EmailTemplate
from app.utils.constants import LEGAL_FOOTER, TEAM_NAME, MESSAGE

logger = get_logger(__name__)


class EmailResponse:
    """Response model for email sending operations."""

    def __init__(
        self,
        success: bool,
        message_id: str | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.message_id = message_id
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "message_id": self.message_id,
            "error": self.error,
        }


class EmailTemplateService:
    """Service for rendering email templates using Jinja2."""

    def __init__(self) -> None:
        """Initialize the template service with Jinja2 environment."""
        # Get the absolute path to the email templates directory
        current_file = Path(__file__)
        template_path = current_file.parent.parent / "config" / "templates" / "email"

        # Ensure the path exists
        if not template_path.exists():
            raise FileNotFoundError(
                f"Email templates directory not found: {template_path}"
            )

        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add default context variables
        self.default_context = {
            "team_name": TEAM_NAME,
            "legal_footer": LEGAL_FOOTER,
            "logo_url": settings.LOGO_URL,
            "message": MESSAGE,
        }

    def render_template(
        self,
        template: EmailTemplate,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Render an email template with the given context.

        Args:
            template: EmailTemplate enum value
            context: Template context variables

        Returns:
            Rendered template content

        Raises:
            TemplateNotFound: If the template doesn't exist
            Exception: For other template rendering errors
        """
        if context is None:
            context = {}

        # Merge with default context
        full_context = {**self.default_context, **context}

        # Get template file path
        template_file = EmailTemplate.get_template_path(template)

        try:
            template_obj = self.env.get_template(template_file)
            return template_obj.render(**full_context)
        except TemplateNotFound:
            logger.exception(f"Template not found: {template_file}")
            raise TemplateNotFound(
                f"Email template '{template.value}' not found"
            ) from None
        except Exception as e:
            logger.exception(f"Error rendering template {template_file}: {e}")
            raise Exception(f"Failed to render email template: {e}") from e


class EmailService:
    """Service for sending emails via AWS SES SMTP."""

    # Make EmailTemplate available as a class attribute
    EmailTemplate = EmailTemplate

    def __init__(self) -> None:
        """Initialize the email service."""
        self.template_service = EmailTemplateService()

    async def send_email(
        self,
        to_email: str | list[str] | None = None,
        template: EmailTemplate | None = None,
        body: str | None = None,
        subject: str | None = None,
        context: dict[str, Any] | None = None,
        sender: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
    ) -> EmailResponse:
        """
        Send an email with smart defaults and flexible options.

        This is the main email sending function that handles all use cases:
        - Template-based emails with auto-generated subjects
        - Raw body emails with custom subjects
        - Multiple recipients, CC, BCC support

        Args:
            to_email: Email address(es) of the recipient(s) - single string or list of strings (required)
            template: EmailTemplate enum value (optional - if provided, uses template rendering)
            body: Raw email body content (optional - if provided, uses raw body)
            subject: Email subject (optional - auto-generated if template has subject config)
            context: Template context variables (optional - for template rendering)
            sender: Email address of the sender (optional)
            cc: Email address(es) for CC - single string or list of strings (optional)
            bcc: Email address(es) for BCC - single string or list of strings (optional)

        Returns:
            EmailResponse with success status and message ID or error

        Raises:
            ValueError: If neither template nor body is provided, or if body provided without subject
        """
        # Validate input
        if template is None and body is None:
            raise ValueError("Either template or body must be provided")

        if body is not None and subject is None:
            raise ValueError("Subject is required when using raw body")

        # If customer_name exists in context and ends with a dot, replace final '.' with a space
        _context = dict(context) if context is not None else {}
        customer_name: str | None = _context.get("customer_name")
        username: str | None = _context.get("username")
        if isinstance(username, str) and username.endswith("."):
            # Replace last '.' with a space
            _context["username"] = username[:-1] + " "
        if isinstance(customer_name, str) and customer_name.endswith("."):
            # Replace last '.' with a space
            _context["customer_name"] = customer_name[:-1] + " "
        # Determine email content and subject
        if template is not None:
            # Template-based email
            try:
                html_content = self.template_service.render_template(template, _context)
            except Exception as e:
                logger.exception(f"Error rendering template {template.value}: {e}")
                # return EmailResponse(
                #     success=False,
                #     message_id=None,
                #     error=f"Template rendering failed: {e}",
                # )
                raise Exception(f"Email sending failed: Failed to render template") from e

            # Auto-generate subject if not provided and template has subject config
            if subject is None:
                subject = EmailTemplate.get_subject(template, _context)
        else:
            # Raw body email
            html_content = body or ""  # Ensure html_content is not None

        # Use default sender if not provided
        if sender is None:
            sender = settings.DEFAULT_EMAIL_SENDER or ""

        # Ensure subject is not None
        if subject is None:
            subject = "Email from Nova"

        # Check if we're in testing mode
        if os.getenv("LOCAL_TESTING", "false").lower() == "true":
            logger.info(
                f"Test mode: Email would be sent to {to_email}",
                subject=subject,
                template=template.value if template is not None else None,
            )
            return EmailResponse(
                success=True, message_id="test-message-id-12345", error=None
            )

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = sender
            msg["Subject"] = subject

            if to_email:
                # Handle multiple recipients
                if isinstance(to_email, list):
                    msg["To"] = ", ".join(to_email)
                else:
                    msg["To"] = to_email

            # Handle CC
            if cc:
                if isinstance(cc, list):
                    msg["Cc"] = ", ".join(cc)
                else:
                    msg["Cc"] = cc

            # Handle BCC (BCC recipients are added to the SMTP send, not the message headers)
            all_recipients = []
            if to_email:
                if isinstance(to_email, list):
                    all_recipients.extend(to_email)
                else:
                    all_recipients.append(to_email)

            if cc:
                if isinstance(cc, list):
                    all_recipients.extend(cc)
                else:
                    all_recipients.append(cc)

            if bcc:
                if isinstance(bcc, list):
                    all_recipients.extend(bcc)
                else:
                    all_recipients.append(bcc)

            # Attach HTML content
            msg.attach(MIMEText(html_content, "html"))

            # Send email via SMTP
            with smtplib.SMTP(
                settings.AWS_SES_SMTP_HOST, settings.AWS_SES_SMTP_PORT
            ) as server:
                server.starttls()
                server.login(
                    settings.AWS_SES_SMTP_USERNAME, settings.AWS_SES_SMTP_PASSWORD
                )
                server.send_message(msg, to_addrs=all_recipients)

            # Generate message ID
            import uuid

            message_id = f"smtp-{uuid.uuid4()}"

            logger.info(
                f"Email sent successfully to {all_recipients}",
                subject=subject,
                message_id=message_id,
            )
            return EmailResponse(success=True, message_id=message_id, error=None)

        except smtplib.SMTPAuthenticationError as e:
            logger.exception(f"SMTP authentication failed: {e}")
            return EmailResponse(
                success=False,
                message_id=None,
                error=f"SMTP authentication failed: {e!s}. Please check SMTP credentials.",
            )
        except smtplib.SMTPRecipientsRefused as e:
            logger.exception(f"Recipient refused: {e}")
            return EmailResponse(
                success=False,
                message_id=None,
                error=f"Recipient refused: {e!s}. Please verify recipient email.",
            )
        except smtplib.SMTPSenderRefused as e:
            logger.exception(f"Sender refused: {e}")
            return EmailResponse(
                success=False,
                message_id=None,
                error=f"Sender refused: {e!s}. Please check sender email configuration.",
            )
        except smtplib.SMTPException as e:
            logger.exception(f"SMTP error: {e}")
            return EmailResponse(
                success=False,
                message_id=None,
                error=f"SMTP error: {e!s}. Please check SMTP configuration.",
            )
        except Exception as e:
            logger.exception(f"Unexpected error sending email: {e}")
            return EmailResponse(
                success=False,
                message_id=None,
                error=f"Unexpected error: {e!s}",
            )


# Global email service instance
email_service = EmailService()
