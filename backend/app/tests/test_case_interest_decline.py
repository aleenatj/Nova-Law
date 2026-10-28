"""Tests for case interest and decline endpoints."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.models.case import Case
from app.db.models.case_customer import CaseCustomer
from app.db.models.customer import Customer
from app.db.models.lawyer import Lawyer
from app.db.models.match import Match
from app.db.models.user import User
from app.db.models.user_role import UserRole
from app.enums.case import CasePriorityEnum, CaseStatusEnum, CaseTypeEnum
from app.enums.match import MatchStatusEnum
from app.enums.user_role import UserRoleEnum


class TestCaseInterestDecline:
    """Test case for case interest and decline endpoints."""

    def test_lawyer_interest_without_lawyer_id_success(self, db: Session) -> None:
        """Test lawyer can express interest without providing lawyer_id."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer1.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Commit user and role to make them visible to the login endpoint
        db.commit()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.PENDING,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer1.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        print(f"Login response status: {login_response.status_code}")
        print(f"Login response body: {login_response.text}")
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        print(f"Case interest response status: {response.status_code}")
        print(f"Case interest response body: {response.text}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (
            "Case interest updated successfully"
            in response.json()["message"][0]["message"]
        )

    def test_lawyer_interest_with_lawyer_id_success(self, db: Session) -> None:
        """Test lawyer can express interest with providing lawyer_id."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer2.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer2.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.PENDING,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer2.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint with lawyer_id
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        encrypted_lawyer_id = encrypt_id(str(lawyer.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id, "lawyer_id": encrypted_lawyer_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (
            "Case interest updated successfully"
            in response.json()["message"][0]["message"]
        )

    def test_lawyer_interest_with_mismatched_lawyer_id_forbidden(
        self, db: Session
    ) -> None:
        """Test lawyer cannot express interest with mismatched lawyer_id."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer3.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer3.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.PENDING,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer3.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint with mismatched lawyer_id
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        # Use a different lawyer ID that doesn't match the current user
        different_lawyer_id = encrypt_id("999")
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id, "lawyer_id": different_lawyer_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert response.json()["success"] is False
        assert "Access denied: Lawyer ID mismatch" in response.json()["message"]

    def test_navigator_interest_without_lawyer_id_bad_request(
        self, db: Session
    ) -> None:
        """Test navigator cannot express interest without providing lawyer_id."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.navigator1.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Navigator",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.NAVIGATOR.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer4.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.navigator1.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint without lawyer_id (should fail)
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert "Lawyer ID is mandatory for navigators" in response.json()["message"]

    def test_navigator_interest_with_lawyer_id_success(self, db: Session) -> None:
        """Test navigator can express interest with providing lawyer_id."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.navigator2.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Navigator",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.NAVIGATOR.id)
        db.add(user_role)
        db.flush()

        # Create another user for lawyer
        lawyer_user = User(
            email=f"test.lawyer4.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(lawyer_user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=lawyer_user.id)
        db.add(lawyer)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer5.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.PENDING,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.navigator2.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint with lawyer_id
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        encrypted_lawyer_id = encrypt_id(str(lawyer.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id, "lawyer_id": encrypted_lawyer_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (
            "Case interest updated successfully"
            in response.json()["message"][0]["message"]
        )

    def test_case_decline_success(self, db: Session) -> None:
        """Test case decline endpoint works correctly."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer5.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer6.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.PENDING,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer5.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case decline endpoint
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/decline",
            json={
                "case_id": encrypted_case_id,
                "decline_reason": {
                    "reason": ["Conflict of interest"],
                    "reason_other": "Cannot take this case due to conflict",
                },
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (
            "Case decline updated successfully"
            in response.json()["message"][0]["message"]
        )

    def test_no_match_found_error(self, db: Session) -> None:
        """Test error when no match is found for case and lawyer."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer6.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer7.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer6.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint with non-existent match
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404
        assert response.json()["success"] is False
        assert "No match found" in response.json()["message"]

    def test_unauthorized_user_forbidden(self, db: Session) -> None:
        """Test unauthorized user (customer) cannot access the endpoints."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.customer1.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create customer
        customer = Customer(user_id=user.id)
        db.add(customer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(user_role)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.customer1.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint (should fail due to insufficient permissions)
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id("123")  # Use a dummy case ID
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert response.json()["success"] is False
        assert (
            "You do not have permission to access this resource."
            in response.json()["message"]
        )

    def test_case_interest_duplicate_action(self, db: Session) -> None:
        """Test case interest endpoint when action is already completed."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer7.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer8.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match with INTERESTED status (already completed)
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.INTERESTED,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer7.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint with already completed action
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (
            "Case interest action already completed"
            in response.json()["message"][0]["message"]
        )
        assert response.json()["data"] == []

    def test_case_decline_duplicate_action(self, db: Session) -> None:
        """Test case decline endpoint when action is already completed."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer8.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer9.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match with DECLINED status (already completed)
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.DECLINED,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer8.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case decline endpoint with already completed action
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/decline",
            json={
                "case_id": encrypted_case_id,
                "decline_reason": {
                    "reason": ["Conflict of interest"],
                    "reason_other": "Cannot take this case due to conflict",
                },
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (
            "Case decline action already completed"
            in response.json()["message"][0]["message"]
        )
        assert response.json()["data"] == []

    def test_case_interest_after_decline_success(self, db: Session) -> None:
        """Test case interest endpoint when case was previously declined."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer9.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer10.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match with DECLINED status (previously declined)
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.DECLINED,
            declined_reason={"reason": ["Conflict of interest"]},
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer9.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case interest endpoint with previously declined case
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (
            "Case interest updated successfully"
            in response.json()["message"][0]["message"]
        )
        assert response.json()["data"] == []

    def test_case_decline_when_already_interested_forbidden(self, db: Session) -> None:
        """Test case decline endpoint when case is already marked as interested."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.lawyer10.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create lawyer
        lawyer = Lawyer(user_id=user.id)
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer11.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match with INTERESTED status (already interested)
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.INTERESTED,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.lawyer10.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Test case decline endpoint with already interested case
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/decline",
            json={
                "case_id": encrypted_case_id,
                "decline_reason": {
                    "reason": ["Conflict of interest"],
                    "reason_other": "Cannot take this case due to conflict",
                },
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert (
            "Cannot decline a case that is already marked as interested"
            in response.json()["message"]
        )

    def test_inactive_lawyer_forbidden(self, db: Session) -> None:
        """Test that inactive lawyers cannot perform case actions."""
        # Create test data with unique timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user = User(
            email=f"test.inactive.lawyer.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="InactiveLawyer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(user)
        db.flush()

        # Create active lawyer first
        lawyer = Lawyer(user_id=user.id, status="Active")
        db.add(lawyer)
        db.flush()

        # Create user role
        user_role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
        db.add(user_role)
        db.flush()

        # Create customer for the case
        customer_user = User(
            email=f"test.customer12.{timestamp}@unit-test.com",
            first_name="Test",
            last_name="Customer",
            password=get_password_hash("testpassword"),
            status="Active",
        )
        db.add(customer_user)
        db.flush()

        customer = Customer(user_id=customer_user.id)
        db.add(customer)
        db.flush()

        # Create case
        case = Case(
            start_date=datetime.now().date(),
            case_type=CaseTypeEnum.FAMILY_LAW,
            priority=CasePriorityEnum.MEDIUM,
            status=CaseStatusEnum.OPEN,
        )
        db.add(case)
        db.flush()

        # Create case customer
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.flush()

        # Create match
        match = Match(
            case_id=case.id,
            lawyer_id=lawyer.id,
            user_id=customer_user.id,
            status=MatchStatusEnum.PENDING,
        )
        db.add(match)
        db.flush()

        # Commit all changes to make them visible to the login endpoint
        db.commit()

        # Login to get access token
        from app.tests.conftest import client

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"test.inactive.lawyer.{timestamp}@unit-test.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Now make the lawyer inactive
        object.__setattr__(lawyer, "status", "Inactive")
        db.commit()

        # Test case interest endpoint with inactive lawyer
        from app.utils.encryption import encrypt_id

        encrypted_case_id = encrypt_id(str(case.id))
        response = client.post(
            "/api/v1/case/interest",
            json={"case_id": encrypted_case_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404
        assert response.json()["success"] is False
        assert "Lawyer profile not found" in response.json()["message"]
