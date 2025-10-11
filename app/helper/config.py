from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL (from env or default)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:Password@postgres:5432/predictions")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model class
Base = declarative_base()


# ✅ Add this function — this is what FastAPI Depends(get_db) needs
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional: for creating tables during startup
def create_tables():
    Base.metadata.create_all(bind=engine)
