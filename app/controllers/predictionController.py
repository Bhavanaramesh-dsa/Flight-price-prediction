
# controllers/predictionController.py
from datetime import datetime
import logging
import traceback
import inspect

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

# import your models / helpers
from models.dbConfig import get_db, Prediction, Base, engine
from constants import FlightRequest
from helpers import parse_total_stops, predict_flight_price_util, parse_datetime, duration_to_minutes, predict_price
from databaseLogic.predictionDL import save_prediction_record

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
def predict_flight_price(request: FlightRequest, db: Session = Depends(get_db)):

    try:
        # 1️⃣ Run prediction model
        predicted_price = float(predict_price(request.dict()))
        logger.info(f"💰 Predicted price: {predicted_price}")

        # 2️⃣ Parse date/time info
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

        logger.info(f"🛫 Parsed total_stops={total_stops}, duration_mins={duration_mins}")

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
async def get_predictions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    # make sure to await execute (AsyncSession)
    result = await db.execute(select(Prediction).order_by(Prediction.arrival_time.desc()).limit(limit))
    predictions = result.scalars().all()
    return predictions
