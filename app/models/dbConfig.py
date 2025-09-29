import os
from sqlalchemy import (
    create_engine, Column, Integer, SmallInteger, Text,
    Date, DateTime, Numeric, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:2801@localhost:5432/flightdb")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

database = Database(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()



class Prediction(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    airline = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    destination = Column(Text, nullable=False)
    total_stops = Column(SmallInteger, nullable=False)
    date_of_journey = Column(Date, nullable=False)
    dep_datetime = Column(DateTime(timezone=False), nullable=False)
    arrival_datetime = Column(DateTime(timezone=False), nullable=False)
    duration_mins = Column(Integer, nullable=False)
    raw_duration = Column(Text)
    predicted_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


def get_db():
    #SQLAlchemy session"
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

