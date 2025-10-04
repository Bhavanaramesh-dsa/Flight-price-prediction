from sqlalchemy import Column, Integer, SmallInteger, Text, Date, DateTime, Numeric, func
from app.helper.config import Base

# Your existing Prediction model
class Prediction(Base):
    __tablename__ = "flights"

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

# New model for API predictions
class FlightPrediction(Base):
    __tablename__ = "flight_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    airline = Column(Text)
    source_city = Column(Text)
    departure_time = Column(Text)
    stops = Column(Text)
    arrival_time = Column(Text)
    destination_city = Column(Text)
    class_type = Column(Text)
    duration = Column(Numeric(10, 2))
    days_left = Column(Integer)
    predicted_price = Column(Numeric(10, 2))
    actual_price = Column(Numeric(10, 2), nullable=True)
    prediction_date = Column(DateTime, server_default=func.now())

def create_tables():
    from app.helper.config import engine
    Base.metadata.create_all(bind=engine)