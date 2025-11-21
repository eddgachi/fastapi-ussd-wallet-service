from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from db.models import Base

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.ENV == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)
