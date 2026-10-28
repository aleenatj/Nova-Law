from sqlalchemy.orm import Session

from app.db.models.lawyer import Lawyer, LawyerExpertType
from app.db.models.user import User
from app.enums.lawyer import (
    ExpertTypeEnum,
    LawyerStatusEnum,
    MatterTypeEnum,
    RegulatorEnum,
    RelationshipTypeEnum,
)
from app.utils.encryption import encrypt_id


class TestLawyerAPI:
    """Test cases for Lawyer API endpoints."""

    def test_create_lawyer_success(self, client, db: Session):
        """Test successful lawyer creation."""
        # Create a test user first
        test_user = User(
            email="lawyer@unit-test.com",
            first_name="Test",
            last_name="Lawyer",
            password="testpassword123",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Test data
        lawyer_data = {
            "status": LawyerStatusEnum.ACTIVE,
            "city": "London",
            "county": "Greater London",
            "regulator": RegulatorEnum.SRA,
            "expert_types": [ExpertTypeEnum.SOLICITOR],
            "relationship_types": [RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS],
            "matter_types": [MatterTypeEnum.FINANCIAL_CLAIMS],
        }

        response = client.post("/api/v1/lawyer", json=lawyer_data)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] is not None
        assert body["data"]["city"] == "London"
        assert body["data"]["regulator"] == RegulatorEnum.SRA.value

        # Verify in database
        lawyer = db.query(Lawyer).filter(Lawyer.user_id == test_user.id).first()
        assert lawyer is not None
        assert lawyer.city == "London"
        assert lawyer.regulator == RegulatorEnum.SRA

        # Verify multi-select data
        expert_types = (
            db.query(LawyerExpertType)
            .filter(LawyerExpertType.lawyer_id == lawyer.id)
            .all()
        )
        assert len(expert_types) == 1
        assert expert_types[0].expert_type == ExpertTypeEnum.SOLICITOR

    def test_create_lawyer_invalid_user_id(self, client, db: Session):
        """Test lawyer creation with invalid user ID."""
        lawyer_data = {
            "status": LawyerStatusEnum.ACTIVE,
            "city": "London",
            "expert_types": [],
            "relationship_types": [],
            "matter_types": [],
        }

        response = client.post("/api/v1/lawyer", json=lawyer_data)

        assert response.status_code == 500
        body = response.json()
        assert body["success"] is False
        assert "Failed to create lawyer" in body["message"][0]["message"]

    def test_update_lawyer_success(self, client, db: Session):
        """Test successful lawyer update."""
        # Create a test user and lawyer
        test_user = User(
            email="update@unit-test.com",
            first_name="Update",
            last_name="Lawyer",
            password="testpassword123",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        lawyer = Lawyer(
            status=LawyerStatusEnum.ACTIVE, city="London", user_id=test_user.id
        )
        db.add(lawyer)
        db.commit()
        db.refresh(lawyer)

        # Update data with encrypted ID
        encrypted_lawyer_id = encrypt_id(str(lawyer.id))
        update_data = {
            "id": encrypted_lawyer_id,
            "city": "Manchester",
            "regulator": RegulatorEnum.BSB,
            "expert_types": [ExpertTypeEnum.BARRISTER],
        }

        response = client.put("/api/v1/lawyer", json=update_data)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] == encrypted_lawyer_id
        assert body["data"]["city"] == "Manchester"
        assert body["data"]["regulator"] == RegulatorEnum.BSB.value

        # Verify in database
        db.refresh(lawyer)
        assert lawyer.city == "Manchester"
        assert lawyer.regulator == RegulatorEnum.BSB

        # Verify expert types updated
        expert_types = (
            db.query(LawyerExpertType)
            .filter(LawyerExpertType.lawyer_id == lawyer.id)
            .all()
        )
        assert len(expert_types) == 1
        assert expert_types[0].expert_type == ExpertTypeEnum.BARRISTER

    def test_update_lawyer_not_found(self, client, db: Session):
        """Test lawyer update with non-existent ID."""
        fake_encrypted_id = encrypt_id("99999")
        update_data = {"id": fake_encrypted_id, "city": "Manchester"}

        response = client.put("/api/v1/lawyer", json=update_data)

        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["message"][0]["message"] == "Lawyer not found"

    def test_update_lawyer_invalid_id(self, client, db: Session):
        """Test lawyer update with invalid ID format."""
        update_data = {"id": "invalid_id", "city": "Manchester"}

        response = client.put("/api/v1/lawyer", json=update_data)

        assert response.status_code == 500
        body = response.json()
        assert body["success"] is False
        assert "Failed to update lawyer" in body["message"][0]["message"]

    def test_search_lawyer_success(self, client, db: Session):
        """Test successful lawyer search."""
        # Create test users and lawyers
        test_user1 = User(
            email="search1@unit-test.com",
            first_name="Search1",
            last_name="Lawyer",
            password="testpassword123",
        )
        test_user2 = User(
            email="search2@unit-test.com",
            first_name="Search2",
            last_name="Lawyer",
            password="testpassword123",
        )
        db.add_all([test_user1, test_user2])
        db.commit()
        db.refresh(test_user1)
        db.refresh(test_user2)

        lawyer1 = Lawyer(
            status=LawyerStatusEnum.ACTIVE, city="London", user_id=test_user1.id
        )
        lawyer2 = Lawyer(
            status=LawyerStatusEnum.ACTIVE, city="Manchester", user_id=test_user2.id
        )
        db.add_all([lawyer1, lawyer2])
        db.commit()

        # Search request using GET with query parameters
        search_params = {
            "page": 1,
            "limit": 10,
            "order_by": "created_at",
            "order_dir": "desc",
        }

        response = client.get("/api/v1/lawyer", params=search_params)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["total_count"] == 2
        assert body["data"]["records_in_page"] == 2
        assert len(body["data"]["items"]) == 2

    def test_search_lawyer_with_filters(self, client, db: Session):
        """Test lawyer search with filters."""
        # Create test user and lawyer
        test_user = User(
            email="filter@unit-test.com",
            first_name="Filter",
            last_name="Lawyer",
            password="testpassword123",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        lawyer = Lawyer(
            status=LawyerStatusEnum.ACTIVE,
            city="London",
            county="Greater London",
            regulator=RegulatorEnum.SRA,
            user_id=test_user.id,
        )
        db.add(lawyer)
        db.commit()

        # Add expert type
        expert_type = LawyerExpertType(
            lawyer_id=lawyer.id, expert_type=ExpertTypeEnum.SOLICITOR
        )
        db.add(expert_type)
        db.commit()

        # Search with filters using GET with query parameters
        search_params = {
            "city": "London",
            "regulator": RegulatorEnum.SRA.value,
            "expert_type": ExpertTypeEnum.SOLICITOR.value,
        }

        response = client.get("/api/v1/lawyer", params=search_params)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["total_count"] == 1
        assert body["data"]["items"][0]["city"] == "London"

    def test_get_lawyer_by_id_success(self, client, db: Session):
        """Test successful lawyer retrieval by ID."""
        # Create test user and lawyer
        test_user = User(
            email="get@unit-test.com",
            first_name="Get",
            last_name="Lawyer",
            password="testpassword123",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        lawyer = Lawyer(
            status=LawyerStatusEnum.ACTIVE, city="London", user_id=test_user.id
        )
        db.add(lawyer)
        db.commit()
        db.refresh(lawyer)

        # Get lawyer by ID using encrypted ID
        encrypted_lawyer_id = encrypt_id(str(lawyer.id))
        response = client.get(f"/api/v1/lawyer/{encrypted_lawyer_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] == encrypted_lawyer_id
        assert body["data"]["city"] == "London"

    def test_get_lawyer_by_id_not_found(self, client, db: Session):
        """Test lawyer retrieval with non-existent ID."""
        fake_encrypted_id = encrypt_id("99999")
        response = client.get(f"/api/v1/lawyer/{fake_encrypted_id}")

        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["message"][0]["message"] == "Lawyer not found"

    def test_get_lawyer_by_id_invalid_format(self, client, db: Session):
        """Test lawyer retrieval with invalid ID format."""
        response = client.get("/api/v1/lawyer/invalid_id")

        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert body["message"][0]["message"] == "Invalid lawyer ID format"

    def test_create_lawyer_with_expert_types(self, client, db: Session):
        """Test lawyer creation with multiple expert types."""
        # Create test user
        test_user = User(
            email="expert@unit-test.com",
            first_name="Expert",
            last_name="Lawyer",
            password="testpassword123",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Test data with multiple expert types
        lawyer_data = {
            "status": LawyerStatusEnum.ACTIVE,
            "city": "London",
            "user_id": test_user.id,
            "expert_types": [
                ExpertTypeEnum.SOLICITOR,
                ExpertTypeEnum.FAMILY_CONSULTANT,
            ],
            "relationship_types": [],
            "matter_types": [],
        }

        response = client.post("/api/v1/lawyer", json=lawyer_data)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

        # Verify expert types in database
        lawyer = db.query(Lawyer).filter(Lawyer.user_id == test_user.id).first()
        expert_types = (
            db.query(LawyerExpertType)
            .filter(LawyerExpertType.lawyer_id == lawyer.id)
            .all()
        )
        assert len(expert_types) == 2
        expert_type_values = [et.expert_type for et in expert_types]
        assert ExpertTypeEnum.SOLICITOR in expert_type_values
        assert ExpertTypeEnum.FAMILY_CONSULTANT in expert_type_values

    def test_update_lawyer_expert_types(self, client, db: Session):
        """Test lawyer update with expert types modification."""
        # Create test user and lawyer
        test_user = User(
            email="update_expert@unit-test.com",
            first_name="UpdateExpert",
            last_name="Lawyer",
            password="testpassword123",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        lawyer = Lawyer(
            status=LawyerStatusEnum.ACTIVE, city="London", user_id=test_user.id
        )
        db.add(lawyer)
        db.commit()
        db.refresh(lawyer)

        # Add initial expert type
        initial_expert = LawyerExpertType(
            lawyer_id=lawyer.id, expert_type=ExpertTypeEnum.SOLICITOR
        )
        db.add(initial_expert)
        db.commit()

        # Update with new expert types using encrypted ID
        encrypted_lawyer_id = encrypt_id(str(lawyer.id))
        update_data = {
            "id": encrypted_lawyer_id,
            "expert_types": [ExpertTypeEnum.BARRISTER, ExpertTypeEnum.ARBITRATOR],
        }

        response = client.put("/api/v1/lawyer", json=update_data)

        assert response.status_code == 200

        # Verify expert types updated
        expert_types = (
            db.query(LawyerExpertType)
            .filter(LawyerExpertType.lawyer_id == lawyer.id)
            .all()
        )
        assert len(expert_types) == 2
        expert_type_values = [et.expert_type for et in expert_types]
        assert ExpertTypeEnum.BARRISTER in expert_type_values
        assert ExpertTypeEnum.ARBITRATOR in expert_type_values
        assert (
            ExpertTypeEnum.SOLICITOR not in expert_type_values
        )  # Old one should be removed
