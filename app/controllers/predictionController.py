
# controllers/predictionController.py
from datetime import datetime
import logging
import traceback
import inspect
from helper.config import engine
import pandas as pd


from fastapi import APIRouter, Depends, HTTPException
from requests import Session
from starlette.concurrency import run_in_threadpool
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, text

# import your models / helpers
from helper.helpers import duration_to_minutes, parse_total_stops, predict_price
from helper.constants import FlightRequest
from helper.config import Prediction, get_db
from databaseLogic.predictionDL import save_predictions_to_db

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api", tags=["Predictions"])


async def _maybe_async_call(func, *args, **kwargs):
    """
    Helper: calls func either by awaiting if coroutine or using run_in_threadpool for sync functions.
    """
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return await run_in_threadpool(func, *args, **kwargs)


@router.post("/predict")
async def predict_flight_price(request: FlightRequest, db: Session = Depends(get_db)):

    try:
        # Run prediction model
        predicted_price = float(predict_price(request.dict()))
        logger.info(f" Predicted price: {predicted_price}")

        #  Parse date/time info
        try:
            journey_date = datetime.strptime(request.Date_of_Journey, "%d/%m/%Y").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Date_of_Journey format (expected DD/MM/YYYY)")

        # Parse departure and arrival datetimes
        dep_datetime = datetime.strptime(f"{request.Dep_Time} {request.Date_of_Journey}", "%H:%M %d/%m/%Y")
        try:
            arrival_datetime = datetime.strptime(request.Arrival_Time, "%H:%M %d/%m/%Y")
        except ValueError:
            # handle Arrival_Time with date inside
            try:
                arrival_datetime = datetime.strptime(request.Arrival_Time, "%H:%M %d/%m/%Y")
            except Exception:
                # fallback — append journey date
                arrival_datetime = datetime.strptime(
                    f"{request.Arrival_Time} {request.Date_of_Journey}", "%H:%M %d/%m/%Y"
                )

        #  Parse total stops & duration
        total_stops = parse_total_stops(request.Total_Stops)
        duration_mins = duration_to_minutes(request.Duration)

        logger.info(f" Parsed total_stops={total_stops}, duration_mins={duration_mins}")

        # Create DB record
        prediction_record = Prediction(
            airline=request.Airline,
            source=request.Source,
            destination=request.Destination,
            total_stops=total_stops,
            date_of_journey=journey_date,
            dep_datetime=dep_datetime,
            arrival_datetime=arrival_datetime,
            duration_mins=duration_mins,
            raw_duration=request.Duration,
            predicted_price=predicted_price,
        )

        # Save to DB
        try:
            db.add(prediction_record)
            db.commit()
            db.refresh(prediction_record)
            logger.info(f" Saved prediction record ID {prediction_record.id} to database")
        except Exception as db_error:
            db.rollback()
            logger.error(" Database insert failed", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {db_error}")

        #  Return response
        return {
            "prediction_id": prediction_record.id,
            "predicted_price": predicted_price,
        }

    except Exception as e:
        logger.error(" Unhandled exception in /predict")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.get("/past-predictions")
def get_predictions(limit: int = 20):
        # Read directly from PostgreSQL
        query = f"SELECT * FROM predictions;"
        df = pd.read_sql(query, con=engine)

        # Convert DataFrame rows into list of dictionaries
        return df.to_dict(orient="records")

