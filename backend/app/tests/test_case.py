"""Tests for case API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.case import Case
from app.db.models.case_customer import CaseCustomer
from app.db.models.case_lawyer import CaseLawyer
from app.db.models.customer import Customer
from app.db.models.lawyer import Lawyer
from app.db.models.match import Match
from app.db.models.user import User
from app.enums.case import CasePriorityEnum, CaseStatusEnum, CaseTypeEnum
from app.enums.user_role import UserRoleEnum
from app.main import app

import time
import uuid


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session."""
    from app.tests.conftest import override_get_db
    from app.utils.dependencies import get_db
    from sqlalchemy import text

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Get the database session
    db = next(override_get_db())
    
    # Clean up test users before the test
    try:
        # Delete in order to respect foreign key constraints
        # Start with the most dependent tables and work backwards
        db.execute(text("DELETE FROM case_resolve WHERE resolve_id IN (SELECT id FROM resolve WHERE customer_id IN (SELECT id FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')))"))
        db.execute(text("DELETE FROM resolve WHERE customer_id IN (SELECT id FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com'))"))
        db.execute(text("DELETE FROM case_customer WHERE customer_id IN (SELECT id FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com'))"))
        db.execute(text("DELETE FROM case_lawyer WHERE lawyer_id IN (SELECT id FROM lawyer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com'))"))
        db.execute(text("DELETE FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')"))
        db.execute(text("DELETE FROM lawyer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')"))
        db.execute(text("DELETE FROM user_role WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')"))
        db.execute(text("DELETE FROM \"user\" WHERE email LIKE '%@unit-test.com'"))
        db.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
        db.rollback()
    
    yield db

    # Clean up test users after the test
    try:
        # Delete in order to respect foreign key constraints
        # Start with the most dependent tables and work backwards
        db.execute(text("DELETE FROM case_resolve WHERE resolve_id IN (SELECT id FROM resolve WHERE customer_id IN (SELECT id FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')))"))
        db.execute(text("DELETE FROM resolve WHERE customer_id IN (SELECT id FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com'))"))
        db.execute(text("DELETE FROM case_customer WHERE customer_id IN (SELECT id FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com'))"))
        db.execute(text("DELETE FROM case_lawyer WHERE lawyer_id IN (SELECT id FROM lawyer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com'))"))
        db.execute(text("DELETE FROM customer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')"))
        db.execute(text("DELETE FROM lawyer WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')"))
        db.execute(text("DELETE FROM user_role WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE '%@unit-test.com')"))
        db.execute(text("DELETE FROM \"user\" WHERE email LIKE '%@unit-test.com'"))
        db.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
        db.rollback()
    
    # Clean up
    db.close()
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_navigator(db_session: Session) -> User:
    """Create a test navigator user."""
    from app.db.services.user import create_user, assign_user_role
    from app.schemas.v1.user import UserCreate

    # Use timestamp and uuid to make email unique
    timestamp = int(time.time() * 1000000)  # microseconds
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"navigator_{timestamp}_{unique_id}@unit-test.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="Navigator",
        phone="+1234567890",
    )
    user = create_user(db_session, user_data)
    assign_user_role(db_session, user.id, UserRoleEnum.NAVIGATOR)
    return user


@pytest.fixture
def test_user_lawyer(db_session: Session) -> User:
    """Create a test lawyer user."""
    from app.db.services.user import create_user, assign_user_role
    from app.schemas.v1.user import UserCreate

    # Use timestamp and uuid to make email unique
    timestamp = int(time.time() * 1000000)  # microseconds
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"lawyer_{timestamp}_{unique_id}@unit-test.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="Lawyer",
        phone="+1234567891",
    )
    user = create_user(db_session, user_data)
    assign_user_role(db_session, user.id, UserRoleEnum.LAWYER)
    return user


@pytest.fixture
def test_user_customer(db_session: Session) -> User:
    """Create a test customer user."""
    from app.db.services.user import create_user, assign_user_role
    from app.schemas.v1.user import UserCreate

    # Use timestamp and uuid to make email unique
    timestamp = int(time.time() * 1000000)  # microseconds
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"customer_{timestamp}_{unique_id}@unit-test.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="Customer",
        phone="+1234567892",
    )
    user = create_user(db_session, user_data)
    assign_user_role(db_session, user.id, UserRoleEnum.CUSTOMER)
    return user


