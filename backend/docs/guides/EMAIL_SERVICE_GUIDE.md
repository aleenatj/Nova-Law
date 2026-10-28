# Email Service Guide

## Overview

The Nova Law AI email service provides a simplified, unified interface for sending emails with smart defaults and flexible options. This guide covers all use cases and provides examples for developers who want to add new email functionality.

## Architecture

The email service consists of:

- **`EmailService`**: Main service class with a single `send_email()` method
- **`EmailTemplateService`**: Handles Jinja2 template rendering
- **`EmailTemplate`**: Enum for type-safe template names and subject configuration
- **`EmailResponse`**: Standardized response format

## Core Components

### EmailService

The main service class with a single, flexible `send_email()` method:

```python
from app.core.email import email_service

# Single method handles all use cases
await email_service.send_email(
    to_email: str | list[str] | None = None,      # Optional - if provided, use template
    template: EmailTemplate | None = None,        # Optional - if provided, use template
    body: str | None = None,                      # Optional - if provided, use raw body
    subject: str | None = None,                   # Optional - auto-generated if possible
    context: dict[str, Any] | None = None,        # Optional - for template rendering
    sender: str | None = None,                    # Optional
    cc: str | list[str] | None = None,            # Optional
    bcc: str | list[str] | None = None,           # Optional
) -> EmailResponse
```

**Note**: The `EmailTemplate` enum is also available as a class attribute on the service:
```python
# Access templates via the service
email_service.EmailTemplate.PASSWORD_RESET
email_service.EmailTemplate.WELCOME
```

### EmailTemplate Enum

Type-safe template management with configurable subjects:

```python
from app.enums.email import EmailTemplate

class EmailTemplate(str, Enum):
    """Available email templates in the system."""
    PASSWORD_RESET = "password_reset"
    # Add more templates here as needed

# Subject templates for each email type
EMAIL_SUBJECTS = {
    "password_reset": "Password Reset for {{ username }}",
    # Add more subjects here as needed:
    # "welcome": "Welcome {{ username }} to {{ team_name }}",
    # "case_update": "Case Update: {{ case_id }} - {{ case_title }}",
    # "document_ready": "Document Ready: {{ document_name }} for {{ case_id }}",
    # "new_case": "New Case: {{ case_no }} On {{ case_created_at }} Registered",
}
```

## Import Approaches

The email service supports two import approaches:

### Approach 1: Separate Imports (Traditional)
```python
from app.core.email import email_service
from app.enums.email import EmailTemplate

await email_service.send_email(
    to_email="user@example.com",
    template=EmailTemplate.PASSWORD_RESET,
    context={"username": "John"}
)
```

### Approach 2: Service-Attached Enum (Recommended)
```python
from app.core.email import email_service

await email_service.send_email(
    to_email="user@example.com",
    template=email_service.EmailTemplate.PASSWORD_RESET,
    context={"username": "John"}
)
```

### Comparison

| Aspect | Separate Imports | Service-Attached Enum |
|--------|------------------|----------------------|
| **Imports** | 2 imports needed | 1 import needed |
| **Coupling** | Loose coupling | Tight coupling to service |
| **Discoverability** | IDE may not suggest templates | IDE suggests templates via service |
| **Namespace** | Global namespace | Service namespace |
| **Maintenance** | Need to update imports if enum moves | Always available via service |

**Recommendation**: Use the service-attached enum approach for better discoverability and cleaner imports.

## Use Cases and Examples

### 1. Template-Based Email with Auto-Generated Subject

**Use Case**: Send a password reset email using a template with automatic subject generation.

```python
from app.core.email import email_service

# Send password reset email
response = await email_service.send_email(
    to_email="user@example.com",
    template=email_service.EmailTemplate.PASSWORD_RESET,
    context={
        "username": "John Doe",
        "reset_link": "https://example.com/reset?token=abc123",
        "header_subtitle": "Password Reset Request"
    }
)

# Result: Subject = "Password Reset for John Doe"
# Result: HTML content rendered from password_reset.html template
```

