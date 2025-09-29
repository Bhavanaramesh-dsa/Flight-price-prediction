# from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from ..models.dbConfig import Prediction

from ..models.dbConfig import Base, engine, get_db
from ..helper.constants import  FlightRequest, PredictionInput
from sqlalchemy import Engine, select
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base


from fastapi import APIRouter, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.dbConfig import Base
from ..helper.constants import FlightRequest
from ..helper.helpers import (
    predict_flight_price_util,
    parse_datetime,
    duration_to_minutes
)

from ..databaseLogic.predictionDL import save_prediction_record

Base.metadata.create_all(bind=engine)


router = APIRouter(
    prefix="/api",
    tags=["Predictions"]
)

class Config:
        orm_mode = True



router = APIRouter(
    prefix="/api",
    tags=["Predictions"]
)

# Base.metadata.create_all(bind=Base.metadata.bind)
Base.metadata.create_all(bind=engine)


@router.post("/predict")
async def predict_flight_price(request: FlightRequest, db: AsyncSession = Depends(get_db)):
 
    try:
        predicted_price = await predict_flight_price_util(request.dict())
        journey_date, dep_datetime, arrival_datetime = parse_datetime(
            request.Date_of_Journey,
            request.Dep_Time,
            request.Arrival_Time
        )
        duration_mins = duration_to_minutes(request.Duration)

        prediction_record = await save_prediction_record(
            db=db,
            request=request,
            predicted_price=predicted_price,
            journey_date=journey_date,
            dep_datetime=dep_datetime,
            arrival_datetime=arrival_datetime,
            duration_mins=duration_mins
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Prediction error: {error}")

    return {
        "prediction_id": prediction_record.id,
        "predicted_price": predicted_price
    }


@router.get("/past-predictions")
async def get_predictions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result =  db.execute(
        select(Prediction).order_by(Prediction.arrival_time.desc()).limit(limit)
    )
    predictions = result.scalars().all()
    return predictions