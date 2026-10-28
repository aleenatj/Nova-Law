# Nova Law API Versioning Management Guide

**Document Version:** 1.0
**Date:** July 29, 2025
**Project:** Nova Law AI Backend
<!-- **Status:** Production Ready   -->

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [How Versioning is Implemented](#how-versioning-is-implemented)
3. [Managing New Versions](#managing-new-versions)
4. [Version Lifecycle Management](#version-lifecycle-management)
5. [Migration Examples](#migration-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide explains how API versioning is implemented in the Nova Law backend and provides step-by-step instructions for managing new versions. The system uses **URI-based versioning** with optional header support for maximum flexibility.

### **Key Principles**
- ✅ **Backward Compatibility:** Old versions continue to work
- ✅ **Gradual Migration:** Clients can migrate at their own pace
- ✅ **Clear Communication:** Deprecation notices and migration guides
- ✅ **Automated Detection:** Version detection from URLs and headers
- ✅ **Monitoring:** Track usage and migration progress

---

## 🏗️ How Versioning is Implemented

### **1. Core Architecture**

The versioning system consists of four main components:

#### **A. Version Manager (`app/core/versioning.py`)**
```python
# Centralized version management
class VersionManager:
    def __init__(self):
        self.supported_versions: list[APIVersion] = [APIVersion.V1]
        self.default_version: APIVersion = APIVersion.V1
        self.deprecated_versions: list[APIVersion] = []
        self.deprecation_schedule: dict[str, datetime] = {}
```

**Responsibilities:**
- Track supported and deprecated versions
- Manage version lifecycle dates
- Provide version information

#### **B. Version Detector (`app/core/versioning.py`)**
```python
class VersionDetector:
    def detect_version(self, request: Request) -> str:
        # 1. Check URL path: /api/v1/users
        # 2. Check Accept header: application/vnd.nova.v1+json
        # 3. Check X-API-Version header: v1
        # 4. Return default version if none found
```

**Responsibilities:**
- Detect API version from multiple sources
- Provide fallback to default version
- Support multiple detection methods

#### **C. Versioning Middleware (`app/middleware/versioning.py`)**
```python
class VersionDetectionMiddleware:
    async def __call__(self, request: Request, call_next):
        # Detect version and add to request state
        version = self.detector.detect_version(request)
        request.state.api_version = version

        # Add version headers to response
        response.headers["X-API-Version"] = version
        return response
```

**Responsibilities:**
- Automatically detect version for each request
- Add version information to response headers
- Handle deprecation warnings

#### **D. Version Tracking (`app/monitoring/version_tracking.py`)**
```python
class VersionUsageTracker:
    def track_request(self, version: str, endpoint: str):
        # Track usage statistics
        # Monitor migration progress
        # Generate alerts for deprecated versions
```

**Responsibilities:**
- Track API version usage
- Monitor migration progress
- Generate alerts and reports

### **2. Directory Structure**

```
app/
├── api/
│   ├── v1/                    # Current stable version
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── users.py          # User management
│   │   ├── agents.py         # Agent management
│   │   └── status.py         # System status
│   ├── v2/                    # New version (when needed)
│   │   ├── auth.py           # Updated authentication
│   │   ├── users.py          # Updated user management
│   │   └── ...
│   └── __init__.py
├── schemas/
│   ├── v1/                    # Current schemas
│   │   ├── auth.py           # Authentication schemas
│   │   ├── users.py          # User schemas
│   │   └── ...
│   ├── v2/                    # New schemas (when needed)
│   │   ├── auth.py           # Updated schemas
│   │   └── ...
│   └── __init__.py
├── core/
│   ├── versioning.py          # Core versioning logic
│   └── ...
├── middleware/
│   ├── versioning.py          # Version detection middleware
│   └── ...
└── monitoring/
    ├── version_tracking.py    # Usage tracking
    └── ...
```

### **3. Version Detection Methods**

The system supports multiple ways to specify API version:

#### **A. URL Path (Primary Method)**
```bash
# Version 1
GET /api/v1/users
POST /api/v1/auth/login

# Version 2 (when available)
GET /api/v2/users
POST /api/v2/auth/login
```

#### **B. Accept Header**
```bash
# Version 1
Accept: application/vnd.nova.v1+json

# Version 2
Accept: application/vnd.nova.v2+json
```

#### **C. Custom Header**
```bash
# Version 1
X-API-Version: v1

# Version 2
X-API-Version: v2
```

#### **D. Default Fallback**
If no version is specified, the system defaults to the current stable version.

---

## 🔄 Managing New Versions

### **Step 1: Plan the New Version**

#### **A. Identify Changes**
```python
# Example: Adding a new field to user registration
# V1: Basic user registration
class UserCreateV1(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

# V2: Enhanced user registration with phone
class UserCreateV2(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str  # NEW FIELD
    marketing_consent: bool = False  # NEW FIELD
```

#### **B. Determine Version Type**
- **Major Version (v1 → v2):** Breaking changes
- **Minor Version (v1.1):** Backward-compatible additions
- **Patch Version:** Bug fixes (no schema changes)

### **Step 2: Create New Version Structure**

#### **A. Create API Directory**
```bash
mkdir app/api/v2
touch app/api/v2/__init__.py
```

#### **B. Create Schema Directory**
```bash
mkdir app/schemas/v2
touch app/schemas/v2/__init__.py
```

#### **C. Copy and Modify Files**
```bash
# Copy existing files
cp app/api/v1/auth.py app/api/v2/auth.py
cp app/schemas/v1/auth.py app/schemas/v2/auth.py

# Modify for new version
# Update schemas, endpoints, validation rules
```

### **Step 3: Update Version Manager**

#### **A. Add New Version to Enum**
```python
# app/core/versioning.py
class APIVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"  # ADD NEW VERSION
```

#### **B. Register New Version**
```python
# In your application startup
version_manager = VersionManager()
version_manager.add_version(
    version=APIVersion.V2,
    release_date=datetime(2024, 8, 1)
)
```

### **Step 4: Update Main Application**

#### **A. Include New Router**
```python
# app/main.py
from app.api.v2 import auth as auth_v2, users as users_v2

# Include new version routers
app.include_router(auth_v2.router, prefix="/api/v2", tags=["v2"])
app.include_router(users_v2.router, prefix="/api/v2", tags=["v2"])
```

#### **B. Update Version Configuration**
```python
# app/core/versioning.py
def __init__(self):
    self.supported_versions: list[APIVersion] = [APIVersion.V1, APIVersion.V2]
    self.default_version: APIVersion = APIVersion.V1  # Keep v1 as default
```

### **Step 5: Implement Migration Logic**

#### **A. Add Migration Helper**
```python
# app/core/versioning.py
class MigrationHelper:
    @staticmethod
    def migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        """Migrate data from v1 to v2 format."""
        migrated_data = data.copy()

        # Add default values for new fields
        if "phone" not in migrated_data:
            migrated_data["phone"] = ""
        if "marketing_consent" not in migrated_data:
            migrated_data["marketing_consent"] = False

        return migrated_data
```

#### **B. Use in Endpoints**
```python
# app/api/v2/auth.py
@router.post("/register", response_model=UserResponseV2)
async def register_v2(user_data: UserCreateV2):
    # Handle v2 registration with new fields
    return await create_user_v2(user_data)

# app/api/v1/auth.py (keep for backward compatibility)
@router.post("/register", response_model=UserResponseV1)
async def register_v1(user_data: UserCreateV1):
    # Handle v1 registration (legacy)
    return await create_user_v1(user_data)
```

### **Step 6: Test Both Versions**

#### **A. Test V1 (Backward Compatibility)**
```bash
# Test existing v1 endpoints
curl -X POST /api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password", "first_name": "John", "last_name": "Doe"}'
```

#### **B. Test V2 (New Features)**
```bash
# Test new v2 endpoints
curl -X POST /api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password", "first_name": "John", "last_name": "Doe", "phone": "+1234567890", "marketing_consent": true}'
```

---

## 📅 Version Lifecycle Management

### **1. Version States**

```python
# Version lifecycle states
SUPPORTED = "supported"      # Active and maintained
DEPRECATED = "deprecated"    # Still works, but not recommended
END_OF_LIFE = "end_of_life" # No longer supported
```

### **2. Lifecycle Timeline**

```python
# Example timeline for v1 → v2 transition
version_lifecycle = {
    "v1": {
        "release_date": datetime(2024, 1, 1),
        "deprecation_date": datetime(2024, 8, 1),  # When v2 is released
        "end_of_life": datetime(2025, 1, 1),       # When v1 is removed
    },
    "v2": {
        "release_date": datetime(2024, 8, 1),
        "deprecation_date": None,  # Not deprecated yet
        "end_of_life": None,       # Not EOL yet
    }
}
```

### **3. Deprecation Process**

#### **A. Mark Version as Deprecated**
```python
# In your application
version_manager.deprecate_version(
    version=APIVersion.V1,
    deprecation_date=datetime(2024, 8, 1),
    end_of_life=datetime(2025, 1, 1)
)
```

#### **B. Add Deprecation Headers**
```python
# Middleware automatically adds headers
response.headers["Deprecation"] = "true"
response.headers["Sunset"] = "2025-01-01"
response.headers["Link"] = '</api/v2>; rel="successor-version"'
```

#### **C. Monitor Usage**
```python
# Track deprecated version usage
class VersionUsageTracker:
    def track_deprecated_usage(self, version: str, endpoint: str):
        # Log warning
        # Send alert if usage is high
        # Track migration progress
```

### **4. End-of-Life Process**

#### **A. Remove Deprecated Version**
```python
# After end-of-life date
# 1. Remove from supported_versions
# 2. Remove router includes
# 3. Remove schema files
# 4. Update documentation
```

#### **B. Update Default Version**
```python
# When v1 is EOL, make v2 the default
version_manager.default_version = APIVersion.V2
```

---

## 🔄 Migration Examples

### **Example 1: Adding New Fields**

#### **Scenario:** Add phone number to user registration

#### **V1 Schema:**
```python
# app/schemas/v1/auth.py
class UserCreateV1(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
```

#### **V2 Schema:**
```python
# app/schemas/v2/auth.py
class UserCreateV2(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str  # NEW FIELD
```

#### **Migration Logic:**
```python
# app/core/versioning.py
@staticmethod
def migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    migrated = data.copy()
    if "phone" not in migrated:
        migrated["phone"] = ""  # Default value
    return migrated
```

### **Example 2: Changing Field Types**

#### **Scenario:** Change user ID from string to UUID

#### **V1 Schema:**
```python
# app/schemas/v1/users.py
class UserResponseV1(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
```

#### **V2 Schema:**
```python
# app/schemas/v2/users.py
from uuid import UUID

class UserResponseV2(BaseModel):
    id: UUID  # CHANGED TYPE
    email: str
    first_name: str
    last_name: str
```

#### **Migration Logic:**
```python
# app/core/versioning.py
@staticmethod
def migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    migrated = data.copy()
    # Convert string ID to UUID if needed
    if "id" in migrated and isinstance(migrated["id"], str):
        migrated["id"] = UUID(migrated["id"])
    return migrated
```

### **Example 3: Removing Fields**

#### **Scenario:** Remove deprecated field from response

#### **V1 Schema:**
```python
# app/schemas/v1/users.py
class UserResponseV1(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    deprecated_field: str  # TO BE REMOVED
```

#### **V2 Schema:**
```python
# app/schemas/v2/users.py
class UserResponseV2(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    # deprecated_field removed
```

#### **Migration Logic:**
```python
# app/core/versioning.py
@staticmethod
def migrate_v2_to_v1(data: dict[str, Any]) -> dict[str, Any]:
    migrated = data.copy()
    # Add deprecated field for v1 compatibility
    migrated["deprecated_field"] = "legacy_value"
    return migrated
```

---

## ✅ Best Practices

### **1. Versioning Rules**

#### **✅ Do's:**
- Use semantic versioning (v1, v2, v3)
- Maintain backward compatibility
- Provide clear migration guides
- Monitor version usage
- Give sufficient deprecation notice

#### **❌ Don'ts:**
- Don't break existing functionality
- Don't remove versions without notice
- Don't skip testing both versions
- Don't forget to update documentation

### **2. Migration Strategy**

#### **A. Gradual Migration**
```python
# Phase 1: Release new version alongside old
# Phase 2: Encourage migration with deprecation notices
# Phase 3: Monitor usage and migration progress
# Phase 4: Remove old version after sufficient migration
```

#### **B. Communication Plan**
```python
# 1. Announce new version release
# 2. Provide migration documentation
# 3. Send deprecation notices
# 4. Monitor and support migration
# 5. Remove deprecated version
```

### **3. Testing Strategy**

#### **A. Test Both Versions**
```python
# Test v1 endpoints (backward compatibility)
def test_v1_user_registration():
    response = client.post("/api/v1/auth/register", json=v1_data)
    assert response.status_code == 200

# Test v2 endpoints (new features)
def test_v2_user_registration():
    response = client.post("/api/v2/auth/register", json=v2_data)
    assert response.status_code == 200
```

#### **B. Test Migration Logic**
```python
def test_v1_to_v2_migration():
    v1_data = {"email": "user@example.com", "password": "pass"}
    v2_data = MigrationHelper.migrate_v1_to_v2(v1_data)
    assert "phone" in v2_data
    assert v2_data["phone"] == ""
```

### **4. Monitoring and Alerts**

#### **A. Usage Tracking**
```python
# Track version usage
class VersionUsageTracker:
    def track_request(self, version: str, endpoint: str):
        # Log usage statistics
        # Monitor migration progress
        # Generate alerts for deprecated versions
```

#### **B. Migration Progress**
```python
# Monitor migration from v1 to v2
def get_migration_progress():
    v1_usage = get_version_usage("v1")
    v2_usage = get_version_usage("v2")
    total_usage = v1_usage + v2_usage
    return (v2_usage / total_usage) * 100
```

---

## 🔧 Troubleshooting

### **1. Common Issues**

#### **A. Version Not Detected**
```python
# Check version detection order
# 1. URL path: /api/v1/users
# 2. Accept header: application/vnd.nova.v1+json
# 3. Custom header: X-API-Version: v1
# 4. Default version
```

#### **B. Migration Errors**
```python
# Check migration logic
def debug_migration(data: dict[str, Any], from_version: str, to_version: str):
    try:
        migrated = MigrationHelper.migrate_data(data, from_version, to_version)
        return migrated
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return data  # Return original data on error
```

#### **C. Deprecation Warnings**
```python
# Check deprecation configuration
def check_deprecation_status(version: str):
    if version_manager.is_deprecated(version):
        info = version_manager.get_deprecation_info(version)
        logger.warning(f"Using deprecated version {version}: {info}")
```

### **2. Debugging Tools**

#### **A. Version Information Endpoint**
```bash
# Get current version information
curl /api/versions

# Response:
{
  "supported_versions": ["v1", "v2"],
  "deprecated_versions": [],
  "latest_version": "v2",
  "default_version": "v1"
}
```

#### **B. Version Usage Statistics**
```bash
# Get usage statistics
curl /api/monitoring/versions/usage

# Response:
{
  "v1": {"requests": 1000, "percentage": 60},
  "v2": {"requests": 667, "percentage": 40}
}
```

#### **C. Migration Progress**
```bash
# Get migration progress
curl /api/monitoring/versions/migration

# Response:
{
  "from_version": "v1",
  "to_version": "v2",
  "progress_percentage": 40,
  "estimated_completion": "2024-12-01"
}
```

---

## 📚 Additional Resources

### **1. Related Documentation**
- [Schema Versioning](./SCHEMA_VERSIONING.md) - Schema-specific versioning
- [Error Logging System](./ERROR_LOGGING_SYSTEM.md) - Logging and monitoring

### **2. Code Examples**
- [Quick Reference](./VERSIONING_QUICK_REFERENCE.md) - Quick commands and examples

### **3. Monitoring Endpoints**
- `GET /api/versions` - Version information
- `GET /api/versions/{version}/info` - Specific version details
- `GET /api/monitoring/versions/usage` - Usage statistics
- `GET /api/monitoring/versions/migration` - Migration progress

---

**This guide provides everything needed to understand and manage API versioning in the Nova Law backend. For questions or clarifications, refer to the troubleshooting section or contact the development team.**
