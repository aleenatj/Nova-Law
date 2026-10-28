# Error Logging System

**Date:** July 29, 2024
**Status:** ✅ **SIMPLIFIED & UNIFIED**
**Purpose:** Single `log_error` function that automatically adapts to environment

---

## 🎯 **Overview**

The Nova Law AI Backend uses a **unified error logging system** that automatically adapts to the environment (local development or AWS Lambda) based on configuration. You only need to call **one function** - `log_error()`.

### **Key Features**
- ✅ **Single Function** - Only `log_error()` to remember
- ✅ **Environment Detection** - Automatically detects local vs Lambda
- ✅ **Automatic Context** - Adds Lambda context automatically in Lambda
- ✅ **Optional AWS** - Works without AWS dependencies in local development
- ✅ **Best Practice** - Clean, maintainable, and follows Python best practices

---

## 🚀 **Simple Usage**

```python
from app.core.error_logging import log_error, ErrorSeverity, ErrorCategory

# One function - works everywhere automatically
error_id = log_error(
    error=exception,
    severity=ErrorSeverity.HIGH,
    category=ErrorCategory.DATABASE
)
```

**That's it!** The system automatically:
- Detects if you're in local development or AWS Lambda
- Logs to console/file in local development
- Sends CloudWatch metrics in Lambda
- Adds Lambda context automatically
- Handles performance monitoring

---

## 🏗️ **System Architecture**

### **Core Components**

```
┌─────────────────────────────────────────────────────────────┐
│                app/core/error_logging.py                   │
├─────────────────────────────────────────────────────────────┤
│  ✅ Single log_error() function                           │
│  ✅ Environment detection                                  │
│  ✅ Automatic context extraction                           │
│  ✅ CloudWatch integration (Lambda only)                  │
│  ✅ Performance monitoring                                 │
│  ✅ Error tracking and statistics                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Environment                             │
├─────────────────────┬───────────────────────────────────────┤
│    Local/Dev        │           AWS Lambda                │
│                     │                                     │
│  ✅ Console Logging  │  ✅ CloudWatch Metrics             │
│  ✅ File Logging     │  ✅ Lambda Context                 │
│  ✅ Error Tracking   │  ✅ Performance Monitoring          │
│  ✅ Statistics       │  ✅ Cold Start Detection           │
└─────────────────────┴─────────────────────────────────────┘
```

### **Flow Diagram**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   log_error()   │───▶│ Environment     │
│   Code          │    │   Function      │    │ Detection       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Environment Branch                       │
├─────────────────────┬───────────────────────────────────────┤
│   Local Development │           AWS Lambda                 │
│                     │                                     │
│  ✅ Extract Context │  ✅ Extract Context                 │
│  ✅ Log to Console  │  ✅ Add Lambda Context              │
│  ✅ Log to File     │  ✅ Log to Console                  │
│  ✅ Update Stats    │  ✅ Send CloudWatch Metrics         │
│  ✅ Return Error ID │  ✅ Update Stats                    │
│                     │  ✅ Return Error ID                 │
└─────────────────────┴─────────────────────────────────────┘
```

---

## 📋 **Usage Examples**

### **1. Basic Error Logging**

```python
try:
    result = database.execute(query)
except Exception as e:
    error_id = log_error(e, ErrorSeverity.HIGH, ErrorCategory.DATABASE)
```

### **2. API Error with Request Context**

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = log_error(
        exc,
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.SYSTEM,
        request=request
    )
    return {"error_id": error_id, "message": "Internal server error"}
```

### **3. Database Error with Context**

```python
try:
    user = db.get_user(user_id)
except Exception as e:
    error_id = log_error(
        e,
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.DATABASE,
        performance_data={
            "operation": "get_user",
            "user_id": user_id,
            "duration_ms": 250.5
        }
    )
```

### **4. Lambda-Specific Error**

