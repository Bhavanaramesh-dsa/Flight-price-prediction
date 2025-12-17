from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ---------------------------------------------------------
# Input for /predict
# ---------------------------------------------------------
class PredictRequest(BaseModel):
    source: str = Field(..., description="webapp | scheduled")
    records: List[Dict[str, Any]] = Field(
        ..., description="List of feature dictionaries"
    )


# ---------------------------------------------------------
# Output returned by /predict and past predictions
# ---------------------------------------------------------
class PredictionOut(BaseModel):
    id: int
    created_at: datetime
    source: str
    features: Dict[str, Any]
    prediction: float

    class Config:
        orm_mode = True    # Important for SQLAlchemy → Pydantic conversion


# ---------------------------------------------------------
# Query body for /past-predictions
# ---------------------------------------------------------
class PastPredictionsQuery(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    source: Optional[str] = Field(
        None,
        description="webapp | scheduled | all"
    )