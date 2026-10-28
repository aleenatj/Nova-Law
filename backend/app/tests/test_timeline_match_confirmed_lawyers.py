"""Tests for timeline match_confirmed_lawyers API endpoint."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Case, CaseCustomer, Customer, Lawyer, Match, User
from app.db.models.lawyer import (
    LawyerExpertType,
)
from app.enums.lawyer import ExpertTypeEnum
from app.enums.match import MatchStatusEnum
from app.enums.user import StatusEnum
from app.utils.encryption import encrypt_id


class TestTimelineMatchConfirmedLawyers:
    """Test GET /timeline/match_confirmed_lawyers endpoint."""

    def test_get_match_confirmed_lawyers_success(self, client: TestClient, db: Session) -> None:
        """Test successful retrieval of confirmed matched lawyers."""
        # Create test user with customer role
        user = User(
            email="customer@unit-test.com",
            first_name="John",
            last_name="Doe",
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create customer
        customer = Customer(user_id=user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case
        case = Case(case_no="TEST001")
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create case-customer relationship
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.commit()

        # Create lawyer user
        lawyer_user = User(
            email="lawyer@unit-test.com",
            first_name="Jane",
            last_name="Smith",
            status=StatusEnum.ACTIVE,
        )
        db.add(lawyer_user)
        db.commit()
        db.refresh(lawyer_user)

        # Create lawyer
        lawyer = Lawyer(
            user_id=lawyer_user.id,
            about="Experienced family law attorney",
            photo_url="https://example.com/photo.jpg",
            city="London",
            county="Greater London",
            country="UK",
            accredited_specialisations="Child Custody, Property Division",
        )
        db.add(lawyer)
        db.commit()
        db.refresh(lawyer)

        # Create expert types
        expert_type = LawyerExpertType(
            lawyer_id=lawyer.id, expert_type=ExpertTypeEnum.SOLICITOR
        )
        db.add(expert_type)
        db.commit()

        # Create confirmed match
        match = Match(
            lawyer_id=lawyer.id,
            case_id=case.id,
            user_id=user.id,
            status=MatchStatusEnum.INTERESTED,
            is_confirmed=True,
            confirmed_by=user.id,
        )
        db.add(match)
        db.commit()

        # Encrypt case ID
        encrypted_case_id = encrypt_id(str(case.id))

        # Make request
        response = client.get(
            "/api/v1/timeline/match_confirmed_lawyers",
            params={"case_id": encrypted_case_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"][0]["success"] is True
        assert (
            data["message"][0]["message"]
            == "Confirmed matched lawyers retrieved successfully"
        )
        assert data["data"]["total_count"] == 1
        assert data["data"]["records_in_page"] == 1
        assert len(data["data"]["match_confirmed_lawyers"]) == 1

        lawyer_data = data["data"]["match_confirmed_lawyers"][0]
        assert lawyer_data["lawyer_name"] == "Jane Smith"
        assert lawyer_data["lawyer_photo_url"] == "https://example.com/photo.jpg"
        assert lawyer_data["lawyer_about"] == "Experienced family law attorney"
        assert lawyer_data["lawyer_location"] == "London, Greater London, UK"
        assert lawyer_data["lawyer_specialization"] == "Child Custody"

    def test_get_match_confirmed_lawyers_no_confirmed_matches(self, client: TestClient, db: Session) -> None:
        """Test when there are no confirmed matches."""
        # Create test user with customer role
        user = User(
            email="customer2@unit-test.com",
            first_name="John",
            last_name="Doe",
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create customer
        customer = Customer(user_id=user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case
        case = Case(case_no="TEST002")
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create case-customer relationship
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.commit()

        # Encrypt case ID
        encrypted_case_id = encrypt_id(str(case.id))

        # Make request
        response = client.get(
            "/api/v1/timeline/match_confirmed_lawyers",
            params={"case_id": encrypted_case_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 0
        assert data["data"]["records_in_page"] == 0
        assert len(data["data"]["match_confirmed_lawyers"]) == 0

    def test_get_match_confirmed_lawyers_invalid_case_id(self, client: TestClient) -> None:
        """Test with invalid case ID format."""
        response = client.get(
            "/api/v1/timeline/match_confirmed_lawyers", params={"case_id": "invalid_id"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "invalid" in data["message"][0]["message"].lower()

    def test_get_match_confirmed_lawyers_unauthorized_case_access(self, client: TestClient, db: Session) -> None:
        """Test unauthorized access to case."""
        # Create test user with customer role
        user = User(
            email="customer3@unit-test.com",
            first_name="John",
            last_name="Doe",
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create customer
        customer = Customer(user_id=user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case (not assigned to this customer)
        case = Case(case_no="TEST003")
        db.add(case)
        db.commit()
        db.refresh(case)

        # Encrypt case ID
        encrypted_case_id = encrypt_id(str(case.id))

        # Make request
        response = client.get(
            "/api/v1/timeline/match_confirmed_lawyers",
            params={"case_id": encrypted_case_id},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "not authorized" in data["message"][0]["message"].lower()

    def test_get_match_confirmed_lawyers_multiple_confirmed_lawyers(self, client: TestClient, db: Session) -> None:
        """Test with multiple confirmed lawyers."""
        # Create test user with customer role
        user = User(
            email="customer4@unit-test.com",
            first_name="John",
            last_name="Doe",
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create customer
        customer = Customer(user_id=user.id)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create case
        case = Case(case_no="TEST004")
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create case-customer relationship
        case_customer = CaseCustomer(case_id=case.id, customer_id=customer.id)
        db.add(case_customer)
        db.commit()

        # Create two lawyers
        lawyer1_user = User(
            email="lawyer1@unit-test.com",
            first_name="Jane",
            last_name="Smith",
            status=StatusEnum.ACTIVE,
        )
        lawyer2_user = User(
            email="lawyer2@unit-test.com",
            first_name="Bob",
            last_name="Johnson",
            status=StatusEnum.ACTIVE,
        )
        db.add_all([lawyer1_user, lawyer2_user])
        db.commit()
        db.refresh(lawyer1_user)
        db.refresh(lawyer2_user)

        lawyer1 = Lawyer(
            user_id=lawyer1_user.id,
            about="Family law expert",
            city="London",
            country="UK",
            accredited_specialisations="Divorce, Child Custody",
        )
        lawyer2 = Lawyer(
            user_id=lawyer2_user.id,
            about="Property law specialist",
            city="Manchester",
            country="UK",
            accredited_specialisations="Property Division, Financial Claims",
        )
        db.add_all([lawyer1, lawyer2])
        db.commit()
        db.refresh(lawyer1)
        db.refresh(lawyer2)

        # Create confirmed matches for both lawyers
        match1 = Match(
            lawyer_id=lawyer1.id,
            case_id=case.id,
            user_id=user.id,
            status=MatchStatusEnum.INTERESTED,
            is_confirmed=True,
            confirmed_by=user.id,
        )
        match2 = Match(
            lawyer_id=lawyer2.id,
            case_id=case.id,
            user_id=user.id,
            status=MatchStatusEnum.INTERESTED,
            is_confirmed=True,
            confirmed_by=user.id,
        )
        db.add_all([match1, match2])
        db.commit()

        # Encrypt case ID
        encrypted_case_id = encrypt_id(str(case.id))

        # Make request
        response = client.get(
            "/api/v1/timeline/match_confirmed_lawyers",
            params={"case_id": encrypted_case_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 2
        assert data["data"]["records_in_page"] == 2
        assert len(data["data"]["match_confirmed_lawyers"]) == 2

        # Check that both lawyers are in the response
        lawyer_names = [item["lawyer_name"] for item in data["data"]["match_confirmed_lawyers"]]
        assert "Jane Smith" in lawyer_names
        assert "Bob Johnson" in lawyer_names