```python
# In Lambda handler
def lambda_handler(event, context):
    try:
        # Your Lambda logic
        pass
    except Exception as e:
        error_id = log_error(
            e,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            lambda_context=context  # Optional - auto-detected
        )
```

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# Lambda Configuration (optional)
AWS_LAMBDA_FUNCTION_NAME=nova-law-api
AWS_REGION=us-east-1

# CloudWatch Configuration (optional)
ENABLE_CLOUDWATCH_METRICS=true

# Error Monitoring
ENABLE_ERROR_MONITORING=true
ERROR_ALERT_THRESHOLD=5
```

### **Dependencies**

```txt
# Required for all environments
structlog==23.2.0
pydantic==2.5.0

# Optional for Lambda (only if available)
boto3==1.34.0
botocore==1.34.0
mangum==0.17.0
```

---

## 🎯 **Error Categories**

```python
class ErrorCategory(str, Enum):
    AUTHENTICATION = "authentication"    # Login/auth errors
    AUTHORIZATION = "authorization"      # Permission errors
    VALIDATION = "validation"           # Input validation errors
    DATABASE = "database"               # Database errors
    EXTERNAL_SERVICE = "external_service"       # Third-party API errors
    AI_AGENT = "ai_agent"              # AI agent errors
    RATE_LIMIT = "rate_limit"          # Rate limiting errors
    SYSTEM = "system"                   # System errors
    NETWORK = "network"                 # Network errors
    LAMBDA = "lambda"                   # Lambda-specific errors
    UNKNOWN = "unknown"                 # Unknown errors
```

---

## 📊 **Error Severity Levels**

```python
class ErrorSeverity(str, Enum):
    LOW = "low"           # Minor issues, warnings
    MEDIUM = "medium"     # Moderate issues
    HIGH = "high"         # Serious issues
    CRITICAL = "critical" # Critical system failures
```

---

## 🔄 **Environment Detection**

### **Local Development**
```python
# Environment variables not set
AWS_LAMBDA_FUNCTION_NAME = None

# Behavior
log_error(exception)
# ↓
# ✅ Console logging
# ✅ File logging
# ✅ Error tracking
# ✅ Performance monitoring
# ✅ No AWS dependencies
```

### **AWS Lambda**
```python
# Environment variables set
AWS_LAMBDA_FUNCTION_NAME = "nova-law-api"

# Behavior
log_error(exception)
# ↓
# ✅ Console logging
# ✅ CloudWatch metrics
# ✅ Lambda context
# ✅ Performance monitoring
# ✅ Cold start detection
# ✅ Memory usage tracking
```

---

## 📈 **Performance Monitoring**

### **Automatic Performance Tracking**

```python
# With performance data
log_error(
    exception,
    performance_data={
        "duration_ms": 1500,
        "memory_used_mb": 45.2,
        "operation": "database_query"
    }
)
```

### **Lambda Performance Metrics**

```python
from app.core.error_logging import log_performance_metrics

# Log performance metrics
log_performance_metrics(
    operation="api_request",
    duration_ms=250.5,
    memory_used_mb=45.2,
    additional_metrics={
        "request_count": 1,
        "response_status": 200
    }
)
```

### **Cold Start Detection**

```python
from app.core.error_logging import log_cold_start

# Log cold start
log_cold_start("nova-law-api", 1500.0)  # 1.5 seconds
```

---

## 🛠️ **Integration with Middleware**

### **Lambda Optimization Middleware**

The system includes Lambda-specific middleware that automatically integrates with the error logging:

```python
# app/middleware/lambda_optimization.py
from app.core.error_logging import log_error, log_performance_metrics

class LambdaPerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Automatic performance logging
            log_performance_metrics(
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration_ms
            )
            return response
        except Exception as e:
            # Automatic error logging
            log_error(e, request=request)
            raise
```

---

## 📊 **Error Statistics and Monitoring**

### **Get Error Statistics**

```python
from app.core.error_logging import get_error_statistics