### 2. Template-Based Email with Custom Subject

**Use Case**: Use a template but override the subject for urgency or branding.

```python
response = await email_service.send_email(
    to_email="user@example.com",
    template=email_service.EmailTemplate.PASSWORD_RESET,
    subject="URGENT: Password Reset Required",
    context={
        "username": "John Doe",
        "reset_link": "https://example.com/reset?token=abc123"
    }
)

# Result: Subject = "URGENT: Password Reset Required"
# Result: HTML content rendered from password_reset.html template
```

### 3. Raw HTML Body Email

**Use Case**: Send a custom email with raw HTML content (subject required).

```python
response = await email_service.send_email(
    to_email="user@example.com",
    body="<h1>Hello World</h1><p>This is a custom email.</p>",
    subject="Custom Email Subject"
)

# Result: Subject = "Custom Email Subject"
# Result: HTML content = "<h1>Hello World</h1><p>This is a custom email.</p>"
```

### 4. Multiple Recipients

**Use Case**: Send the same email to multiple recipients.

```python
response = await email_service.send_email(
    to_email=["user1@example.com", "user2@example.com", "user3@example.com"],
    template=email_service.EmailTemplate.PASSWORD_RESET,
    context={"username": "Team", "reset_link": "https://example.com/reset"}
)

# Result: Email sent to all three recipients
```

### 5. CC and BCC Support

**Use Case**: Send email with carbon copy and blind carbon copy recipients.

```python
response = await email_service.send_email(
    to_email="user@example.com",
    cc=["manager@example.com", "supervisor@example.com"],
    bcc=["admin@example.com"],
    template=EmailTemplate.PASSWORD_RESET,
    context={"username": "John", "reset_link": "https://example.com/reset"}
)

# Result:
# To: user@example.com
# CC: manager@example.com, supervisor@example.com
# BCC: admin@example.com (not visible to other recipients)
```

### 6. Custom Sender

**Use Case**: Send email from a specific sender address.

```python
response = await email_service.send_email(
    to_email="user@example.com",
    template=EmailTemplate.PASSWORD_RESET,
    sender="support@novalaw.com",
    context={"username": "John", "reset_link": "https://example.com/reset"}
)

# Result: Email sent from support@novalaw.com
```

## Smart Logic Rules

The email service uses intelligent defaults and validation:

### Template vs Body Logic
- If `template` provided → use template rendering
- If `body` provided → use raw body content
- If neither provided → raise `ValueError`

### Subject Logic
- If `subject` provided → use it (overrides template subject)
- If `template` provided and has subject config → auto-generate from template
- If `body` provided → `subject` is required
- If template has no subject config → `subject` is required

### Validation Rules
```python
# ✅ Valid combinations
await email_service.send_email(to_email="user@example.com", template=EmailTemplate.PASSWORD_RESET)
await email_service.send_email(to_email="user@example.com", body="<h1>Hello</h1>", subject="Test")
await email_service.send_email(to_email="user@example.com", template=EmailTemplate.PASSWORD_RESET, subject="Custom")

# ❌ Invalid combinations
await email_service.send_email(to_email="user@example.com")  # No template or body
await email_service.send_email(to_email="user@example.com", body="<h1>Hello</h1>")  # No subject
```

## Adding New Email Templates

### Step 1: Create HTML Template

Create a new HTML template in `app/config/templates/email/html/`:

```html
<!-- app/config/templates/email/html/welcome.html -->
{% extends "html/base.html" %}

{% block content %}
<h2>Welcome to Nova Law AI</h2>

<p>Hi {{ username | default('there') }},</p>

<p>Welcome to {{ team_name | default('Nova Law AI') }}! We're excited to have you on board.</p>

<p>Your account has been successfully created and is ready to use.</p>

<p>Best regards,<br>
The {{ team_name | default('Nova Law AI') }} Team</p>
{% endblock %}
```

