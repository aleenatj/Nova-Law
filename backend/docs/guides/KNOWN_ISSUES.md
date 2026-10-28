# Known Issues

This document tracks known issues in the Nova Law AI Backend and their resolution status.

## Pydantic V1/V2 Mixing Warning

**Status:** 🔄 In Progress (Third-party dependency issue)

**Issue:**
```
UserWarning: Mixing V1 models and V2 models (or constructs, like `TypeAdapter`) is not supported. Please upgrade `BaseMessage` to V2.
```

**Root Cause:**
- `langchain_core.messages.BaseMessage` uses Pydantic V1
- Our application uses Pydantic V2
- This creates a compatibility warning when both are used together

**Impact:**
- ⚠️ Warning message during startup
- ✅ No functional impact on application
- ✅ All features work correctly

**Resolution Plan:**
1. **Short-term:** Warning suppression with clear documentation (current)
2. **Long-term:** Wait for LangChain to migrate BaseMessage to Pydantic V2
3. **Alternative:** Consider using custom message types if needed

**Tracking:**
- LangChain Issue: [Pydantic V2 Migration](https://github.com/langchain-ai/langchain/issues/related-to-pydantic-v2)
- Our Code: `backend/app/main.py` (warning suppression)

**Why We Suppress This Warning:**
- ✅ It's a third-party library issue we cannot fix
- ✅ No functional impact on our application
- ✅ Clear documentation and tracking for future resolution
- ✅ Will be removed when LangChain updates

## Best Practices for Warning Suppression

### ✅ When to Suppress:
- Third-party library warnings you cannot control
- Known issues being addressed upstream
- Temporary workarounds with clear TODO comments
- Performance-critical code where warning is unavoidable

### ❌ When NOT to Suppress:
- Your own code warnings
- Warnings indicating real bugs
- Warnings that could become errors in future versions
- Warnings without clear documentation

### 📝 Documentation Requirements:
- Clear explanation of why suppression is needed
- Link to upstream issue tracking
- Plan for removing suppression
- Impact assessment

## Future Improvements

1. **Monitor LangChain Updates:** Check for Pydantic V2 migration
2. **Alternative Message Types:** Consider custom message implementations
3. **Dependency Updates:** Keep dependencies updated for fixes
4. **Testing:** Ensure no regressions when warnings are removed