@pytest.fixture
def test_customer(db_session: Session, test_user_customer: User) -> Customer:
    """Create a test customer."""
    customer = Customer(user_id=test_user_customer.id)
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_lawyer(db_session: Session, test_user_lawyer: User) -> Lawyer:
    """Create a test lawyer."""
    lawyer = Lawyer(user_id=test_user_lawyer.id)
    db_session.add(lawyer)
    db_session.commit()
    db_session.refresh(lawyer)
    return lawyer


@pytest.fixture
def test_cases(
    db_session: Session, test_customer: Customer, test_lawyer: Lawyer
) -> list[Case]:
    """Create test cases with customer and lawyer assignments."""
    from datetime import date

    cases = []

    # Create multiple test cases
    case_data_list = [
        {
            "start_date": date(2024, 1, 15),
            "case_type": CaseTypeEnum.FAMILY_LAW,
            "priority": CasePriorityEnum.HIGH,
            "status": CaseStatusEnum.OPEN,
        },
        {
            "start_date": date(2024, 2, 20),
            "case_type": CaseTypeEnum.FAMILY_LAW,
            "priority": CasePriorityEnum.MEDIUM,
            "status": CaseStatusEnum.CLOSED,
        },
        {
            "start_date": date(2024, 3, 10),
            "case_type": CaseTypeEnum.FAMILY_LAW,
            "priority": CasePriorityEnum.LOW,
            "status": CaseStatusEnum.CLOSED,
        },
    ]

    for i, case_data in enumerate(case_data_list):
        case = Case(**case_data)
        db_session.add(case)
        db_session.flush()  # Get the case ID

        # Add customer to all cases
        case_customer = CaseCustomer(case_id=case.id, customer_id=test_customer.id)
        db_session.add(case_customer)

        # Add lawyer to first case only
        if i == 0:
            case_lawyer = CaseLawyer(case_id=case.id, lawyer_id=test_lawyer.id)
            db_session.add(case_lawyer)

        # Add match for second case (but no assignment)
        if i == 1:
            match = Match(
                case_id=case.id, lawyer_id=test_lawyer.id, user_id=test_customer.user_id
            )
            db_session.add(match)

        cases.append(case)

    db_session.commit()

    # Refresh to get auto-generated IDs
    for case in cases:
        db_session.refresh(case)

    return cases


def get_auth_headers(user: User) -> dict[str, str]:
    """Get authentication headers for a user."""
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {access_token}"}


