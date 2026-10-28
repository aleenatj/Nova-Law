# Schema Versioning Strategy

This document outlines the schema versioning strategy for the Nova Law AI Backend.

## 🎯 **Why Schema Versioning?**

### **Benefits:**
- **Backward Compatibility:** Support multiple API versions simultaneously
- **Gradual Migration:** Allow clients to migrate at their own pace
- **Breaking Changes:** Safely introduce new features
- **API Contract Stability:** Clear version history and changes

### **When to Version:**
- ✅ Adding/removing required fields
- ✅ Changing field types (string → int)
- ✅ Modifying validation rules
- ✅ Altering response structure
- ✅ Changing field names

## 🏗️ **Directory Structure**

```
app/schemas/
├── v1/                    # Version 1 schemas (current)
│   ├── __init__.py       # V1 schema exports
│   ├── base.py           # Base classes (EncryptedResponse)
│   ├── chat.py           # Chat-related schemas
│   ├── user.py           # User-related schemas
│   ├── auth.py           # Authentication schemas
│   └── agent.py          # Agent-related schemas
├── v2/                    # Version 2 schemas (future)
│   ├── __init__.py
│   ├── base.py
│   ├── chat.py
│   └── ...
└── __init__.py           # Main schema exports (latest version)
```

## 📋 **Versioning Rules**

### **1. Semantic Versioning**
- **Major Version (v1, v2):** Breaking changes
- **Minor Version (v1.1, v1.2):** Backward-compatible additions
- **Patch Version:** Bug fixes (no schema changes)

### **2. Breaking Changes**
- ❌ Removing required fields
- ❌ Changing field types
- ❌ Making optional fields required
- ❌ Changing field names
- ❌ Removing endpoints

### **3. Non-Breaking Changes**
- ✅ Adding optional fields
- ✅ Adding new endpoints
- ✅ Adding new validation rules
- ✅ Making required fields optional
- ✅ Adding new response fields

## 🔄 **Migration Strategy**

### **Phase 1: Create New Version**
```python
# app/schemas/v2/chat.py
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    # NEW: priority field
    priority: str = Field("normal", description="Message priority")
```

### **Phase 2: Support Both Versions**
```python
# app/api/v2/chat.py
@router.post("/chat/send", response_model=ChatResponse)
async def send_message_v2(chat_request: ChatRequestV2):
    # Handle new priority field
    pass

# app/api/v1/chat.py (keep existing)
@router.post("/chat/send", response_model=ChatResponse)
async def send_message_v1(chat_request: ChatRequestV1):
    # Handle legacy format
    pass
```

### **Phase 3: Deprecation Notice**
```python
# Add deprecation headers
@router.post("/chat/send", response_model=ChatResponse)
async def send_message_v1(chat_request: ChatRequestV1):
    # Add deprecation header
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2024-12-31"
    return response
```

### **Phase 4: Remove Old Version**
- After sufficient migration period
- Update documentation
- Notify all clients

## 📝 **Implementation Examples**

### **Example 1: Adding a Field**
```python
# v1/chat.py
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

# v2/chat.py
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    priority: str = "normal"  # NEW FIELD
```

### **Example 2: Changing Field Type**
```python
# v1/user.py
class UserResponse(BaseModel):
    id: str
    age: str  # String format

# v2/user.py
class UserResponse(BaseModel):
    id: str
    age: int  # Integer format
```

### **Example 3: Removing a Field**
```python
# v1/chat.py
class ChatResponse(BaseModel):
    session_id: str
    user_message: MessageResponse
    ai_response: MessageResponse
    debug_info: dict  # TO BE REMOVED

# v2/chat.py
class ChatResponse(BaseModel):
    session_id: str
    user_message: MessageResponse
    ai_response: MessageResponse
    # debug_info removed
```

## 🛠️ **Best Practices**

### **1. Documentation**
- Document all changes between versions
- Provide migration guides
- Include examples for each version

### **2. Testing**
- Test both versions simultaneously
- Ensure backward compatibility
- Validate migration paths

### **3. Monitoring**
- Track API version usage
- Monitor for deprecated version usage
- Alert on breaking changes

### **4. Communication**
- Notify clients of upcoming changes
- Provide migration timelines
- Offer support during migration

## 📊 **Version Lifecycle**

```
v1 (Current) → v2 (Development) → v2 (Beta) → v2 (Stable) → v1 (Deprecated) → v1 (Removed)
     ↓              ↓                ↓           ↓              ↓              ↓
   Production   Development      Testing     Production    Deprecation    Removal
```

## 🔧 **Tools and Utilities**

### **Schema Validation**
```python
# Validate schema compatibility
def validate_schema_compatibility(v1_schema, v2_schema):
    """Check if v2 is backward compatible with v1."""
    pass
```

### **Migration Helpers**
```python
# Convert between versions
def convert_v1_to_v2(v1_data: dict) -> dict:
    """Convert v1 data to v2 format."""
    pass

def convert_v2_to_v1(v2_data: dict) -> dict:
    """Convert v2 data to v1 format."""
    pass
```

### **Version Detection**
```python
# Auto-detect client version
def detect_api_version(request: Request) -> str:
    """Detect API version from request headers or URL."""
    pass
```

## 📈 **Metrics and Monitoring**

### **Key Metrics:**
- API version usage distribution
- Migration progress
- Error rates by version
- Performance by version

### **Alerts:**
- High usage of deprecated versions
- Breaking change errors
- Migration failures

## 🎯 **Next Steps**

1. **Implement v1 schemas** (current)
2. **Set up versioning infrastructure**
3. **Create migration utilities**
4. **Establish deprecation policies**
5. **Monitor and iterate**

---

**Remember:** Schema versioning is about maintaining API stability while enabling evolution. Always prioritize backward compatibility and provide clear migration paths.
