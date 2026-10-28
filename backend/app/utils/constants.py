"""
Application constants for the Nova Law AI application.
"""

# Import enums from the new enums directory

# API Configuration
API_VERSIONS = ["v1"]
DEFAULT_API_VERSION = "v1"
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

# Security Configuration
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
TOKEN_EXPIRY_HOURS = 24
REFRESH_TOKEN_EXPIRY_DAYS = 30

# Rate Limiting
DEFAULT_RATE_LIMIT = 100  # requests per minute
AUTH_RATE_LIMIT = 5  # login attempts per minute
CHAT_RATE_LIMIT = 50  # messages per minute

# Lawyer interest deadline hours
LAWYER_INTEREST_DEADLINE_HOURS = 24

# File Upload
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/csv",
    "application/json",
]

# Chat Configuration
MAX_MESSAGE_LENGTH = 10000
MAX_CHAT_HISTORY = 1000
CHAT_SESSION_TIMEOUT_HOURS = 24

# AI Model Configuration
DEFAULT_MODEL = "gpt-4"
FALLBACK_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 4000
TEMPERATURE = 0.7

# Database Configuration
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 30
DB_POOL_TIMEOUT = 30

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Email Configuration
EMAIL_VERIFICATION_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_HOURS = 1

# Email Template Configuration
MESSAGE = "Thank you for being part of the Nova network."
TEAM_NAME = "The Nova Team"
LEGAL_FOOTER = (
    "Nova Law Trading Limited is a limited company incorporated in England & Wales "
    "with no. 14139589 and registered address at Preston Park House, South Road, "
    "Brighton, East Sussex, United Kingdom, BN1 6SB. For support, contact hello@novalaw.co.uk"
)
DEFAULT_EMAIL_SENDER = "Nova <noreply@novalaw.ai>"

# Cache Configuration
CACHE_TTL_SECONDS = 3600  # 1 hour
CACHE_MAX_SIZE = 1000

# Monitoring Configuration
METRICS_PORT = 9090
HEALTH_CHECK_INTERVAL = 30  # seconds

# Legal Document Types
LEGAL_DOCUMENT_TYPES = [
    "contract",
    "agreement",
    "memo",
    "brief",
    "pleading",
    "motion",
    "order",
    "judgment",
    "statute",
    "regulation",
    "case_law",
    "legal_opinion",
]

# Jurisdictions
SUPPORTED_JURISDICTIONS = [
    "US_FEDERAL",
    "US_STATE_CA",
    "US_STATE_NY",
    "US_STATE_TX",
    "US_STATE_FL",
    "US_STATE_IL",
    "US_STATE_PA",
    "US_STATE_OH",
    "US_STATE_GA",
    "US_STATE_NC",
]

# Time Zones
SUPPORTED_TIMEZONES = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Phoenix",
    "America/Anchorage",
    "Pacific/Honolulu",
]

# Response Messages
SUCCESS_MESSAGES = {
    "USER_CREATED": "User created successfully",
    "USER_UPDATED": "User updated successfully",
    "USER_DELETED": "User deleted successfully",
    "LOGIN_SUCCESS": "Login successful",
    "LOGOUT_SUCCESS": "Logout successful",
    "PASSWORD_RESET_SENT": "Password reset email sent",
    "PASSWORD_CHANGED": "Password changed successfully",
    "CHAT_CREATED": "Chat session created successfully",
    "MESSAGE_SENT": "Message sent successfully",
    "AGENT_CREATED": "AI agent created successfully",
    "AGENT_UPDATED": "AI agent updated successfully",
}

ERROR_MESSAGES = {
    "INVALID_CREDENTIALS": "Invalid email or password",
    "USER_NOT_FOUND": "User not found",
    "EMAIL_ALREADY_EXISTS": "Email address already registered",
    "INVALID_TOKEN": "Invalid or expired token",
    "INSUFFICIENT_PERMISSIONS": "Insufficient permissions for this action",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Please try again later",
    "VALIDATION_ERROR": "Validation error occurred",
    "INTERNAL_ERROR": "An internal error occurred. Please try again later",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "FILE_TOO_LARGE": "File size exceeds maximum allowed limit",
    "INVALID_FILE_TYPE": "File type not supported",
    "CHAT_NOT_FOUND": "Chat session not found",
    "AGENT_NOT_FOUND": "AI agent not found",
}

ENGAGE_VERIFY_TOKEN_URL_PREFIX = "/directengagelogin"
