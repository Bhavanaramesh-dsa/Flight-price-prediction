import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.controllers.predictionController import router as prediction_router
from app.helper.config import Base, engine, get_db
from app.models.dbConfig import FlightPrediction

app = FastAPI(title="Flight Price Prediction")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Create tables at startup
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

# Health check endpoint
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Test connection
        db.execute("SELECT 1")
        
        # Count records in each table
        flights_count = db.execute("SELECT COUNT(*) FROM flights").scalar()
        predictions_count = db.execute("SELECT COUNT(*) FROM flight_predictions").scalar()
        clean_dataset_count = db.execute("SELECT COUNT(*) FROM Clean_Dataset").scalar()
        
        return {
            "status": "healthy",
            "database": "connected", 
            "tables": {
                "flights": flights_count,
                "flight_predictions": predictions_count,
                "Clean_Dataset": clean_dataset_count
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Get all predictions from flight_predictions table
@app.get("/predictions")
def get_predictions(db: Session = Depends(get_db)):
    try:
        predictions = db.query(FlightPrediction).order_by(FlightPrediction.prediction_date.desc()).all()
        return [
            {
                "id": pred.id,
                "airline": pred.airline,
                "source_city": pred.source_city,
                "destination_city": pred.destination_city,
                "predicted_price": float(pred.predicted_price) if pred.predicted_price else None,
                "prediction_date": pred.prediction_date.isoformat() if pred.prediction_date else None
            }
            for pred in predictions
        ]
    except Exception as e:
        return {"error": str(e)}

# Include your existing prediction routes
app.include_router(prediction_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)