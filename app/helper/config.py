from pydantic import BaseSettings
from sqlalchemy import (
    create_engine, Column, Integer, SmallInteger, Text,
    Date, DateTime, Numeric, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# app/helper/config.py
from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "Password"
    DB_HOST: str = "postgres"
    DB_PORT: str = "5432"
    DB_NAME: str = "predictions"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"   # tells Pydantic to read from your .env


# this line will now succeed
settings = Settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Prediction(Base):
    __tablename__ = "predictions"

    # Use serial_number if that's what your DB schema uses
    serial_number = Column(Integer, primary_key=True, index=True)
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
