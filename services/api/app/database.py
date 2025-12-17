from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ---------------------------------------------------------------------
# Database URL (FastAPI uses predictions DB)
# ---------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@postgres:5432/predictions"
)

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base model
Base = declarative_base()

# ---------------------------------------------------------------------
# Import ONLY Prediction model (FastAPI should not manage ingestion tables)
# ---------------------------------------------------------------------
from app.models import Prediction

# ---------------------------------------------------------------------
# OPTIONAL: Remove table auto-creation
# Tables are created by initdb scripts, not FastAPI
# ---------------------------------------------------------------------
# Base.metadata.create_all(bind=engine)