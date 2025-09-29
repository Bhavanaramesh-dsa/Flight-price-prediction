
from sqlmodel import Session
from app.helper.config import Prediction


from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

def save_prediction_record(db: Session, request, predicted_price: float,
                           journey_date, dep_datetime, arrival_datetime, duration_mins):
    try:
        prediction_record = Prediction(
            airline=request.Airline,
            source=request.Source,
            destination=request.Destination,
            total_stops=int(request.Total_Stops.split()[0]) if 'stop' in request.Total_Stops else 0,
            date_of_journey=journey_date,
            dep_datetime=dep_datetime,
            arrival_datetime=arrival_datetime,
            duration_mins=duration_mins,
            raw_duration=request.Duration,
            predicted_price=predicted_price
        )
        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)
        return prediction_record

    except SQLAlchemyError as e:
        db.rollback()  # rollback transaction if error
        raise RuntimeError(f"Database error while saving prediction: {str(e)}") from e
