# Python/FastAPI Coding Standards Reference Guide

## Table of Contents

1. [Overview](#overview)
2. [Naming Conventions](#naming-conventions)
3. [Function Definitions](#function-definitions)
4. [Variable Declarations](#variable-declarations)
5. [Type Hints](#type-hints)
6. [Code Formatting](#code-formatting)
7. [Pre-commit Hooks](#pre-commit-hooks)
8. [Tools Configuration](#tools-configuration)
9. [Examples](#examples)
10. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Overview

This document defines the coding standards and validation rules for the Nova Law AI FastAPI project. All code must follow these standards to pass pre-commit hooks and maintain code quality.

### **Tools Used:**
- **Ruff** - Fastest Python linter (replaces flake8, isort, pyupgrade)
- **Black** - Uncompromising code formatter
- **MyPy** - Static type checker
- **Bandit** - Security linter
- **Pre-commit** - Git hooks framework
- **Poetry** - Dependency management and packaging tool

---

## Naming Conventions

### **1. Variable Names**

#### ✅ **Correct Examples:**
```python
# Snake case for variables
user_id: str = "123"
chat_session: ChatSession = ChatSession()
is_active: bool = True
has_permission: bool = False
can_edit: bool = True
should_validate: bool = True
max_retry_attempts: int = 3
api_version: str = "v1"
database_connection: Session = db
error_message: str = "User not found"
```

#### ❌ **Incorrect Examples:**
```python
# Camel case (wrong)
userId: str = "123"
chatSession: ChatSession = ChatSession()
isActive: bool = True

# Pascal case (wrong for variables)
UserID: str = "123"
ChatSession: ChatSession = ChatSession()

# Single letters (except in loops)
a: str = "value"
b: int = 10
```

### **2. Function Names**

#### ✅ **Correct Examples:**
```python
# Snake case for functions
def create_user(db: Session, user_data: UserCreate) -> User:
    pass

def get_user_by_email(email: str) -> User | None:
    pass

def update_user_password(user_id: str, new_password: str) -> bool:
    pass

def validate_user_input(user_data: UserCreate) -> bool:
    pass

def is_user_authenticated(user: User) -> bool:
    pass

def has_admin_permission(user: User) -> bool:
    pass

def can_access_chat(user: User, chat: ChatSession) -> bool:
    pass
```

#### ❌ **Incorrect Examples:**
```python
# Camel case (wrong)
def createUser(db: Session, userData: UserCreate) -> User:
    pass

# Pascal case (wrong for functions)
def CreateUser(db: Session, user_data: UserCreate) -> User:
    pass

# Abbreviations (unless very common)
def getUsrByEmail(email: str) -> User | None:
    pass

def updUsrPwd(user_id: str, new_pwd: str) -> bool:
    pass
```

### **3. Class Names**

#### ✅ **Correct Examples:**
```python
# Pascal case for classes
class UserRepository:
    pass

class ChatSessionService:
    pass

class MessageValidator:
    pass

class DatabaseConnection:
    pass

class AuthenticationManager:
    pass
```

#### ❌ **Incorrect Examples:**
```python
# Snake case (wrong for classes)
class user_repository:
    pass

# Camel case (wrong for classes)
class userRepository:
    pass

# All lowercase (wrong)
class userrepository:
    pass
```

### **4. Constants**

#### ✅ **Correct Examples:**
```python
# Upper snake case for constants
MAX_RETRY_ATTEMPTS: int = 3
DEFAULT_API_VERSION: str = "v1"
DATABASE_URL: str = "postgresql://..."
JWT_SECRET_KEY: str = "secret"
ALLOWED_FILE_TYPES: list[str] = ["pdf", "doc", "txt"]
SUPPORTED_LANGUAGES: list[str] = ["en", "es", "fr"]
```

#### ❌ **Incorrect Examples:**
```python
# Lower case (wrong for constants)
max_retry_attempts: int = 3
default_api_version: str = "v1"

# Camel case (wrong for constants)
maxRetryAttempts: int = 3
defaultApiVersion: str = "v1"
```

### **5. Private and Protected Methods**

#### ✅ **Correct Examples:**
```python
class UserService:
    def _validate_password(self, password: str) -> bool:
        """Private method - single underscore."""
        pass

    def _internal_helper(self, data: dict) -> dict:
        """Private method - single underscore."""
        pass

    def __secret_method(self) -> None:
        """Very private method - double underscore."""
        pass
```

#### ❌ **Incorrect Examples:**
```python
class UserService:
    def validatePassword(self, password: str) -> bool:
        """Wrong - camel case for private method."""
        pass

    def validate_password(self, password: str) -> bool:
        """Wrong - should be private with underscore."""
        pass
```

---

## Function Definitions

### **1. Parameter Order**

#### ✅ **Correct Order:**
1. **Required positional parameters**
2. **Optional positional parameters**
3. **Required keyword parameters**
4. **Optional keyword parameters**

```python
# ✅ Good
def create_user(
    db: Session,                    # Required positional
    user_data: UserCreate,          # Required positional
    *,
    validate_email: bool = True,    # Optional keyword
    send_welcome_email: bool = True # Optional keyword
) -> User:
    pass

# ✅ Good
def update_user(
    db: Session,
    user_id: str,
    user_data: UserUpdate,
    *,
    validate_changes: bool = True
) -> User | None:
    pass
```

#### ❌ **Incorrect Order:**
```python
# ❌ Bad - wrong parameter order
def create_user(
    validate_email: bool = True,
    db: Session,
    user_data: UserCreate
) -> User:
    pass

# ❌ Bad - mixing required and optional
def update_user(
    db: Session,
    user_data: UserUpdate,
    user_id: str,
    validate_changes: bool = True
) -> User | None:
    pass
```

### **2. Maximum Parameters**

#### ✅ **Good (7 or fewer parameters):**
```python
def create_user(
    db: Session,
    user_data: UserCreate,
    *,
    validate_email: bool = True,
    send_welcome_email: bool = True,
    create_profile: bool = True,
    assign_default_role: bool = True
) -> User:
    pass
```

#### ❌ **Bad (too many parameters):**
```python
def create_user(
    db: Session,
    user_data: UserCreate,
    validate_email: bool,
    send_welcome_email: bool,
    create_profile: bool,
    assign_default_role: bool,
    set_permissions: bool,
    create_workspace: bool,
    send_notification: bool,
    log_activity: bool
) -> User:
    pass
```

### **3. Function Documentation**

#### ✅ **Good Documentation:**
```python
def create_user(
    db: Session,
    user_data: UserCreate,
    *,
    validate_email: bool = True
) -> User:
    """
    Create a new user in the system.

    Args:
        db: Database session
        user_data: User creation data
        validate_email: Whether to validate email format

    Returns:
        Created user instance

    Raises:
        ValueError: If email is invalid or user already exists
        HTTPException: If database operation fails
    """
    pass
```

#### ❌ **Bad Documentation:**
```python
def create_user(db, user_data, validate_email=True):
    """Creates user."""
    pass

def create_user(db, user_data, validate_email=True):
    """
    Creates user.
    @param db database
    @param user_data data
    @return user
    """
    pass
```

---

## Variable Declarations

### **1. Type Hints for All Variables**

#### ✅ **Good:**
```python
# Explicit type hints
user_id: str = "123"
is_active: bool = True
user_list: list[User] = []
user_dict: dict[str, User] = {}
config: dict[str, Any] = {}
api_response: dict[str, Any] = {"status": "success"}
error_count: int = 0
max_attempts: int = 3
timeout_seconds: float = 30.5
```

#### ❌ **Bad:**
```python
# No type hints
user_id = "123"
is_active = True
user_list = []
user_dict = {}
config = {}
```

### **2. Boolean Variable Naming**

#### ✅ **Good Boolean Names:**
```python
is_active: bool = True
has_permission: bool = False
can_edit: bool = True
should_validate: bool = True
will_send_email: bool = False
needs_approval: bool = True
is_authenticated: bool = False
has_subscription: bool = True
```

#### ❌ **Bad Boolean Names:**
```python
active: bool = True
permission: bool = False
edit: bool = True
validate: bool = True
email: bool = False
approval: bool = True
```

### **3. List and Dictionary Declarations**

#### ✅ **Good:**
```python
# Empty collections with type hints
user_list: list[User] = []
user_dict: dict[str, User] = {}
config: dict[str, Any] = {}

# Pre-populated collections
allowed_roles: list[str] = ["admin", "user", "guest"]
api_versions: list[str] = ["v1", "v2"]
user_permissions: dict[str, list[str]] = {
    "admin": ["read", "write", "delete"],
    "user": ["read", "write"]
}
```

#### ❌ **Bad:**
```python
# No type hints
user_list = []
user_dict = {}
config = {}

# Wrong naming
users = []
usersDict = {}
userConfig = {}
```

---

## Type Hints

### **1. Function Parameter Type Hints**

#### ✅ **Good:**
```python
def get_user_by_id(
    db: Session,
    user_id: str
) -> User | None:
    pass

def create_user(
    db: Session,
    user_data: UserCreate,
    *,
    validate_email: bool = True
) -> User:
    pass

def update_user(
    db: Session,
    user_id: str,
    user_data: UserUpdate
) -> User | None:
    pass
```

#### ❌ **Bad:**
```python
def get_user_by_id(db, user_id):
    pass

def create_user(db, user_data, validate_email=True):
    pass

def update_user(db, user_id, user_data):
    pass
```

### **2. Variable Type Hints**

#### ✅ **Good:**
```python
# Basic types
user_id: str = "123"
age: int = 25
height: float = 175.5
is_active: bool = True

# Complex types
user_list: list[User] = []
user_dict: dict[str, User] = {}
config: dict[str, Any] = {}
api_response: dict[str, Any] = {"status": "success"}

# Optional types
user: User | None = None
email: str | None = None
age: int | None = None

# Union types
user_id: str | int = "123"
status: str | int = "active"
```

#### ❌ **Bad:**
```python
# No type hints
user_id = "123"
age = 25
user_list = []
user_dict = {}

# Wrong syntax
user: User or None = None
email: str or None = None
```

### **3. Generic Type Hints**

#### ✅ **Good:**
```python
from typing import TypeVar, Generic, List, Dict, Any

T = TypeVar('T')

class Repository(Generic[T]):
    def get_by_id(self, id: str) -> T | None:
        pass

    def get_all(self) -> List[T]:
        pass

    def create(self, data: Dict[str, Any]) -> T:
        pass
```

---

## Code Formatting

### **1. Line Length and Indentation**

#### ✅ **Good:**
```python
# 88 characters max line length
def create_user_with_comprehensive_validation(
    db: Session,
    user_data: UserCreate,
    *,
    validate_email: bool = True,
    send_welcome_email: bool = True,
    create_default_profile: bool = True
) -> User:
    """Create user with comprehensive validation."""
    pass

# Proper indentation (4 spaces)
if user.is_active:
    if user.has_permission("admin"):
        return user
    else:
        return None
```

#### ❌ **Bad:**
```python
# Too long lines
def create_user_with_comprehensive_validation_and_email_validation_and_profile_creation(db: Session, user_data: UserCreate, validate_email: bool = True, send_welcome_email: bool = True, create_default_profile: bool = True) -> User:
    pass

# Wrong indentation
if user.is_active:
  if user.has_permission("admin"):
      return user
  else:
      return None
```

### **2. Import Organization**

#### ✅ **Good:**
```python
# Standard library imports
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Local imports
from app.db.database import get_db
from app.schemas.v1.user import UserCreate, UserResponse
from app.services.user_service import UserService
```

#### ❌ **Bad:**
```python
# Mixed imports
from fastapi import APIRouter
import os
from app.db.database import get_db
from typing import List
from sqlalchemy.orm import Session
import sys
```

### **3. String Quotes**

#### ✅ **Good:**
```python
# Double quotes for all strings (consistent)
message = "User created successfully"
status = "active"

# Double quotes for docstrings
def create_user():
    """Create a new user in the system."""
    message = "User 'admin' created successfully"
    return message
```

#### ❌ **Bad:**
```python
# Inconsistent quotes
message = "User created successfully"
status = 'active'
```

---

## Pre-commit Hooks

### **1. Configuration**

The project uses the following pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  # Pre-commit hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: check-docstring-first
      - id: check-json
      - id: check-toml
      - id: debug-statements
      - id: requirements-txt-fixer

  # Black for formatting
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black

  # Ruff for linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix, --unsafe-fixes]
      - id: ruff-format

  # MyPy for type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy

  # Bandit for security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.6
    hooks:
      - id: bandit
        args: [-r, -f, json, -o, bandit-report.json]
```

### **2. Running Pre-commit Hooks**

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files
pre-commit run --all-files

# Run against specific files
pre-commit run --files app/api/v1/users.py

# Run specific hook
pre-commit run ruff --all-files
pre-commit run black --all-files
pre-commit run mypy --all-files
```

### **3. What Each Hook Checks**

#### **Ruff:**
- Variable naming conventions
- Function naming conventions
- Import organization
- Code complexity
- Unused imports/variables
- Code style violations
- Type annotation compliance
- Docstring compliance

#### **Black:**
- Code formatting
- Line length (88 characters)
- Indentation (4 spaces)
- Quote consistency

#### **MyPy:**
- Type hints
- Type checking
- Missing type annotations
- Type compatibility

#### **Bandit:**
- Security vulnerabilities
- Hardcoded passwords
- SQL injection risks
- Unsafe function calls

---

## Tools Configuration

### **1. Ruff Configuration (ruff.toml)**

```toml
target-version = "py311"
line-length = 88
indent-width = 4

[lint]
select = [
    "E", "F", "I", "N", "W", "B", "C4", "UP", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "AIR", "PERF", "LOG", "RUF"
]
ignore = [
    "E501",  # line too long, handled by formatter
    "D200",  # one-line-docstring-should-be-on-one-line
    "D201",  # no-blank-line-before-docstring
    "D202",  # no-blank-line-after-docstring
    "D205",  # 1-blank-line-required-summary-line
    "D208",  # no-blank-line-after-docstring
    "D209",  # multi-line-docstring-closing-bracket-should-be-on-a-separate-line
    "D210",  # no-surrounding-whitespace
    "D211",  # no-blank-line-before-docstring (KEEP THIS - better practice)
    "D212",  # multi-line-docstring-summary-should-start-at-the-first-line (KEEP THIS - better practice)
    "D214",  # section-underline-should-be-passed
    "D215",  # section-underline-is-missing
    "D300",  # use-triple-quotes
    "D301",  # use-r-prefix-for-backslash-escaped-string
    "D400",  # first-line-should-end-with-a-period
    "D401",  # first-line-should-be-in-imperative-mood
    "D402",  # first-line-should-not-be-the-functions-signature
    "D403",  # one-word-per-line
    "D404",  # no-this-any-other
    "D405",  # capitalize-section-name
    "D406",  # new-line-after-section-name
    "D407",  # missing-dashed-underline-after-section
    "D408",  # section underline should be in the line following the section's name
    "D409",  # section underline should match the length of its name
    "D410",  # missing-blank-line-after-section
    "D411",  # missing-blank-line-before-section
    "D412",  # no-blank-lines-between-header-and-content
    "D413",  # missing-blank-line-after-last-section
    "D414",  # section has no content
    "D415",  # first-line-should-end-with-a-period
    "D416",  # section name should end with a newline
    "D417",  # missing-argument-description
    "D418",  # missing-argument-description
    "D419",  # non-argument-description
    # Keep essential rules for code quality
    "PLR2004", # magic numbers (keep - good practice)
    "SIM114", # combine if branches (keep - good practice)
    "SIM116", # use dictionary instead of consecutive if statements (keep - good practice)
    "RET505", # unnecessary elif after return (keep - good practice)
    "TRY300", # consider moving to else block (keep - good practice)
    "TRY401", # redundant exception object (keep - good practice)
    "ARG001", # unused function argument (keep - good practice)
    "ARG002", # unused method argument (keep - good practice)
    "BLE001", # do not catch blind exception (keep - good practice)
    "FBT001", # boolean-typed positional argument (keep - good practice)
    "FBT002", # boolean default positional argument (keep - good practice)
    "PYI041", # use float instead of int | float (keep - good practice)
    "DTZ007", # naive datetime (keep - good practice)
    "SIM118", # use key in dict instead of key in dict.keys() (keep - good practice)
    "RET504", # unnecessary assignment before return (keep - good practice)
    "G004",   # logging statement uses f-string (keep - good practice)
    "T201",   # print found (keep - good practice)
    "EXE001", # shebang is present but file is not executable (keep - good practice)
    "RUF001", # string contains ambiguous character (keep - good practice)
    "S602",   # subprocess call with shell=True (keep - good practice)
    "TD002",  # missing author in TODO (keep - good practice)
    "TD003",  # missing issue link on the line following this TODO (keep - good practice)
    "FIX002", # line contains TODO (keep - good practice)
    "B008",   # do not perform function call in argument defaults (keep - good practice)
    "PGH003", # use specific rule codes when ignoring type issues (keep - good practice)
    "PTH123", # open() should be replaced by Path.open() (keep - good practice)
    "PLR0913", # too many arguments in function definition (keep - good practice)
    "ERA001", # found commented-out code (keep - good practice)
    "PERF401", # use a list comprehension to create a transformed list (keep - good practice)
    "TRY002", # create your own exception (keep - good practice)
    "TRY003", # avoid specifying long messages outside the exception class (keep - good practice)
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["S101", "S603", "S607"]

[lint.flake8-quotes]
docstring-quotes = "double"
inline-quotes = "double"
multiline-quotes = "double"

[lint.isort]
known-first-party = ["app"]
known-third-party = ["fastapi", "sqlalchemy", "pydantic"]

[format]
quote-style = "double"
indent-style = "space"
```

### **2. MyPy Configuration (mypy.ini)**

```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
show_error_codes = True

# Per-module options:
[mypy.plugins.pydantic.*]
init_forbid_extra = True
init_typed = True
warn_required_dynamic_aliases = True
warn_untyped_fields = True

[mypy-fastapi.*]
ignore_missing_imports = True

[mypy-sqlalchemy.*]
ignore_missing_imports = True

[mypy-pydantic.*]
ignore_missing_imports = True
```

### **3. Poetry Configuration (pyproject.toml)**

```toml
[tool.poetry]
name = "nova-law-backend"
version = "1.0.0"
description = "Multi-agent AI system backend with FastAPI, PostgreSQL, LangChain, and LangGraph."
authors = ["Nova Law Team <team@novalaw.ai>"]
readme = "README.md"
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = ">=3.11,<3.12"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
# ... other production dependencies

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
httpx = "^0.25.2"
black = "^24.3.0"
ruff = "^0.4.0"
mypy = "^1.8.0"
pre-commit = "^3.7.0"
bandit = "^1.8.6"  # Security linting

[build-system]
requires = ["poetry-core>=1.5.0"]
build-backend = "poetry.core.masonry.api"
```

**Key Poetry Commands:**
```bash
# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Install dependencies
poetry install

# Update lock file
poetry lock

# Run commands in virtual environment
poetry run python --version
poetry run ruff check .
poetry run bandit -r .
```

---

## Examples

### **1. Complete Function Example**

#### ✅ **Good Example:**
```python
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.schemas.v1.user import UserCreate, UserResponse, UserUpdate
from app.db.models.user import User


def create_user(
    db: Session,
    user_data: UserCreate,
    *,
    validate_email: bool = True,
    send_welcome_email: bool = True
) -> UserResponse:
    """
    Create a new user in the system.

    Args:
        db: Database session for user creation
        user_data: User creation data including email and password
        validate_email: Whether to validate email format before creation
        send_welcome_email: Whether to send welcome email after creation

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException: If email already exists or validation fails
        ValueError: If user data is invalid
    """
    # Validate email if required
    if validate_email and not _is_valid_email(user_data.email):
        raise ValueError("Invalid email format")

    # Check if user already exists
    existing_user = _get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    new_user = _create_user_in_db(db, user_data)

    # Send welcome email if requested
    if send_welcome_email:
        _send_welcome_email(new_user.email)

    return UserResponse.from_orm(new_user)


def _is_valid_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address."""
    return db.query(User).filter(User.email == email).first()


def _create_user_in_db(db: Session, user_data: UserCreate) -> User:
    """Create user in database."""
    from app.core.security import get_password_hash

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def _send_welcome_email(email: str) -> None:
    """Send welcome email to new user."""
    # Email sending logic here
    pass
```

#### ❌ **Bad Example:**
```python
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.schemas.v1.user import UserCreate, UserResponse, UserUpdate
from app.db.models.user import User


def CreateUser(db, userData, validateEmail=True, sendWelcomeEmail=True):
    """Creates user."""
    # No type hints
    if validateEmail and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', userData.email):
        raise ValueError("Invalid email format")

    # Wrong variable naming
    existingUser = db.query(User).filter(User.email == userData.email).first()
    if existingUser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # No error handling
    from app.core.security import get_password_hash
    hashedPassword = get_password_hash(userData.password)
    dbUser = User(
        email=userData.email,
        full_name=userData.full_name,
        hashed_password=hashedPassword
    )
    db.add(dbUser)
    db.commit()
    db.refresh(dbUser)

    if sendWelcomeEmail:
        # Email logic here
        pass

    return UserResponse.from_orm(dbUser)
```

### **2. Class Example**

#### ✅ **Good Example:**
```python
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.models.user import User
from app.schemas.v1.user import UserCreate, UserUpdate, UserResponse


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: Session):
        self.db = db
        self.model = User

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user instance

        Raises:
            ValueError: If user data is invalid
        """
        from app.core.security import get_password_hash

        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.db.query(User).filter(User.email == email).first()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users with pagination."""
        return (
            self.db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete user from database."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        total_users = self.db.query(User).count()
        active_users = (
            self.db.query(User)
            .filter(User.is_active == True)
            .count()
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users
        }
```

#### ❌ **Bad Example:**
```python
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.schemas.v1.user import UserCreate, UserUpdate, UserResponse


class userRepository:
    """user repository."""

    def __init__(self, db):
        self.db = db
        self.model = User

    def createUser(self, userData):
        """creates user."""
        from app.core.security import get_password_hash

        hashedPassword = get_password_hash(userData.password)
        dbUser = User(
            email=userData.email,
            full_name=userData.full_name,
            hashed_password=hashedPassword
        )
        self.db.add(dbUser)
        self.db.commit()
        self.db.refresh(dbUser)
        return dbUser

    def getUserById(self, userId):
        """gets user by id."""
        return self.db.query(User).filter(User.id == userId).first()

    def getUserByEmail(self, email):
        """gets user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def getActiveUsers(self, skip=0, limit=100):
        """gets active users."""
        return (
            self.db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def updateUser(self, userId, userData):
        """updates user."""
        user = self.getUserById(userId)
        if not user:
            return None

        updateData = userData.dict(exclude_unset=True)
        for field, value in updateData.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def deleteUser(self, userId):
        """deletes user."""
        user = self.getUserById(userId)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True
```

---

## Common Issues and Solutions

### **1. Variable Naming Issues**

#### **Problem:**
```python
# ❌ Wrong
userID = "123"
userName = "John"
isActive = True
hasPermission = False
```

#### **Solution:**
```python
# ✅ Correct
user_id = "123"
user_name = "John"
is_active = True
has_permission = False
```

### **2. Function Naming Issues**

#### **Problem:**
```python
# ❌ Wrong
def CreateUser(db, userData):
    pass

def getUserByEmail(email):
    pass

def updateUserPassword(userId, newPassword):
    pass
```

#### **Solution:**
```python
# ✅ Correct
def create_user(db: Session, user_data: UserCreate) -> User:
    pass

def get_user_by_email(email: str) -> User | None:
    pass

def update_user_password(user_id: str, new_password: str) -> bool:
    pass
```

### **3. Type Hint Issues**

#### **Problem:**
```python
# ❌ Wrong
def get_user(db, user_id):
    pass

user_list = []
user_dict = {}
```

#### **Solution:**
```python
# ✅ Correct
def get_user(db: Session, user_id: str) -> User | None:
    pass

user_list: list[User] = []
user_dict: dict[str, User] = {}
```

### **4. Parameter Order Issues**

#### **Problem:**
```python
# ❌ Wrong
def create_user(validate_email=True, db=None, user_data=None):
    pass
```

#### **Solution:**
```python
# ✅ Correct
def create_user(
    db: Session,
    user_data: UserCreate,
    *,
    validate_email: bool = True
) -> User:
    pass
```

### **5. Boolean Variable Issues**

#### **Problem:**
```python
# ❌ Wrong
active = True
permission = False
edit = True
```

#### **Solution:**
```python
# ✅ Correct
is_active = True
has_permission = False
can_edit = True
```

### **6. Import Organization Issues**

#### **Problem:**
```python
# ❌ Wrong
from app.db.database import get_db
import os
from fastapi import APIRouter
from typing import List
import sys
```

#### **Solution:**
```python
# ✅ Correct
import os
import sys
from typing import List

from fastapi import APIRouter

from app.db.database import get_db
```

### **7. Documentation Issues**

#### **Problem:**
```python
# ❌ Wrong
def create_user(db, user_data):
    """Creates user."""
    pass
```

#### **Solution:**
```python
# ✅ Correct
def create_user(
    db: Session,
    user_data: UserCreate
) -> User:
    """
    Create a new user in the system.

    Args:
        db: Database session
        user_data: User creation data

    Returns:
        Created user instance

    Raises:
        ValueError: If user data is invalid
    """
    pass
```

---

## Summary

This reference guide provides comprehensive coding standards for the Nova Law AI FastAPI project. All code must follow these standards to pass pre-commit hooks and maintain high code quality.

### **Key Points:**
1. **Use snake_case for variables and functions**
2. **Use PascalCase for classes**
3. **Use UPPER_SNAKE_CASE for constants**
4. **Always include type hints**
5. **Follow proper parameter order**
6. **Use descriptive names**
7. **Write comprehensive documentation**
8. **Run pre-commit hooks before committing**

### **Tools to Use:**
- **Ruff** for linting and import sorting
- **Black** for code formatting
- **MyPy** for type checking
- **Bandit** for security checks
- **Pre-commit** for automated validation

Follow these standards to ensure consistent, maintainable, and high-quality code across the project.