# Get current error statistics
stats = get_error_statistics()
print(stats)
# Output:
# {
#     "total_errors": 15,
#     "error_types": {"DatabaseError": 8, "ValidationError": 7},
#     "severity_distribution": {"high": 10, "medium": 5},
#     "category_distribution": {"database": 8, "validation": 7},
#     "timestamp": "2024-07-29T10:30:00"
# }
```

### **Error Monitoring Endpoints**

The system provides monitoring endpoints for error tracking:

```python
# GET /api/monitoring/errors
# Returns error statistics and recent errors

# GET /api/monitoring/alerts/{alert_id}/resolve
# Resolves specific alerts
```

---

## 🔧 **Best Practices**

### **1. Use Appropriate Categories**

```python
# Database errors
log_error(e, category=ErrorCategory.DATABASE)

# Authentication errors
log_error(e, category=ErrorCategory.AUTHENTICATION)

# Validation errors
log_error(e, category=ErrorCategory.VALIDATION)
```

### **2. Set Correct Severity**

```python
# Minor issues
log_error(e, severity=ErrorSeverity.LOW)

# Serious issues
log_error(e, severity=ErrorSeverity.HIGH)

# Critical failures
log_error(e, severity=ErrorSeverity.CRITICAL)
```

### **3. Include Context**

```python
# With request context
log_error(e, request=request)

# With performance data
log_error(e, performance_data={"duration_ms": 1500})

# With custom context
context = ErrorContext(user_id="123", operation="get_user")
log_error(e, context=context)
```

### **4. Handle Lambda Context**

```python
# In Lambda handlers
def lambda_handler(event, context):
    try:
        # Your logic
        pass
    except Exception as e:
        # Lambda context is auto-detected, but you can pass it explicitly
        log_error(e, lambda_context=context)
```

---

## 🚀 **Deployment Considerations**

### **Local Development**

- No AWS dependencies required
- Works with standard Python logging
- Console and file logging
- Error tracking and statistics

### **AWS Lambda Deployment**

- Automatic CloudWatch integration
- Lambda context extraction
- Performance monitoring
- Cold start detection
- Memory usage tracking

### **Environment Variables**

```bash
# For Lambda deployment
AWS_LAMBDA_FUNCTION_NAME=nova-law-api
AWS_REGION=us-east-1
ENABLE_CLOUDWATCH_METRICS=true

# For local development
ENABLE_ERROR_MONITORING=true
ERROR_ALERT_THRESHOLD=5
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

1. **AWS Dependencies Not Available**
   - System works without AWS dependencies
   - Only CloudWatch metrics are disabled
   - Console logging still works

2. **Lambda Context Not Detected**
   - Check `AWS_LAMBDA_FUNCTION_NAME` environment variable
   - Pass `lambda_context` explicitly if needed

3. **Performance Metrics Not Sent**
   - Check `ENABLE_CLOUDWATCH_METRICS` environment variable
   - Verify AWS credentials and permissions

### **Debugging**

```python
from app.core.error_logging import is_lambda_environment

# Check environment
if is_lambda_environment():
    print("Running in Lambda environment")
else:
    print("Running in local environment")
```

---

## 📚 **Related Documentation**

- [AWS Lambda Deployment Guide](../guides/AWS_LAMBDA_DEPLOYMENT.md)
- [API Versioning Strategy](../guides/API_VERSIONING_STRATEGY.md)
- [Implementation Guide](../guides/IMPLEMENTATION_GUIDE.md)

---

## 🎉 **Summary**

The Nova Law AI Backend error logging system provides:

- ✅ **Single Function** - Only `log_error()` to remember
- ✅ **Environment Detection** - Automatically adapts to local/Lambda
- ✅ **Automatic Context** - Adds request and Lambda context
- ✅ **Performance Monitoring** - Built-in performance tracking
- ✅ **CloudWatch Integration** - Automatic in Lambda environment
- ✅ **Error Statistics** - Comprehensive error tracking
- ✅ **Best Practices** - Clean, maintainable code

**The system is designed to be simple, powerful, and environment-aware!** 🚀
