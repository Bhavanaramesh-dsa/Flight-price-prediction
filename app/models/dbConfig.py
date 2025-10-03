from sqlalchemy import create_engine, Column, Integer, SmallInteger, Text, DateTime, Numeric, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from app.helper.config import settings

# PostgreSQL connection
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# SQLAlchemy Base
metadata = MetaData()
Base = declarative_base(metadata=metadata)


def create_tables():
    Base.metadata.create_all(bind=engine)


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
