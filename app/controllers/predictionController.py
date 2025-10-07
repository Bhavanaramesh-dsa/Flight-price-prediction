
# controllers/predictionController.py
from typing import List, Optional
import logging
import traceback
import inspect

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

# import your models / helpers
from models.dbConfig import get_db, Prediction, Base, engine
from helper.constants import FlightRequest
from helper.helpers import predict_flight_price_util, parse_datetime, duration_to_minutes
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
async def predict_flight_price(request: FlightRequest, db: AsyncSession = Depends(get_db)):
    """
    Accepts a single FlightRequest and returns predicted_price + saved DB record id.
    """
    try:
        logger.info(f"Received prediction request: {request.dict()}")

        # 1) Generate prediction (handle sync/async util)
        predicted_price = await _maybe_async_call(predict_flight_price_util, request.dict())
        logger.info(f"Predicted price: {predicted_price}")

        # 2) Parse datetimes and duration
        journey_date, dep_datetime, arrival_datetime = parse_datetime(
            request.Date_of_Journey, request.Dep_Time, request.Arrival_Time
        )
        duration_mins = duration_to_minutes(request.Duration)

        # 3) Save prediction record (handle sync/async)
        prediction_record = await _maybe_async_call(
            save_prediction_record,
            db,
            request,
            predicted_price,
            journey_date,
            dep_datetime,
            arrival_datetime,
            duration_mins
        )

        # commit (AsyncSession)
        await db.commit()

        logger.info(f"✅ Saved prediction record ID {getattr(prediction_record, 'id', None)} to database")
        return {"prediction_id": getattr(prediction_record, "id", None), "predicted_price": predicted_price}

    except ValueError as ve:
        logger.error("ValueError during prediction")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error("Unhandled exception during /predict call")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
async def predict_batch(requests: List[FlightRequest], db: AsyncSession = Depends(get_db)):
    """
    Accepts a list of FlightRequest and returns list of {prediction_id, predicted_price}.
    Useful for Airflow sending bulk CSV rows in one request.
    """
    results = []
    try:
        for r in requests:
            predicted_price = await _maybe_async_call(predict_flight_price_util, r.dict())
            journey_date, dep_datetime, arrival_datetime = parse_datetime(
                r.Date_of_Journey, r.Dep_Time, r.Arrival_Time
            )
            duration_mins = duration_to_minutes(r.Duration)
            record = await _maybe_async_call(
                save_prediction_record,
                db,
                r,
                predicted_price,
                journey_date,
                dep_datetime,
                arrival_datetime,
                duration_mins
            )
            results.append({"prediction_id": getattr(record, "id", None), "predicted_price": predicted_price})
        await db.commit()
        return {"predictions": results}
    except Exception:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Batch prediction failed")


@router.get("/past-predictions")
async def get_predictions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    # make sure to await execute (AsyncSession)
    result = await db.execute(select(Prediction).order_by(Prediction.arrival_time.desc()).limit(limit))
    predictions = result.scalars().all()
    return predictions