### Step 2: Add Template to Enum

Update `app/enums/email.py`:

```python
class EmailTemplate(str, Enum):
    """Available email templates in the system."""
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"  # Add new template

# Add subject template
EMAIL_SUBJECTS = {
    "password_reset": "Password Reset for {{ username }}",
    "welcome": "Welcome {{ username }} to {{ team_name }}",  # Add new subject
}
```

### Step 3: Use the New Template

```python
# Send welcome email
response = await email_service.send_email(
    to_email="newuser@example.com",
    template=EmailTemplate.WELCOME,
    context={
        "username": "Jane Doe",
        "team_name": "Nova Law AI"
    }
)

# Result: Subject = "Welcome Jane Doe to Nova Law AI"
```

## Template Structure

### Base Template

All email templates extend the base template:

```html
<!-- app/config/templates/email/html/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email from Nova Law AI</title>
    <style>
        /* CSS styles for email compatibility */
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        {% include "html/partials/header.html" %}

        {% block content %}
        <!-- Main content goes here -->
        {% endblock %}

        {% include "html/partials/footer.html" %}
    </div>
</body>
</html>
```

### Header Partial

```html
<!-- app/config/templates/email/html/partials/header.html -->
<div class="header">
    <h1>{{ team_name | default('Nova Law AI') }}</h1>
    {% if header_subtitle %}
    <p>{{ header_subtitle }}</p>
    {% endif %}
</div>
```

### Footer Partial

```html
<!-- app/config/templates/email/html/partials/footer.html -->
<div class="footer">
    <p>{{ legal_footer | default('© 2024 Nova Law AI. All rights reserved.') }}</p>
    {% if unsubscribe_link %}
    <p><a href="{{ unsubscribe_link }}">Unsubscribe</a></p>
    {% endif %}
</div>
```

## Context Variables

### Default Context

The following variables are automatically available in all templates:

```python
default_context = {
    "team_name": "Nova Law AI",
    "legal_footer": "© 2024 Nova Law AI. All rights reserved."
}
```

### Custom Context

Pass additional variables through the `context` parameter:

```python
context = {
    "username": "John Doe",
    "reset_link": "https://example.com/reset?token=abc123",
    "expiry_hours": "24",
    "header_subtitle": "Password Reset Request",
    "custom_field": "Custom value"
}
```

## Error Handling

The email service provides comprehensive error handling:

```python
response = await email_service.send_email(
    to_email="user@example.com",
    template=EmailTemplate.PASSWORD_RESET,
    context={"username": "John"}
)

if response.success:
    print(f"Email sent successfully. Message ID: {response.message_id}")
else:
    print(f"Email failed: {response.error}")
```

### Common Error Scenarios

1. **Template Not Found**: Template file doesn't exist
2. **SMTP Authentication Error**: Invalid SMTP credentials
3. **Recipient Refused**: Invalid email address
4. **Sender Refused**: Invalid sender address
5. **Network Error**: SMTP server unreachable

## Testing

### Unit Tests

Test the email service functionality:

```python
import pytest
from unittest.mock import patch
from app.core.email import email_service
from app.enums.email import EmailTemplate

@pytest.mark.asyncio
async def test_send_email_template():
    """Test sending template email."""
    with patch.dict(os.environ, {"LOCAL_TESTING": "true"}):
        response = await email_service.send_email(
            to_email="test@example.com",
            template=EmailTemplate.PASSWORD_RESET,
            context={"username": "John"}
        )

        assert response.success is True
        assert response.message_id == "test-message-id-12345"

@pytest.mark.asyncio
async def test_send_email_validation():
    """Test validation errors."""
    with pytest.raises(ValueError, match="Either template or body must be provided"):
        await email_service.send_email(to_email="test@example.com")
```