class TestCaseAPI:
    """Test case for case API endpoints."""

    def test_get_cases_success_navigator(
        self,
        client,
        db_session: Session,
        test_user_navigator: User,
        test_cases: list[Case],
    ):
        """Test successful GET /api/v1/case for navigator user."""
        headers = get_auth_headers(test_user_navigator)

        response = client.get("/api/v1/case", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert body["success"] is True
        assert len(body["message"]) == 1
        assert body["message"][0]["success"] is True
        assert body["message"][0]["message"] == "Cases fetched successfully"

        data = body["data"]
        # Navigator should see all cases in the database (including the 3 test cases)
        assert data["total_count"] >= 3
        assert data["records_in_page"] >= 3
        assert len(data["cases"]) >= 3

        # Check first case
        first_case = data["cases"][0]
        assert "id" in first_case
        assert "case_no" in first_case
        assert "case_type" in first_case
        assert "priority" in first_case
        assert "status" in first_case
        assert "start_date" in first_case
        assert "created_at" in first_case
        assert "customer" in first_case

    def test_get_cases_success_lawyer(
        self,
        client,
        db_session: Session,
        test_user_lawyer: User,
        test_cases: list[Case],
    ):
        """Test successful GET /api/v1/case for lawyer user - should see assigned and matched-but-unassigned cases."""
        headers = get_auth_headers(test_user_lawyer)

        response = client.get("/api/v1/case", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert body["success"] is True
        assert len(body["message"]) == 1
        assert body["message"][0]["success"] is True
        assert body["message"][0]["message"] == "Cases fetched successfully"

        data = body["data"]
        # Lawyer should see 2 cases: 1 assigned + 1 matched-but-unassigned
        assert data["total_count"] == 2
        assert data["records_in_page"] == 2
        assert len(data["cases"]) == 2

    def test_get_cases_success_customer(
        self,
        client,
        db_session: Session,
        test_user_customer: User,
        test_cases: list[Case],
    ):
        """Test successful GET /api/v1/case for customer user."""
        headers = get_auth_headers(test_user_customer)

        response = client.get("/api/v1/case", headers=headers)

        assert response.status_code == 200
        body = response.json()

        assert body["success"] is True
        assert len(body["message"]) == 1
        assert body["message"][0]["success"] is True
        assert body["message"][0]["message"] == "Cases fetched successfully"

    def test_get_cases_pagination(
        self,
        client,
        db_session: Session,
        test_user_navigator: User,
        test_cases: list[Case],
    ):
        """Test GET /api/v1/case with pagination parameters."""
        headers = get_auth_headers(test_user_navigator)

        response = client.get("/api/v1/case?page=1&limit=10", headers=headers)

        assert response.status_code == 200
        body = response.json()

        data = body["data"]
        # Navigator should see all cases in the database (including the 3 test cases)
        assert data["total_count"] >= 3
        assert data["records_in_page"] >= 3
        assert len(data["cases"]) >= 3

    def test_get_cases_ordering(
        self,
        client,
        db_session: Session,
        test_user_navigator: User,
        test_cases: list[Case],
    ):
        """Test GET /api/v1/case with ordering parameters."""
        headers = get_auth_headers(test_user_navigator)

        response = client.get(
            "/api/v1/case?order_by=case_no&order_dir=asc", headers=headers
        )

        assert response.status_code == 200
        body = response.json()

        data = body["data"]
        # Navigator should see all cases in the database (including the 3 test cases)
        assert len(data["cases"]) >= 3

        # Check that cases are ordered by case_no ascending
        case_nos = [case["case_no"] for case in data["cases"]]
        assert case_nos == sorted(case_nos)

    def test_get_cases_unauthorized(self, client, db_session: Session):
        """Test GET /api/v1/case without authentication."""
        response = client.get("/api/v1/case")

        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert "Bearer token missing or unknown" in body["message"]

    def test_get_cases_empty_list(
        self, client, db_session: Session, test_user_navigator: User
    ):
        """Test GET /api/v1/case when cases exist (should return 200 with cases)."""
        headers = get_auth_headers(test_user_navigator)

        response = client.get("/api/v1/case", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["message"]) == 1
        assert body["message"][0]["success"] is True
        assert body["message"][0]["message"] == "Cases fetched successfully"

    def test_get_cases_invalid_page_parameter(
        self,
        client,
        db_session: Session,
        test_user_navigator: User,
        test_cases: list[Case],
    ):
        """Test GET /api/v1/case with invalid page parameter."""
        headers = get_auth_headers(test_user_navigator)

        response = client.get("/api/v1/case?page=0", headers=headers)

        assert response.status_code == 422  # Validation error
        body = response.json()
        assert body["success"] is False
        # The message is a list of validation errors
        assert isinstance(body["message"], list)
        # Check that there's at least one validation error
        assert len(body["message"]) > 0

    def test_get_cases_invalid_limit_parameter(
        self,
        client,
        db_session: Session,
        test_user_navigator: User,
        test_cases: list[Case],
    ):
        """Test GET /api/v1/case with invalid limit parameter."""
        headers = get_auth_headers(test_user_navigator)

        response = client.get("/api/v1/case?limit=5", headers=headers)

        assert response.status_code == 422  # Validation error
        body = response.json()
        assert body["success"] is False
        # The message is a list of validation errors
        assert isinstance(body["message"], list)
        # Check that there's at least one validation error
        assert len(body["message"]) > 0
