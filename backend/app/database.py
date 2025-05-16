from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Create SQLAlchemy engine instance
engine = create_engine(settings.DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models, all the models will inherit this base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Dependency function that yields db session
    and ensures it gets closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()