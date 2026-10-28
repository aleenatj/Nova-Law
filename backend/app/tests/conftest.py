# Set test environment variables BEFORE any imports
import asyncio
import os
import warnings
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app

# Set test environment variables
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("JWE_SECRET_KEY", "test-jwe-secret-key-for-testing-only")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "2")

# Set required environment variables for testing
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test-aws-key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test-aws-secret")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("DEFAULT_EMAIL_SENDER", "test@example.com")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("QUESTIONS_FILE_PATH", "app/config/questions/resolve.json")

# Set database environment variables for testing
# These will be used to construct the database URL
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "nova_law_test")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")

"""
Test configuration and fixtures for Nova Law AI Backend tests.
"""

# Suppress Pydantic V1/V2 mixing warning during tests
# This is a known issue with LangChain's BaseMessage still using Pydantic V1
warnings.filterwarnings(
    "ignore",
    message="Mixing V1 models and V2 models.*",
    category=UserWarning,
    module="pydantic._internal._generate_schema",
)

# Create test-specific database engine

# Create test database engine with proper configuration for testing
test_engine = create_engine(
    settings.database_url,
    poolclass=NullPool,  # No connection pooling for tests
    echo=False,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False,  # Prevent expired object issues
)


def override_get_db() -> Generator[Session, None, None]:
    """Override the database dependency for testing."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create a database engine for testing."""
    yield test_engine


def cleanup_test_users(session: Session) -> None:
    """Clean up only test users (identified by email pattern)."""
    try:
        # Delete test users by email pattern (test.*@unit-test.com, navigator.*@unit-test.com, etc.)
        session.execute(
            text(
                "DELETE FROM user_role WHERE user_id IN (SELECT id FROM \"user\" WHERE email LIKE 'test%@unit-test.com' OR email LIKE 'navigator%@unit-test.com' OR email LIKE 'john.doe.%@unit-test.com' OR email LIKE 'jane.doe.%@unit-test.com' OR email LIKE 'customer%@unit-test.com' OR email LIKE 'lawyer%@unit-test.com' OR email LIKE 'norole%@unit-test.com' OR email LIKE 'inactive%@unit-test.com' OR email LIKE 'test2%@unit-test.com' OR email LIKE 'test3%@unit-test.com' OR email LIKE 'minimal%@unit-test.com' OR email LIKE 'jose.maria%@unit-test.com')"
            )
        )
        session.execute(
            text(
                "DELETE FROM \"user\" WHERE email LIKE 'test%@unit-test.com' OR email LIKE 'navigator%@unit-test.com' OR email LIKE 'john.doe.%@unit-test.com' OR email LIKE 'jane.doe.%@unit-test.com' OR email LIKE 'customer%@unit-test.com' OR email LIKE 'lawyer%@unit-test.com' OR email LIKE 'norole%@unit-test.com' OR email LIKE 'inactive%@unit-test.com' OR email LIKE 'test2%@unit-test.com' OR email LIKE 'test3%@unit-test.com' OR email LIKE 'minimal%@unit-test.com' OR email LIKE 'jose.maria%@unit-test.com'"
            )
        )
        session.commit()
    except Exception:
        session.rollback()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=test_engine)

    # Create a new session
    session = TestSessionLocal()

    # Clean up any existing test data before the test
    cleanup_test_users(session)

    yield session

    # Clean up test data after the test
    cleanup_test_users(session)
    session.close()


# No cleanup needed for PostgreSQL database
# The database will persist between test runs