### Integration Tests

Test with actual SMTP (use test environment):

```python
@pytest.mark.asyncio
async def test_send_email_integration():
    """Test actual email sending."""
    response = await email_service.send_email(
        to_email="test@example.com",
        template=EmailTemplate.PASSWORD_RESET,
        context={"username": "John"}
    )

    assert response.success is True
    assert response.message_id is not None
```

## Configuration

### Environment Variables

Configure the email service through environment variables:

```bash
# AWS SES Configuration
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587
AWS_SES_SMTP_USERNAME=your_smtp_username
AWS_SES_SMTP_PASSWORD=your_smtp_password

# Default Settings
DEFAULT_EMAIL_SENDER=noreply@novalaw.com
FRONTEND_URL=https://app.novalaw.com

# Testing
LOCAL_TESTING=false  # Set to true for test mode
```

### Test Mode

When `LOCAL_TESTING=true`, emails are logged but not sent:

```python
# Test mode behavior
if os.getenv("LOCAL_TESTING", "false").lower() == "true":
    logger.info(f"Test mode: Email would be sent to {to_email}")
    return EmailResponse(
        success=True,
        message_id="test-message-id-12345",
        error=None
    )
```

## Best Practices

### 1. Use Templates for Consistent Branding

```python
# ✅ Good: Use templates for consistent emails
await email_service.send_email(
    to_email="user@example.com",
    template=EmailTemplate.PASSWORD_RESET,
    context={"username": "John"}
)

# ❌ Avoid: Raw HTML for standard emails
await email_service.send_email(
    to_email="user@example.com",
    body="<h1>Reset your password</h1>...",
    subject="Password Reset"
)
```

### 2. Provide Meaningful Context

```python
# ✅ Good: Provide all necessary context
context = {
    "username": "John Doe",
    "reset_link": "https://example.com/reset?token=abc123",
    "expiry_hours": "24",
    "header_subtitle": "Password Reset Request"
}

# ❌ Avoid: Missing context variables
context = {
    "username": "John"  # Missing other variables
}
```

### 3. Handle Errors Gracefully

```python
# ✅ Good: Proper error handling
try:
    response = await email_service.send_email(
        to_email="user@example.com",
        template=EmailTemplate.PASSWORD_RESET,
        context={"username": "John"}
    )

    if not response.success:
        logger.error(f"Email failed: {response.error}")
        # Handle failure (retry, notify admin, etc.)

except Exception as e:
    logger.exception("Unexpected error sending email")
    # Handle unexpected errors
```

### 4. Use Type Hints

```python
# ✅ Good: Use type hints for clarity
from typing import Any
from app.enums.email import EmailTemplate

async def send_welcome_email(
    to_email: str,
    username: str,
    team_name: str = "Nova Law AI"
) -> EmailResponse:
    context: dict[str, Any] = {
        "username": username,
        "team_name": team_name
    }

    return await email_service.send_email(
        to_email=to_email,
        template=EmailTemplate.WELCOME,
        context=context
    )
```

## Troubleshooting

### Common Issues

1. **Template Not Found**
   - Ensure template file exists in `app/config/templates/email/html/`
   - Check template name matches enum value

2. **Subject Not Generated**
   - Verify subject template exists in `EMAIL_SUBJECTS`
   - Check context variables are provided

3. **SMTP Errors**
   - Verify AWS SES credentials
   - Check network connectivity
   - Ensure sender email is verified

4. **Test Mode Not Working**
   - Set `LOCAL_TESTING=true` environment variable
   - Check logs for test mode messages

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger("app.core.email").setLevel(logging.DEBUG)
```

## Conclusion

The simplified email service provides a clean, unified interface for all email functionality. By following this guide, developers can easily add new email templates and use cases while maintaining consistency and reliability.

For additional support, refer to the test files in `app/tests/test_email.py` for comprehensive examples of all functionality.
