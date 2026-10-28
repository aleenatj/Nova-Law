from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Create database engine using the constructed database URL
engine = create_engine(
    settings.database_url,
    pool_size=15,             # number of connections to keep open
    max_overflow=20,         # how many extra connections can be opened
    pool_pre_ping=True,      # check if connections are alive
    pool_recycle=1800,       # recycle connections after 30 min
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
