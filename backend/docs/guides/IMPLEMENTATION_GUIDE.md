# Nova Law API Versioning - Implementation Guide

**Document Version:** 1.0
**Date:** July 29, 2025
**Status:** Ready for Implementation

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
3. [Phase 2: Version Management Tools](#phase-2-version-management-tools)
4. [Phase 3: Migration Framework](#phase-3-migration-framework)
5. [Phase 4: Monitoring & Documentation](#phase-4-monitoring--documentation)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Checklist](#deployment-checklist)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- FastAPI project structure
- Existing API endpoints (v1)
- Git repository

### **Installation Steps**

1. **Copy Versioning Files**
```bash
# Copy the new versioning modules
cp app/core/versioning.py backend/app/core/
cp app/middleware/versioning.py backend/app/middleware/
cp app/utils/schema_migration.py backend/app/utils/
cp app/monitoring/version_tracking.py backend/app/monitoring/
```

2. **Update Main Application**
```bash
# Backup current main.py
cp backend/app/main.py backend/app/main_backup.py

# Use the updated main.py
cp app/main_updated.py backend/app/main.py
```

3. **Test the Implementation**
```bash
cd backend
python -m pytest tests/ -v
uvicorn app.main:app --reload
```

---

## 🏗️ Phase 1: Infrastructure Setup

### **Step 1.1: Create Directory Structure**

```bash
# Create version-specific directories
mkdir -p backend/app/api/v2
mkdir -p backend/app/schemas/v2
mkdir -p backend/app/middleware
mkdir -p backend/app/monitoring

# Create __init__.py files
touch backend/app/api/v2/__init__.py
touch backend/app/schemas/v2/__init__.py
touch backend/app/middleware/__init__.py
touch backend/app/monitoring/__init__.py
```

### **Step 1.2: Install Dependencies**

Add to `backend/requirements.txt`:
```txt
# Versioning dependencies
pydantic>=2.5.0
structlog>=24.1.0
```

### **Step 1.3: Update Configuration**

Add to `backend/app/core/config.py`:
```python
# Versioning settings
API_VERSIONING_ENABLED: bool = True
DEFAULT_API_VERSION: str = "v1"
SUPPORTED_VERSIONS: list[str] = ["v1"]
DEPRECATED_VERSIONS: list[str] = []
```

### **Step 1.4: Initialize Version Manager**

Create `backend/app/core/versioning.py`:
```python
# Copy the versioning.py content from the strategy document
```

### **Step 1.5: Add Middleware**

Create `backend/app/middleware/versioning.py`:
```python
# Copy the versioning middleware content
```

### **Step 1.6: Update Main Application**

Update `backend/app/main.py`:
```python
# Add versioning middleware
from app.middleware.versioning import (
    VersionDetectionMiddleware,
    VersionValidationMiddleware,
    DeprecationWarningMiddleware
)

# Add middleware in correct order
app.add_middleware(VersionDetectionMiddleware)
app.add_middleware(VersionValidationMiddleware)
app.add_middleware(DeprecationWarningMiddleware)
```

---

## 🛠️ Phase 2: Version Management Tools

### **Step 2.1: Create Schema Migration Utilities**

Create `backend/app/utils/schema_migration.py`:
```python
# Copy the schema migration content
```

### **Step 2.2: Add Version Detection**

Update existing endpoints to use version detection:

```python
# Example: Update auth.py
from app.core.versioning import version_detector

@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and return tokens."""
    # Get detected version
    version = getattr(request.state, "api_version", "v1")

    # Version-specific logic
    if version == "v2":
        # Enhanced v2 login logic
        return await login_v2(user_credentials, db)
    else:
        # Standard v1 login logic
        return await login_v1(user_credentials, db)
```

### **Step 2.3: Create Version-Specific Schemas**

Create `backend/app/schemas/v2/auth.py`:
```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """v2 User creation schema with enhanced validation."""
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)
    # NEW: Phone number field
    phone_number: str | None = Field(None, description="User phone number")
    # NEW: Terms acceptance
    accept_terms: bool = Field(..., description="Terms acceptance required")
```

### **Step 2.4: Add Migration Functions**

Create migration utilities:

```python
# backend/app/utils/migrations.py
from app.utils.schema_migration import schema_migrator

def migrate_user_create_v1_to_v2(v1_data: dict) -> dict:
    """Migrate user creation from v1 to v2."""
    return schema_migrator.migrate_data(
        v1_data, "v1", "v2", "user_create"
    )

def migrate_user_create_v2_to_v1(v2_data: dict) -> dict:
    """Migrate user creation from v2 to v1 (backward compatibility)."""
    return schema_migrator.migrate_data(
        v2_data, "v2", "v1", "user_create"
    )
```

---

## 🔄 Phase 3: Migration Framework

### **Step 3.1: Create v2 API Endpoints**

Create `backend/app/api/v2/auth.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.v2.auth import UserCreate, UserLogin, TokenResponse
from app.utils.dependencies import get_db
from app.utils.schema_migration import schema_migrator

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register_v2(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user with v2 enhanced validation."""
    # Enhanced v2 registration logic
    # Include phone number validation
    # Include terms acceptance validation

    # Create user with v2 fields
    user = create_user_v2(db, user_data)

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/login", response_model=TokenResponse)
async def login_v2(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user with v2 enhanced features."""
    # Enhanced v2 login logic
    # Include device tracking
    # Include remember me functionality

    return await login_user_v2(user_credentials, db)
```

### **Step 3.2: Add Deprecation Management**

Create `backend/app/core/deprecation.py`:
```python
from datetime import datetime
from typing import Dict

class DeprecationManager:
    def __init__(self):
        self.deprecated_endpoints: Dict[str, Dict] = {}

    def mark_deprecated(
        self,
        endpoint: str,
        version: str,
        sunset_date: datetime,
        alternative: str = None
    ):
        """Mark an endpoint as deprecated."""
        self.deprecated_endpoints[endpoint] = {
            "version": version,
            "sunset_date": sunset_date,
            "alternative": alternative
        }

    def get_deprecation_info(self, endpoint: str) -> Dict:
        """Get deprecation information for an endpoint."""
        return self.deprecated_endpoints.get(endpoint, {})
```

### **Step 3.3: Update Main Application for v2**

Update `backend/app/main.py`:
```python
# Include v2 routers
from app.api.v2 import auth as auth_v2, users as users_v2

# Add v2 routers
app.include_router(auth_v2.router, prefix="/api/v2", tags=["authentication"])
app.include_router(users_v2.router, prefix="/api/v2", tags=["users"])
```

### **Step 3.4: Add Version-Specific Endpoints**

```python
# Example: Add version-specific health checks
@app.get("/api/v1/health")
async def health_check_v1():
    """v1 health check."""
    return {
        "status": "healthy",
        "version": "v1",
        "features": ["basic_health_check"]
    }

@app.get("/api/v2/health")
async def health_check_v2():
    """v2 health check with enhanced metrics."""
    return {
        "status": "healthy",
        "version": "v2",
        "features": ["enhanced_metrics", "performance_data"],
        "metrics": {
            "response_time": "15ms",
            "uptime": "99.9%",
            "active_connections": 150
        }
    }
```

---

## 📊 Phase 4: Monitoring & Documentation

### **Step 4.1: Create Monitoring Endpoints**

Create `backend/app/api/v1/monitoring.py`:
```python
from fastapi import APIRouter
from app.monitoring.version_tracking import version_tracker, alert_manager

router = APIRouter()

@router.get("/usage")
async def get_usage_stats(days: int = 30):
    """Get API usage statistics."""
    return version_tracker.get_usage_report(days=days)

@router.get("/migrations")
async def get_migration_progress():
    """Get migration progress information."""
    return version_tracker.get_migration_report()

@router.get("/alerts")
async def get_alerts():
    """Get current alerts for version management."""
    return alert_manager.check_alerts(version_tracker)
```

### **Step 4.2: Add Version Information Endpoints**

```python
@app.get("/api/versions")
async def get_api_versions():
    """Get information about supported API versions."""
    return {
        "supported_versions": [v.value for v in version_manager.supported_versions],
        "deprecated_versions": [v.value for v in version_manager.deprecated_versions],
        "latest_version": version_manager.get_latest_version().value,
        "recommended_version": version_manager.get_recommended_version().value
    }

@app.get("/api/versions/{version}/info")
async def get_version_info(version: str):
    """Get detailed information about a specific API version."""
    if not version_manager.is_supported(version):
        return {
            "error": "Unsupported version",
            "message": f"Version {version} is not supported",
            "supported_versions": [v.value for v in version_manager.supported_versions]
        }

    deprecation_info = version_manager.get_deprecation_info(version)

    return {
        "version": version,
        "supported": True,
        "deprecated": version_manager.is_deprecated(version),
        "deprecation_info": deprecation_info
    }
```

### **Step 4.3: Create Documentation Templates**

Create `backend/docs/api/README.md`:
```markdown
# Nova Law API Documentation

## Versioning Strategy

This API uses URI versioning with the following pattern:
- `/api/v1/` - Current stable version
- `/api/v2/` - Latest version with new features

## Migration Guides

- [v1 to v2 Migration Guide](migration/v1-to-v2.md)
- [Breaking Changes](migration/breaking-changes.md)
- [Best Practices](migration/best-practices.md)

## Version Lifecycle

- **v1**: Stable, fully supported
- **v2**: Latest features, recommended for new integrations
- **v0**: Deprecated, will be removed
```

### **Step 4.4: Add Automated Documentation**

Create `backend/app/utils/api_docs.py`:
```python
from typing import Dict, List
import json

class APIDocumentationGenerator:
    def __init__(self):
        self.version_docs: Dict[str, Dict] = {}

    def add_version_documentation(
        self,
        version: str,
        endpoints: List[Dict],
        schemas: Dict,
        examples: Dict
    ):
        """Add documentation for a specific version."""
        self.version_docs[version] = {
            "endpoints": endpoints,
            "schemas": schemas,
            "examples": examples,
            "generated_at": time.time()
        }

    def generate_version_docs(self, version: str) -> str:
        """Generate documentation for a specific version."""
        if version not in self.version_docs:
            return f"No documentation available for version {version}"

        docs = self.version_docs[version]

        # Generate markdown documentation
        markdown = f"# API v{version} Documentation\n\n"

        # Add endpoints
        markdown += "## Endpoints\n\n"
        for endpoint in docs["endpoints"]:
            markdown += f"### {endpoint['method']} {endpoint['path']}\n"
            markdown += f"{endpoint['description']}\n\n"

        return markdown
```

---

## 🧪 Testing Strategy

### **Step 5.1: Create Version-Specific Tests**

Create `backend/tests/test_versioning.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_version_detection():
    """Test version detection from URL path."""
    response = client.get("/api/v1/status/health")
    assert response.status_code == 200
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"

def test_version_headers():
    """Test version headers in responses."""
    response = client.get("/api/v1/status/health")
    assert "X-API-Version" in response.headers
    assert "X-Latest-API-Version" in response.headers
    assert "X-Supported-Versions" in response.headers

def test_unsupported_version():
    """Test handling of unsupported versions."""
    response = client.get("/api/v0/status/health")
    assert response.status_code == 400
    assert "Unsupported API version" in response.json()["error"]

def test_migration_functionality():
    """Test schema migration functionality."""
    from app.utils.schema_migration import schema_migrator

    # Test v1 to v2 migration
    v1_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    }

    v2_data = schema_migrator.migrate_data(v1_data, "v1", "v2", "user_create")

    assert "phone_number" in v2_data
    assert "accept_terms" in v2_data
    assert v2_data["phone_number"] is None
    assert v2_data["accept_terms"] is False

def test_backward_compatibility():
    """Test backward compatibility."""
    from app.utils.schema_migration import schema_migrator

    # Test v2 to v1 migration
    v2_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123",
        "phone_number": "+1234567890",
        "accept_terms": True
    }

    v1_data = schema_migrator.migrate_data(v2_data, "v2", "v1", "user_create")

    assert "phone_number" not in v1_data
    assert "accept_terms" not in v1_data
    assert "email" in v1_data
    assert "full_name" in v1_data
```

### **Step 5.2: Create Integration Tests**

Create `backend/tests/test_version_integration.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v1_endpoints():
    """Test v1 endpoints work correctly."""
    # Test auth endpoints
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code in [200, 401]  # 401 if user doesn't exist

    # Test user endpoints
    response = client.get("/api/v1/users")
    assert response.status_code in [200, 401]

def test_v2_endpoints():
    """Test v2 endpoints work correctly."""
    # Test v2 auth endpoints
    response = client.post("/api/v2/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
        "remember_me": True,
        "device_id": "test-device"
    })
    assert response.status_code in [200, 401]

def test_version_specific_features():
    """Test version-specific features."""
    # Test v1 health check
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v1"

    # Test v2 health check
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v2"
    assert "metrics" in data
```

### **Step 5.3: Create Performance Tests**

Create `backend/tests/test_version_performance.py`:
```python
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_version_performance():
    """Test performance differences between versions."""
    # Test v1 performance
    start_time = time.time()
    response = client.get("/api/v1/status/health")
    v1_time = time.time() - start_time

    # Test v2 performance
    start_time = time.time()
    response = client.get("/api/v2/status/health")
    v2_time = time.time() - start_time

    # Ensure both versions are reasonably fast
    assert v1_time < 1.0  # Less than 1 second
    assert v2_time < 1.0  # Less than 1 second

    print(f"v1 response time: {v1_time:.3f}s")
    print(f"v2 response time: {v2_time:.3f}s")

def test_concurrent_requests():
    """Test handling of concurrent requests to different versions."""
    import threading
    import queue

    results = queue.Queue()

    def make_request(version):
        response = client.get(f"/api/{version}/status/health")
        results.put((version, response.status_code))

    # Start concurrent requests
    threads = []
    for version in ["v1", "v2"]:
        thread = threading.Thread(target=make_request, args=(version,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Check results
    while not results.empty():
        version, status_code = results.get()
        assert status_code == 200
```

---

## 🚀 Deployment Checklist

### **Pre-Deployment**

- [ ] **Code Review**
  - [ ] All versioning code reviewed
  - [ ] Migration functions tested
  - [ ] Documentation updated
  - [ ] Tests passing

- [ ] **Environment Setup**
  - [ ] Versioning environment variables configured
  - [ ] Database migrations ready
  - [ ] Monitoring tools configured
  - [ ] Backup strategy in place

- [ ] **Testing**
  - [ ] Unit tests passing
  - [ ] Integration tests passing
  - [ ] Performance tests within limits
  - [ ] Security tests passed

### **Deployment Steps**

1. **Backup Current System**
```bash
# Backup current main.py
cp backend/app/main.py backend/app/main_backup.py

# Backup database
pg_dump nova_law_db > backup_before_versioning.sql
```

2. **Deploy Versioning System**
```bash
# Copy new files
cp app/core/versioning.py backend/app/core/
cp app/middleware/versioning.py backend/app/middleware/
cp app/utils/schema_migration.py backend/app/utils/
cp app/monitoring/version_tracking.py backend/app/monitoring/

# Update main.py
cp app/main_updated.py backend/app/main.py
```

3. **Update Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Run Database Migrations**
```bash
alembic upgrade head
```

5. **Test Deployment**
```bash
# Start application
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/versions
curl http://localhost:8000/api/v1/status/health
curl http://localhost:8000/api/v2/status/health
```

### **Post-Deployment**

- [ ] **Monitoring**
  - [ ] Version usage tracking active
  - [ ] Error rates monitored
  - [ ] Performance metrics collected
  - [ ] Alerts configured

- [ ] **Documentation**
  - [ ] API documentation updated
  - [ ] Migration guides published
  - [ ] Team training completed
  - [ ] Client communication sent

- [ ] **Validation**
  - [ ] All v1 endpoints working
  - [ ] v2 endpoints accessible
  - [ ] Version headers present
  - [ ] Monitoring data flowing

---

## 🔧 Troubleshooting

### **Common Issues**

#### **Issue 1: Version Detection Not Working**
**Symptoms:** All requests show "unknown" version
**Solution:**
```python
# Check middleware order in main.py
app.add_middleware(VersionDetectionMiddleware)  # Must be first
app.add_middleware(VersionValidationMiddleware)
app.add_middleware(DeprecationWarningMiddleware)
```

#### **Issue 2: Migration Functions Not Found**
**Symptoms:** Migration errors in logs
**Solution:**
```python
# Ensure migration rules are registered
from app.utils.schema_migration import schema_migrator
schema_migrator._register_default_migrations()
```

#### **Issue 3: Version Headers Missing**
**Symptoms:** Response headers don't include version info
**Solution:**
```python
# Check middleware implementation
def _add_version_headers(self, response: Response, version: str):
    response.headers["X-API-Version"] = version
    # ... other headers
```

#### **Issue 4: Performance Degradation**
**Symptoms:** Slower response times after versioning
**Solution:**
```python
# Optimize middleware
# Add caching for version detection
# Use async operations where possible
```

### **Debugging Commands**

```bash
# Check version detection
curl -H "Accept: application/vnd.novalaw.v1+json" http://localhost:8000/api/v1/status/health

# Check version headers
curl -v http://localhost:8000/api/v1/status/health

# Test migration
python -c "
from app.utils.schema_migration import schema_migrator
data = {'email': 'test@example.com', 'full_name': 'Test'}
result = schema_migrator.migrate_data(data, 'v1', 'v2', 'user_create')
print(result)
"

# Check monitoring
curl http://localhost:8000/api/monitoring/usage
curl http://localhost:8000/api/monitoring/alerts
```

### **Log Analysis**

```bash
# Check for versioning errors
grep "version" logs/app.log

# Check migration errors
grep "migration" logs/app.log

# Check performance issues
grep "response_time" logs/app.log
```
<!--
---

## 📞 Support

### **Getting Help**

- **Documentation:** [Link to docs]
- **GitHub Issues:** [Link to issues]
- **Team Chat:** #api-versioning
- **Email:** api-support@novalaw.com

### **Emergency Contacts**

- **After Hours:** emergency@novalaw.com
- **Phone:** +1-555-API-HELP
- **Pager:** For critical issues only -->

---

**Implementation Guide Version:** 1.0
**Last Updated:** July 29, 2025
<!-- **Next Review:** March 2025   -->
**Owner:** Nova Law API Team
