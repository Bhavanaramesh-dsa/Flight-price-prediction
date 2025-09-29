# app/models/dbConfig.py
import os
from sqlalchemy import create_engine, Column, Integer, SmallInteger, Text, Date, DateTime, Numeric, func, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:flightdb@localhost:5432/flightdb")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# SQLAlchemy Base
metadata = MetaData()
Base = declarative_base(metadata=metadata)


def create_tables():
    Base.metadata.create_all(bind=engine)


load_dotenv()

# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = os.getenv("DB_PORT")
# DB_NAME = os.getenv("DB_NAME")

# SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
class Prediction(Base):
    __tablename__ = "flights"

    id = Column("serial_number", Integer, primary_key=True, index=True)  
    airline = Column(Text)
    flight = Column(Text)
    source_city = Column(Text)
    departure_time = Column(DateTime)
    stops = Column(SmallInteger)
    arrival_time = Column(DateTime)
    destination_city = Column(Text)
    class_type = Column("class", Text)
    duration = Column(Text)
    days_left = Column(Integer)
    price = Column(Numeric(10, 2))



# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
