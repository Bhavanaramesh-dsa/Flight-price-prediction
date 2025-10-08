
from datetime import date, datetime
from pydantic import BaseModel, Field


# Input payload 
class FlightRequest(BaseModel):
    Airline: str = Field(..., example="IndiGo")
    Source: str = Field(..., example="Delhi")
    Destination: str = Field(..., example="Cochin")
    Total_Stops: str = Field(..., example="1 stop")
    Date_of_Journey: str = Field(..., example="24/03/2019")  # dd/mm/yyyy
    Dep_Time: str = Field(..., example="22:20")  # HH:MM 24h
    Arrival_Time: str = Field(..., example="01:10 25/03/2019")  # HH:MM dd/mm/yyyy or HH:MM
    Duration: str = Field(..., example="2h 50m")

# Output payload 
class PredictionResponse(BaseModel):
    id: int
    airline: str
    source: str
    destination: str
    total_stops: int
    date_of_journey: date
    dep_datetime: datetime
    arrival_datetime: datetime
    duration_mins: int
    raw_duration: str | None = None
    predicted_price: float
    created_at: datetime


