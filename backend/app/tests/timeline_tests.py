#!/usr/bin/env python3
"""
Simple test runner for timeline tests that bypasses conftest.py issues.
"""

import asyncio
import sys
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import Mock, patch


# Mock the database session
class MockSession:
    def __init__(self) -> None:
        self.add_called = False
        self.commit_called = False
        self.refresh_called = False

    def add(self, obj: object) -> None:
        self.add_called = True

    def commit(self) -> None:
        self.commit_called = True

    def refresh(self, obj: object) -> None:
        self.refresh_called = True


# Mock the database models
class MockUser:
    def __init__(self, user_id: int, first_name: str, last_name: str) -> None:
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        # Mock user_roles attribute
        self.user_roles = [Mock(role_id=1)]  # Default role ID
        # Mock customer attribute
        self.customer: MockCustomer | None = None


class MockCustomer:
    def __init__(self, customer_id: int) -> None:
        self.id = customer_id


class MockCase:
    def __init__(self, case_id: int) -> None:
        self.id = case_id


class MockTimelineEvent:
    def __init__(self, event_id: int, case_id: int, user_id: int) -> None:
        self.id = event_id
        self.case_id = case_id
        self.action_user_id = user_id
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


class MockTimelineType:
    def __init__(self, type_id: int, name: str) -> None:
        self.id = type_id
        self.name = name


# Mock fixtures
def create_mock_fixtures() -> dict[str, Any]:
    """Create mock fixtures for testing."""
    test_customer = MockUser(1, "Customer", "User")
    test_customer.customer = MockCustomer(1)  # Set customer attribute

    test_lawyer = MockUser(2, "Lawyer", "User")
    test_navigator = MockUser(3, "Navigator", "User")
    test_case = MockCase(1)
    test_timeline_type = MockTimelineType(1, "Case Opened")
    test_timeline_event = MockTimelineEvent(1, 1, 2)

    return {
        "test_customer": test_customer,
        "test_lawyer": test_lawyer,
        "test_navigator": test_navigator,
        "test_case": test_case,
        "test_timeline_type": test_timeline_type,
        "test_timeline_event": test_timeline_event,
    }


async def test_timeline_endpoint_basic() -> bool:
    """Basic test of timeline endpoint functionality."""
    print("Running basic timeline endpoint test...")

    # Mock fixtures
    fixtures = create_mock_fixtures()

    # Mock the database session
    mock_db = MockSession()

    # Mock the timeline functions
    with (
        patch("app.api.v1.timeline.get_timeline_events_by_case_id") as mock_get_events,
        patch("app.api.v1.timeline.check_customer_case_access") as mock_check_access,
    ):
        # Setup mocks
        mock_check_access.return_value = True
        mock_get_events.return_value = (
            [
                {
                    "id": cast(MockTimelineEvent, fixtures["test_timeline_event"]).id,
                    "case_id": cast(MockCase, fixtures["test_case"]).id,
                    "timeline_type_id": cast(
                        MockTimelineType, fixtures["test_timeline_type"]
                    ).id,
                    "timeline_type_name": cast(
                        MockTimelineType, fixtures["test_timeline_type"]
                    ).name,
                    "action_user_id": cast(MockUser, fixtures["test_customer"]).id,
                    "action_user_name": f"{cast(MockUser, fixtures['test_customer']).first_name} {cast(MockUser, fixtures['test_customer']).last_name}",
                    "notify_user_id": None,
                    "notify_user_name": None,
                    "meta_data": {"action": "case_opened"},
                    "version": 1,
                    "created_at": cast(
                        MockTimelineEvent, fixtures["test_timeline_event"]
                    ).created_at,
                    "updated_at": cast(
                        MockTimelineEvent, fixtures["test_timeline_event"]
                    ).updated_at,
                }
            ],
            1,
        )

        # Import the function to test
        from fastapi import status

        from app.api.v1.timeline import get_timeline_events
        from app.schemas.v1.base import BaseResponse

        # Create a mock request object that bypasses schema validation
        mock_request = Mock()
        mock_request.case_id = "1"  # Simple string ID
        mock_request.role_code = None
        mock_request.page = 0
        mock_request.limit = 10
        mock_request.order_dir = "desc"
        mock_request.order_by = "id"

        # Call endpoint
        response = await get_timeline_events(
            request=mock_request,
            db=mock_db,  # type: ignore
            current_user=cast(MockUser, fixtures["test_customer"]),  # type: ignore
        )

        # Assertions
        assert isinstance(response, BaseResponse)
        assert response.status == status.HTTP_200_OK
        assert response.message == "Timeline events retrieved successfully"
        assert response.data is not None
        assert response.data.total_records == 1

        print("✅ Basic timeline endpoint test passed!")
        return True


async def test_timeline_endpoint_lawyer() -> bool:
    """Test timeline endpoint for lawyer user."""
    print("Running lawyer timeline endpoint test...")

    # Mock fixtures
    fixtures = create_mock_fixtures()

    # Mock the database session
    mock_db = MockSession()

    # Mock the timeline functions
    with patch("app.api.v1.timeline.get_timeline_events_by_case_id") as mock_get_events:
        # Setup mocks
        mock_get_events.return_value = (
            [
                {
                    "id": cast(MockTimelineEvent, fixtures["test_timeline_event"]).id,
                    "case_id": cast(MockCase, fixtures["test_case"]).id,
                    "timeline_type_id": cast(
                        MockTimelineType, fixtures["test_timeline_type"]
                    ).id,
                    "timeline_type_name": cast(
                        MockTimelineType, fixtures["test_timeline_type"]
                    ).name,
                    "action_user_id": cast(MockUser, fixtures["test_lawyer"]).id,
                    "action_user_name": f"{cast(MockUser, fixtures['test_lawyer']).first_name} {cast(MockUser, fixtures['test_lawyer']).last_name}",
                    "notify_user_id": None,
                    "notify_user_name": None,
                    "meta_data": {"action": "case_opened"},
                    "version": 1,
                    "created_at": cast(
                        MockTimelineEvent, fixtures["test_timeline_event"]
                    ).created_at,
                    "updated_at": cast(
                        MockTimelineEvent, fixtures["test_timeline_event"]
                    ).updated_at,
                }
            ],
            1,
        )

        # Import the function to test
        from fastapi import status

        from app.api.v1.timeline import get_timeline_events
        from app.schemas.v1.base import BaseResponse

        # Create a mock request object that bypasses schema validation
        mock_request = Mock()
        mock_request.case_id = "1"  # Simple string ID
        mock_request.role_code = None
        mock_request.page = 0
        mock_request.limit = 10
        mock_request.order_dir = "desc"
        mock_request.order_by = "id"

        # Call endpoint
        response = await get_timeline_events(
            request=mock_request,
            db=mock_db,  # type: ignore
            current_user=cast(MockUser, fixtures["test_lawyer"]),  # type: ignore
        )

        # Assertions
        assert isinstance(response, BaseResponse)
        assert response.status == status.HTTP_200_OK
        assert response.message == "Timeline events retrieved successfully"
        assert response.data is not None
        assert response.data.total_records == 1

        print("✅ Lawyer timeline endpoint test passed!")
        return True


async def main() -> int:
    """Run all timeline tests."""
    print("🚀 Starting timeline endpoint tests...")
    print("=" * 50)

    tests = [
        test_timeline_endpoint_basic,
        test_timeline_endpoint_lawyer,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All timeline tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)
