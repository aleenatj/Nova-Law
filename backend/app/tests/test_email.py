"""Unit tests for the email service with Jinja2 templating."""

import os
from unittest.mock import MagicMock, patch

import pytest
from jinja2 import TemplateNotFound

from app.core.email import (
    EmailResponse,
    EmailService,
    EmailTemplateService,
    email_service,
)
from app.enums.email import EmailTemplate


class TestEmailResponse:
    """Test cases for EmailResponse class."""

    def test_email_response_creation(self) -> None:
        """Test EmailResponse creation with success."""
        response = EmailResponse(success=True, message_id="test-123")
        assert response.success is True
        assert response.message_id == "test-123"
        assert response.error is None

    def test_email_response_with_error(self) -> None:
        """Test EmailResponse creation with error."""
        response = EmailResponse(success=False, error="Test error")
        assert response.success is False
        assert response.message_id is None
        assert response.error == "Test error"

    def test_email_response_to_dict(self) -> None:
        """Test EmailResponse to_dict method."""
        response = EmailResponse(success=True, message_id="test-123")
        result = response.to_dict()
        assert result == {
            "success": True,
            "message_id": "test-123",
            "error": None,
        }


class TestEmailTemplateService:
    """Test cases for EmailTemplateService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.template_service = EmailTemplateService()

    def test_template_service_initialization(self) -> None:
        """Test EmailTemplateService initialization."""
        assert self.template_service.env is not None
        assert "team_name" in self.template_service.default_context
        assert "legal_footer" in self.template_service.default_context

    def test_render_template_html(self) -> None:
        """Test rendering HTML template."""
        context = {"username": "John", "reset_link": "https://example.com/reset"}
        result = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, context
        )

        assert "Reset Your Password" in result
        assert "John" in result
        assert "https://example.com/reset" in result

    def test_render_template_password_reset(self) -> None:
        """Test rendering password reset template."""
        context = {"username": "Jane", "reset_link": "https://example.com/reset"}
        result = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, context
        )

        assert "Reset Your Password" in result
        assert "Jane" in result
        assert "https://example.com/reset" in result

    def test_render_template_with_default_context(self) -> None:
        """Test that default context is merged with provided context."""
        context = {"username": "Alice", "reset_link": "https://example.com/reset"}
        result = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, context
        )

        # Check that both custom and default context are present
        assert "Alice" in result
        assert "Nova Law AI" in result
        assert "team@novalaw.ai" in result

    def test_render_template_not_found(self) -> None:
        """Test rendering non-existent template raises TemplateNotFound."""
        # Test with a template name that doesn't exist by directly calling the template service
        with pytest.raises(TemplateNotFound):
            # Access the template service's env directly to test non-existent template
            self.template_service.env.get_template("html/nonexistent.html")

    def test_render_template_html_content(self) -> None:
        """Test rendering HTML template content."""
        context = {"username": "Bob", "reset_link": "https://example.com/reset"}
        html_content = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, context
        )

        assert "Reset Your Password" in html_content
        assert "<html" in html_content
        assert "Nova Law AI" in html_content

    def test_render_template_with_none_context(self) -> None:
        """Test rendering template with None context."""
        result = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, None
        )
        assert "Reset Your Password" in result
        assert "Nova Law AI" in result


class TestEmailService:
    """Test cases for EmailService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.email_service = EmailService()

    @patch.dict(os.environ, {"LOCAL_TESTING": "true"})
    async def test_send_email_test_mode(self) -> None:
        """Test sending email in test mode."""
        response = await self.email_service.send_email(
            to_email="test@example.com",
            body="Test Body",
            subject="Test Subject",
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"
        assert response.error is None

    @patch("smtplib.SMTP")
    @patch.dict(os.environ, {"LOCAL_TESTING": "false"})
    async def test_send_email_success(self, mock_smtp: MagicMock) -> None:
        """Test successful email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        response = await self.email_service.send_email(
            to_email="test@example.com",
            body="Test Body",
            subject="Test Subject",
        )

        assert response.success is True
        assert response.message_id is not None
        assert response.error is None
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    @patch.dict(os.environ, {"LOCAL_TESTING": "false"})
    async def test_send_email_smtp_authentication_error(
        self, mock_smtp: MagicMock
    ) -> None:
        """Test email sending with SMTP authentication error."""
        import smtplib

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Auth failed"
        )
        mock_smtp.return_value.__enter__.return_value = mock_server

        response = await self.email_service.send_email(
            to_email="test@example.com",
            body="Test Body",
            subject="Test Subject",
        )

        assert response.success is False
        assert response.message_id is None
        assert "authentication failed" in response.error.lower()

    @patch.dict(os.environ, {"LOCAL_TESTING": "true"})
    async def test_send_email_template_test_mode(self) -> None:
        """Test sending template email in test mode."""
        response = await self.email_service.send_email(
            to_email="test@example.com",
            template=EmailTemplate.PASSWORD_RESET,
            context={"username": "John", "reset_link": "https://example.com/reset"},
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"
        assert response.error is None

    @patch("smtplib.SMTP")
    @patch.dict(os.environ, {"LOCAL_TESTING": "false"})
    async def test_send_email_template_success(self, mock_smtp: MagicMock) -> None:
        """Test successful template email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        response = await self.email_service.send_email(
            to_email="test@example.com",
            template=EmailTemplate.PASSWORD_RESET,
            context={"username": "John", "reset_link": "https://example.com/reset"},
        )

        assert response.success is True
        assert response.message_id is not None
        assert response.error is None
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    async def test_send_email_template_not_found(self) -> None:
        """Test sending email with non-existent template."""
        # Test with a template that doesn't exist by mocking the template service
        with patch.object(
            self.email_service.template_service, "render_template"
        ) as mock_render:
            mock_render.side_effect = TemplateNotFound("Template not found")

            response = await self.email_service.send_email(
                to_email="test@example.com",
                template=EmailTemplate.PASSWORD_RESET,  # Use existing template for the test
                context={"username": "John"},
            )

            assert response.success is False
            assert response.message_id is None
            assert "Template not found" in response.error

    @patch("smtplib.SMTP")
    @patch.dict(os.environ, {"LOCAL_TESTING": "false"})
    async def test_send_email_template_smtp_error(self, mock_smtp: MagicMock) -> None:
        """Test template email sending with SMTP error."""
        import smtplib

        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("SMTP error")
        mock_smtp.return_value.__enter__.return_value = mock_server

        response = await self.email_service.send_email(
            to_email="test@example.com",
            template=EmailTemplate.PASSWORD_RESET,
            context={"username": "John", "reset_link": "https://example.com/reset"},
        )

        assert response.success is False
        assert response.message_id is None
        assert "Failed to send email" in response.error


class TestSendEmailFunction:
    """Test cases for the send_email function."""

    @patch.dict(os.environ, {"LOCAL_TESTING": "true"})
    async def test_send_email_template_auto_subject(self) -> None:
        """Test send_email with template and auto-generated subject."""
        response = await email_service.send_email(
            to_email="test@example.com",
            template=EmailTemplate.PASSWORD_RESET,
            context={"username": "John", "reset_link": "https://example.com/reset"},
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"
        assert response.error is None

    @patch.dict(os.environ, {"LOCAL_TESTING": "true"})
    async def test_send_email_template_custom_subject(self) -> None:
        """Test send_email with template and custom subject."""
        response = await email_service.send_email(
            to_email="test@example.com",
            template=EmailTemplate.PASSWORD_RESET,
            subject="URGENT: Password Reset Required",
            context={"username": "John", "reset_link": "https://example.com/reset"},
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"
        assert response.error is None

    @patch.dict(os.environ, {"LOCAL_TESTING": "true"})
    async def test_send_email_raw_body(self) -> None:
        """Test send_email with raw body."""
        response = await email_service.send_email(
            to_email="test@example.com",
            body="<h1>Hello World</h1><p>This is a test email.</p>",
            subject="Test Email",
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"
        assert response.error is None

    @patch.dict(os.environ, {"LOCAL_TESTING": "true"})
    async def test_send_email_multiple_recipients(self) -> None:
        """Test send_email with multiple recipients."""
        response = await email_service.send_email(
            to_email=["user1@example.com", "user2@example.com"],
            template=EmailTemplate.PASSWORD_RESET,
            context={"username": "Team", "reset_link": "https://example.com/reset"},
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"
        assert response.error is None

    @patch.dict(os.environ, {"LOCAL_TESTING": "true"})
    async def test_send_email_with_cc_bcc(self) -> None:
        """Test send_email with CC and BCC."""
        response = await email_service.send_email(
            to_email="user@example.com",
            cc=["manager@example.com"],
            bcc=["admin@example.com"],
            template=EmailTemplate.PASSWORD_RESET,
            context={"username": "John", "reset_link": "https://example.com/reset"},
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"
        assert response.error is None

    async def test_send_email_validation_errors(self) -> None:
        """Test send_email validation errors."""
        # Test no template or body provided
        with pytest.raises(
            ValueError, match="Either template or body must be provided"
        ):
            await email_service.send_email(to_email="test@example.com")

        # Test body without subject
        with pytest.raises(ValueError, match="Subject is required when using raw body"):
            await email_service.send_email(
                to_email="test@example.com", body="<h1>Hello</h1>"
            )


class TestTemplateRendering:
    """Integration tests for template rendering."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.template_service = EmailTemplateService()

    def test_email_template_subject_generation(self) -> None:
        """Test email subject generation from template enum."""
        # Test basic subject without context (should return raw template)
        subject = EmailTemplate.get_subject(EmailTemplate.PASSWORD_RESET)
        assert subject == "Password Reset for {{ username }}"

        # Test subject with context
        context = {"username": "John Doe"}
        subject_with_context = EmailTemplate.get_subject(
            EmailTemplate.PASSWORD_RESET, context
        )
        assert subject_with_context == "Password Reset for John Doe"

        # Test subject with more context variables
        context = {"username": "Jane", "case_id": "CASE-1001"}
        subject_with_context = EmailTemplate.get_subject(
            EmailTemplate.PASSWORD_RESET, context
        )
        assert subject_with_context == "Password Reset for Jane"

        # Test unknown template (using a mock template)
        class MockTemplate:
            value = "unknown"

        unknown_subject = EmailTemplate.get_subject(MockTemplate())
        assert unknown_subject == "Email from Nova Law AI"

    def test_password_reset_template_rendering(self) -> None:
        """Test that password reset template renders correctly with all expected content."""
        context = {
            "username": "TestUser",
            "reset_link": "https://app.novalaw.ai/reset?token=abc123",
        }

        html_content = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, context
        )

        # Check HTML content
        assert "Reset Your Password" in html_content
        assert "TestUser" in html_content
        assert "https://app.novalaw.ai/reset?token=abc123" in html_content
        assert "team@novalaw.ai" in html_content
        assert "<html" in html_content
        assert "<body>" in html_content

    def test_template_with_custom_context(self) -> None:
        """Test template rendering with custom context variables."""
        context = {
            "username": "CustomUser",
            "reset_link": "https://app.novalaw.ai/reset?token=xyz789",
            "header_subtitle": "Custom Subtitle",
        }

        html_content = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, context
        )

        # Check that custom context is used
        assert "CustomUser" in html_content
        assert "Custom Subtitle" in html_content
        assert "https://app.novalaw.ai/reset?token=xyz789" in html_content

    def test_template_fallback_values(self) -> None:
        """Test that template uses fallback values when context is missing."""
        html_content = self.template_service.render_template(
            EmailTemplate.PASSWORD_RESET, {}
        )

        # Should use default values
        assert "Reset Your Password" in html_content
        assert "Nova Law AI" in html_content
