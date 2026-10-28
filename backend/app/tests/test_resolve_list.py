import time
from datetime import date

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.models.case import Case
from app.db.models.case_resolve import CaseResolve
from app.db.models.customer import Customer
from app.db.models.resolve import Resolve
from app.db.models.user import User
from app.db.models.user_role import UserRole
from app.enums.case import CaseTypeEnum
from app.enums.resolve import ResolveStatusEnum
from app.enums.user_role import UserRoleEnum
from app.tests.conftest import client


class TestResolveListEndpoint:
    """Test cases for the resolve list endpoint."""

    def test_get_resolve_list_success(self, db: Session) -> None:
        """Test successful resolve list retrieval."""
        # Create test user with unique email
        timestamp = int(time.time())
        test_user = User(
            email=f"test1_{timestamp}@unit-test.com",
            password=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Add user role
        user_role = UserRole(user_id=test_user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(user_role)
        db.commit()

        # Create customer
        customer = Customer(user_id=test_user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case
        case = Case(
            start_date=date(2024, 1, 15),
            case_type=CaseTypeEnum.FAMILY_LAW
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create test resolves
        resolve1 = Resolve(
            resolve_date=date(2024, 1, 15),
            user_id=test_user.id,
            customer_id=customer.id,
            result_reference_id="court",
            result_version=1,
            status=ResolveStatusEnum.COMPLETED,
        )
        resolve2 = Resolve(
            resolve_date=date(2024, 1, 16),
            user_id=test_user.id,
            customer_id=customer.id,
            result_reference_id="collaborative",
            result_version=2,
            status=ResolveStatusEnum.COMPLETED,
        )
        db.add_all([resolve1, resolve2])
        db.commit()
        db.refresh(resolve1)
        db.refresh(resolve2)

        # Link resolves to case
        case_resolve1 = CaseResolve(case_id=case.id, resolve_id=resolve1.id)
        case_resolve2 = CaseResolve(case_id=case.id, resolve_id=resolve2.id)
        db.add_all([case_resolve1, case_resolve2])
        db.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test1_{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # Test resolve list endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/resolve/list", headers=headers)

        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"][0]["success"] is True
        assert body["message"][0]["message"] == "Resolve data fetched"
        assert body["data"]["total_count"] == 2
        assert body["data"]["records_in_page"] == 2
        assert len(body["data"]["resolves"]) == 2

        # Check that the new fields are present and titles are correctly fetched
        resolves = body["data"]["resolves"]
        assert len(resolves) == 2
        
        # Check first resolve (collaborative - newer date)
        resolve1 = resolves[0]
        assert "case_type" in resolve1
        assert "resolve_status" in resolve1
        assert "no_of_questions_answered" in resolve1
        assert "customer" in resolve1
        assert "start_date" in resolve1
        assert "resolve_id" in resolve1
        assert "title" in resolve1
        assert resolve1["title"] is None  # collaborative version 2 doesn't exist in resolve.json
        
        # Check second resolve (court - older date)
        resolve2 = resolves[1]
        assert "case_type" in resolve2
        assert "resolve_status" in resolve2
        assert "no_of_questions_answered" in resolve2
        assert "customer" in resolve2
        assert "start_date" in resolve2
        assert "resolve_id" in resolve2
        assert "title" in resolve2
        assert resolve2["title"] == "Court"  # From resolve.json court.1.title

        # Check customer object structure
        for item in resolves:
            if item["customer"]:
                assert "first_name" in item["customer"]
                assert "last_name" in item["customer"]
                assert "email" in item["customer"]
                assert "id" in item["customer"]

    def test_get_resolve_list_pagination(self, db: Session) -> None:
        """Test resolve list pagination."""
        # Create test user with unique email
        timestamp = int(time.time())
        test_user = User(
            email=f"test2_{timestamp}@unit-test.com",
            password=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Add user role
        user_role = UserRole(user_id=test_user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(user_role)
        db.commit()

        # Create customer
        customer = Customer(user_id=test_user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case
        case = Case(
            start_date=date(2024, 1, 15),
            case_type=CaseTypeEnum.FAMILY_LAW
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create multiple test resolves
        resolves = []
        for i in range(25):
            # Use modulo to keep dates within valid range
            day = 1 + (i % 28)  # Keep within 1-28 to avoid month boundary issues
            resolve = Resolve(
                resolve_date=date(2024, 1, day),
                user_id=test_user.id,
                customer_id=customer.id,
                result_reference_id="court",
                result_version=1,
                status=ResolveStatusEnum.COMPLETED,
            )
            resolves.append(resolve)
        db.add_all(resolves)
        db.commit()

        # Link all resolves to case
        case_resolves = []
        for resolve in resolves:
            case_resolve = CaseResolve(case_id=case.id, resolve_id=resolve.id)
            case_resolves.append(case_resolve)
        db.add_all(case_resolves)
        db.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test2_{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # Test first page
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/resolve/list?page=1&limit=10", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total_count"] == 25
        assert body["data"]["records_in_page"] == 10
        assert len(body["data"]["resolves"]) == 10

        # Test second page
        response = client.get("/api/v1/resolve/list?page=2&limit=10", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total_count"] == 25
        assert body["data"]["records_in_page"] == 10
        assert len(body["data"]["resolves"]) == 10

    def test_get_resolve_list_ordering(self, db: Session) -> None:
        """Test resolve list ordering."""
        # Create test user with unique email
        timestamp = int(time.time())
        test_user = User(
            email=f"test3_{timestamp}@unit-test.com",
            password=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Add user role
        user_role = UserRole(user_id=test_user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(user_role)
        db.commit()

        # Create customer
        customer = Customer(user_id=test_user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case
        case = Case(
            start_date=date(2024, 1, 15),
            case_type=CaseTypeEnum.FAMILY_LAW
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create test resolves with different dates
        resolve1 = Resolve(
            resolve_date=date(2024, 1, 15),
            user_id=test_user.id,
            customer_id=customer.id,
            result_reference_id="court",
            result_version=1,
            status=ResolveStatusEnum.COMPLETED,
        )
        resolve2 = Resolve(
            resolve_date=date(2024, 1, 16),
            user_id=test_user.id,
            customer_id=customer.id,
            result_reference_id="collaborative",
            result_version=1,
            status=ResolveStatusEnum.COMPLETED,
        )
        db.add_all([resolve1, resolve2])
        db.commit()
        db.refresh(resolve1)
        db.refresh(resolve2)

        # Link resolves to case
        case_resolve1 = CaseResolve(case_id=case.id, resolve_id=resolve1.id)
        case_resolve2 = CaseResolve(case_id=case.id, resolve_id=resolve2.id)
        db.add_all([case_resolve1, case_resolve2])
        db.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test3_{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # Test ascending order
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(
            "/api/v1/resolve/list?order_by=resolve_date&order_dir=asc", headers=headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["resolves"][0]["start_date"] == "2024-01-15"
        assert body["data"]["resolves"][1]["start_date"] == "2024-01-16"

        # Test descending order
        response = client.get(
            "/api/v1/resolve/list?order_by=resolve_date&order_dir=desc", headers=headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["resolves"][0]["start_date"] == "2024-01-16"
        assert body["data"]["resolves"][1]["start_date"] == "2024-01-15"

    def test_get_resolve_list_invalid_order_by(self, db: Session) -> None:
        """Test resolve list with invalid order_by field."""
        # Create test user with unique email
        timestamp = int(time.time())
        test_user = User(
            email=f"test4_{timestamp}@unit-test.com",
            password=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User",
        )
        db.add(test_user)
        db.commit()

        # Add user role - use NAVIGATOR to avoid customer lookup
        user_role = UserRole(user_id=test_user.id, role_id=UserRoleEnum.NAVIGATOR.id)
        db.add(user_role)
        db.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test4_{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # Test invalid order_by
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(
            "/api/v1/resolve/list?order_by=invalid_field", headers=headers
        )

        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        # Check if message is a list or a string
        if isinstance(body["message"], list):
            assert (
                body["message"][0]["message"] == "Invalid order_by field: invalid_field"
            )
        else:
            assert "Invalid order_by field: invalid_field" in body["message"]

    def test_get_resolve_list_invalid_order_dir(self, db: Session) -> None:
        """Test resolve list with invalid order direction."""
        # Create test user with unique email
        timestamp = int(time.time())
        test_user = User(
            email=f"test5_{timestamp}@unit-test.com",
            password=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User",
        )
        db.add(test_user)
        db.commit()

        # Add user role - use NAVIGATOR to avoid customer lookup
        user_role = UserRole(user_id=test_user.id, role_id=UserRoleEnum.NAVIGATOR.id)
        db.add(user_role)
        db.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test5_{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # Test invalid order_dir
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/resolve/list?order_dir=invalid", headers=headers)

        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        # Check if message is a list or a string
        if isinstance(body["message"], list):
            assert (
                body["message"][0]["message"]
                == "Order direction must be 'asc' or 'desc'"
            )
        else:
            assert "Order direction must be 'asc' or 'desc'" in body["message"]

    def test_get_resolve_list_unauthorized(self) -> None:
        """Test resolve list without authentication."""
        response = client.get("/api/v1/resolve/list")

        assert response.status_code == 401

    def test_get_resolve_list_draft_status_no_title(self, db: Session) -> None:
        """Test that draft resolves don't have titles."""
        # Create test user with unique email
        timestamp = int(time.time())
        test_user = User(
            email=f"test7_{timestamp}@unit-test.com",
            password=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Add user role
        user_role = UserRole(user_id=test_user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(user_role)
        db.commit()

        # Create customer
        customer = Customer(user_id=test_user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case
        case = Case(
            start_date=date(2024, 1, 15),
            case_type=CaseTypeEnum.FAMILY_LAW
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create draft resolve
        resolve = Resolve(
            resolve_date=date(2024, 1, 15),
            user_id=test_user.id,
            customer_id=customer.id,
            result_reference_id="court",
            result_version=1,
            status=ResolveStatusEnum.IN_PROGRESS,
        )
        db.add(resolve)
        db.commit()
        db.refresh(resolve)

        # Link resolve to case
        case_resolve = CaseResolve(case_id=case.id, resolve_id=resolve.id)
        db.add(case_resolve)
        db.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test7_{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # Test resolve list endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/resolve/list", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"][0]["success"] is True
        assert body["message"][0]["message"] == "Resolve data fetched"
        assert body["data"]["total_count"] == 1
        assert body["data"]["records_in_page"] == 1
        assert len(body["data"]["resolves"]) == 1

        # Check that draft resolve has no title
        resolve_item = body["data"]["resolves"][0]
        assert resolve_item["title"] is None
        assert resolve_item["resolve_status"] == "In progress"

    def test_get_resolve_list_empty_result(self, db: Session) -> None:
        """Test resolve list with no records."""
        # Create test user with unique email
        timestamp = int(time.time())
        test_user = User(
            email=f"test6_{timestamp}@unit-test.com",
            password=get_password_hash("testpassword"),
            first_name="Test",
            last_name="User",
        )
        db.add(test_user)
        db.commit()

        # Add user role
        user_role = UserRole(user_id=test_user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(user_role)
        db.commit()

        # Create customer record
        customer = Customer(user_id=test_user.id)
        db.add(customer)
        db.commit()

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test6_{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        # Test empty result
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/resolve/list", headers=headers)

        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["message"] == "No records found"
        assert body["data"] == []
