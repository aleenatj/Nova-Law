"""Tests for enum organization and functionality."""

from app.enums import (
    AgentType,
    APIVersion,
    ChatStatus,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    MessageType,
    Permission,
    UserRoleEnum,
)


class TestAuthEnums:
    """Test authentication and authorization enums."""

    def test_user_role_values(self) -> None:
        """Test that UserRoleEnum has expected values."""
        assert UserRoleEnum.NAVIGATOR.value == "Navigator"
        assert UserRoleEnum.LAWYER.value == "Lawyer"
        assert UserRoleEnum.CUSTOMER.value == "Customer"

    def test_user_role_membership(self) -> None:
        """Test enum membership validation."""
        valid_roles = [role.value for role in UserRoleEnum]
        assert "Navigator" in valid_roles
        assert "Lawyer" in valid_roles
        assert "Customer" in valid_roles
        assert "invalid_role" not in valid_roles

    def test_permission_values(self) -> None:
        """Test that Permission enum has expected values."""
        assert Permission.USER_READ.value == "user:read"
        assert Permission.USER_CREATE.value == "user:create"
        assert Permission.CHAT_SEND_MESSAGE.value == "chat:send_message"
        assert Permission.ADMIN_ALL.value == "admin:all"


class TestChatEnums:
    """Test chat and messaging enums."""

    def test_chat_status_values(self) -> None:
        """Test that ChatStatus enum has expected values."""
        assert ChatStatus.ACTIVE.value == "active"
        assert ChatStatus.CLOSED.value == "closed"
        assert ChatStatus.ARCHIVED.value == "archived"
        assert ChatStatus.PENDING.value == "pending"

    def test_message_type_values(self) -> None:
        """Test that MessageType enum has expected values."""
        assert MessageType.USER.value == "user"
        assert MessageType.ASSISTANT.value == "assistant"
        assert MessageType.SYSTEM.value == "system"
        assert MessageType.ERROR.value == "error"


class TestAgentEnums:
    """Test AI agent enums."""

    def test_agent_type_values(self) -> None:
        """Test that AgentType enum has expected values."""
        assert AgentType.GENERAL.value == "general"
        assert AgentType.LEGAL_RESEARCH.value == "legal_research"
        assert AgentType.DOCUMENT_REVIEW.value == "document_review"
        assert AgentType.CONTRACT_ANALYSIS.value == "contract_analysis"
        assert AgentType.CASE_ANALYSIS.value == "case_analysis"


class TestErrorEnums:
    """Test error and logging enums."""

    def test_error_code_values(self) -> None:
        """Test that ErrorCode enum has expected values."""
        assert ErrorCode.INVALID_CREDENTIALS.value == "INVALID_CREDENTIALS"
        assert ErrorCode.TOKEN_EXPIRED.value == "TOKEN_EXPIRED"
        assert ErrorCode.RESOURCE_NOT_FOUND.value == "RESOURCE_NOT_FOUND"
        assert ErrorCode.INTERNAL_SERVER_ERROR.value == "INTERNAL_SERVER_ERROR"

    def test_error_severity_values(self) -> None:
        """Test that ErrorSeverity enum has expected values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_error_category_values(self) -> None:
        """Test that ErrorCategory enum has expected values."""
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestSystemEnums:
    """Test system and API enums."""

    def test_api_version_values(self) -> None:
        """Test that APIVersion enum has expected values."""
        assert APIVersion.V1.value == "v1"
        assert APIVersion.V2.value == "v2"


class TestEnumImports:
    """Test that all enums can be imported correctly."""

    def test_all_enums_importable(self) -> None:
        """Test that all enums can be imported from the main enums module."""
        from app.enums import (
            AgentType,
            APIVersion,
            ChatStatus,
            ErrorCategory,
            ErrorCode,
            ErrorSeverity,
            MessageType,
            Permission,
            UserRoleEnum,
        )

        # Verify all enums are imported
        assert AgentType is not None
        assert APIVersion is not None
        assert ChatStatus is not None
        assert ErrorCategory is not None
        assert ErrorCode is not None
        assert ErrorSeverity is not None
        assert MessageType is not None
        assert Permission is not None
        assert UserRoleEnum is not None

    def test_enum_serialization(self) -> None:
        """Test that enums can be serialized to JSON."""
        import json

        # Test that enum values can be serialized
        user_role_data = {"role": UserRoleEnum.NAVIGATOR.value}
        json_str = json.dumps(user_role_data)
        assert json_str == '{"role": "Navigator"}'

        # Test that enum values can be deserialized
        parsed_data = json.loads(json_str)
        assert parsed_data["role"] == "Navigator"
