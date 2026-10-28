"""Tests for law firm API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.db.models.law_firm import LawFirm
from app.main import app
from app.utils.encryption import encrypt_id


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_law_firm_data():
    """Sample law firm data for testing."""
    return {
        "name": "Test Law Firm",
        "contact_person": "John Doe",
        "contact_no": "+1-555-123-4567",
        "contact_email": "test@lawfirm.com",
        "address_line_1": "123 Test Street",
        "city": "Test City",
        "state": "TS",
        "postal_code": "12345",
        "country": "Test Country",
        "law_firm_type": "Boutique",
    }


@pytest.fixture
def sample_search_request():
    """Sample search request data."""
    return {
        "name": "Test",
        "page": 1,
        "limit": 10,
        "order_by": "name",
        "order_dir": "asc",
    }


class TestLawFirmGetById:
    """Test GET /law-firm/{law_firm_id} endpoint."""

    def test_get_law_firm_by_id_success(self, client, db_session, sample_law_firm_data):
        """Test successful retrieval of law firm by ID."""
        # Create a law firm first
        law_firm = LawFirm(**sample_law_firm_data)
        db_session.add(law_firm)
        db_session.commit()
        db_session.refresh(law_firm)

        # Encrypt the ID
        encrypted_id = encrypt_id(str(law_firm.id))

        # Make request
        response = client.get(f"/api/v1/law-firm/{encrypted_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == sample_law_firm_data["name"]
        assert data["data"]["contact_person"] == sample_law_firm_data["contact_person"]

    def test_get_law_firm_by_id_not_found(self, client):
        """Test getting non-existent law firm."""
        # Use a valid encrypted ID format but for non-existent record
        fake_encrypted_id = encrypt_id("99999")

        response = client.get(f"/api/v1/law-firm/{fake_encrypted_id}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_law_firm_by_id_invalid_format(self, client):
        """Test getting law firm with invalid ID format."""
        response = client.get("/api/v1/law-firm/invalid_id")

        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()


class TestLawFirmSearch:
    """Test GET /law-firm and POST /law-firm/search endpoints."""

    def test_search_law_firms_success(self, client, db_session, sample_law_firm_data):
        """Test successful search for law firms."""
        # Create multiple law firms
        law_firm1 = LawFirm(**sample_law_firm_data)
        law_firm2 = LawFirm(**{**sample_law_firm_data, "name": "Another Law Firm"})
        db_session.add_all([law_firm1, law_firm2])
        db_session.commit()

        # Search request
        search_data = {
            "name": "Test",
            "page": 1,
            "limit": 10,
            "order_by": "name",
            "order_dir": "asc",
        }

        response = client.get("/api/v1/law-firm", params=search_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] >= 1
        assert len(data["data"]["law_firms"]) >= 1

    def test_search_law_firms_with_filters(
        self, client, db_session, sample_law_firm_data
    ):
        """Test search with various filters."""
        # Create law firm with specific city
        law_firm = LawFirm(**{**sample_law_firm_data, "city": "New York"})
        db_session.add(law_firm)
        db_session.commit()

        # Search by city
        search_data = {"city": "New York", "page": 1, "limit": 10}

        response = client.get("/api/v1/law-firm", params=search_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] >= 1

    def test_search_law_firms_pagination(
        self, client, db_session, sample_law_firm_data
    ):
        """Test search pagination."""
        # Create multiple law firms
        for i in range(15):
            law_firm = LawFirm(**{**sample_law_firm_data, "name": f"Law Firm {i}"})
            db_session.add(law_firm)
        db_session.commit()

        # Test first page
        search_data = {"page": 1, "limit": 5}
        response = client.get("/api/v1/law-firm", params=search_data)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["records_in_page"] == 5
        assert data["data"]["total_count"] >= 15

        # Test second page
        search_data = {"page": 2, "limit": 5}
        response = client.get("/api/v1/law-firm", params=search_data)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["records_in_page"] == 5

    def test_search_law_firms_empty_result(self, client, db_session):
        """Test search with no results."""
        search_data = {"name": "NonExistentLawFirm", "page": 1, "limit": 10}

        response = client.get("/api/v1/law-firm", params=search_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 0
        assert len(data["data"]["law_firms"]) == 0


class TestLawFirmEncryption:
    """Test ID encryption/decryption in responses."""

    def test_response_ids_are_encrypted(self, client, db_session, sample_law_firm_data):
        """Test that response IDs are always encrypted."""
        # Create a law firm
        law_firm = LawFirm(**sample_law_firm_data)
        db_session.add(law_firm)
        db_session.commit()
        db_session.refresh(law_firm)

        # Get by ID
        encrypted_id = encrypt_id(str(law_firm.id))
        response = client.get(f"/api/v1/law-firm/{encrypted_id}")

        assert response.status_code == 200
        data = response.json()

        # ID should be encrypted (different from raw ID)
        response_id = data["data"]["id"]
        assert response_id != str(law_firm.id)
        assert len(response_id) > 10  # Encrypted IDs are longer

    def test_search_response_ids_are_encrypted(
        self, client, db_session, sample_law_firm_data
    ):
        """Test that search response IDs are encrypted."""
        # Create a law firm
        law_firm = LawFirm(**sample_law_firm_data)
        db_session.add(law_firm)
        db_session.commit()
        db_session.refresh(law_firm)

        # Search
        search_data = {"page": 1, "limit": 10}
        response = client.get("/api/v1/law-firm", params=search_data)

        assert response.status_code == 200
        data = response.json()

        if data["data"]["law_firms"]:
            # ID should be encrypted
            response_id = data["data"]["law_firms"][0]["id"]
            assert response_id != str(law_firm.id)
            assert len(response_id) > 10
