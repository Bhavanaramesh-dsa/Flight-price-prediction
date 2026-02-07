from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Prediction
from .schemas import PredictRequest, PredictionOut, PastPredictionsQuery
from .ml.model_service import model_service


# ---------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------
app = FastAPI(
    title="Flight Price Prediction API",
    version="1.0.0",
    description="Serves ML predictions and logs them to PostgreSQL."
)


# ---------------------------------------------------------
# STATIC MOUNT: Serve GE reports
# ---------------------------------------------------------
app.mount(
    "/reports",
    StaticFiles(directory="/app/reports"),
    name="reports"
)


# ---------------------------------------------------------
# Database dependency
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Startup: load model once
# ---------------------------------------------------------
@app.on_event("startup")
def load_model():
    print("[INFO] Loading ML model...")
    try:
        model_service.load()
        print("[INFO] Model loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------
# Predict endpoint (SINGLE + BATCH)
# ---------------------------------------------------------
@app.post("/predict", response_model=List[PredictionOut])
def predict(req: PredictRequest, db: Session = Depends(get_db)):

    if not req.records:
        raise HTTPException(status_code=400, detail="No records provided.")

    try:
        preds = model_service.predict(req.records)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Model file not found. Please train the model first."
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed: {str(e)}"
        )

    results: List[PredictionOut] = []

    # -------------------------------------------------
    # BUSINESS NORMALIZATION RULES
    # -------------------------------------------------
    MIN_PRICE = 500.0        # minimum realistic fare
    ROUND_TO = 100           # round to nearest ₹100

    for rec, pred in zip(req.records, preds):

        pred = float(pred)

        # Enforce minimum price
        if pred < MIN_PRICE:
            pred = MIN_PRICE

        pred = round(pred / ROUND_TO) * ROUND_TO

        obj = Prediction(
            source=req.source,
            features=rec,
            prediction=pred,
        )

        db.add(obj)
        db.flush()

        results.append(
            PredictionOut(
                id=obj.id,
                created_at=obj.created_at,
                source=obj.source,
                features=rec,
                prediction=pred,
            )
        )

    db.commit()
    return results


# ---------------------------------------------------------
# Past predictions endpoint
# ---------------------------------------------------------
@app.post("/past-predictions", response_model=List[PredictionOut])
def past_predictions(query: PastPredictionsQuery, db: Session = Depends(get_db)):

    q = db.query(Prediction)

    if query.start:
        q = q.filter(Prediction.created_at >= query.start)

    if query.end:
        q = q.filter(Prediction.created_at <= query.end)

    if query.source and query.source != "all":
        q = q.filter(Prediction.source == query.source)

    q = q.order_by(Prediction.created_at.desc()).limit(1000)

    return [
        PredictionOut(
            id=p.id,
            created_at=p.created_at,
            source=p.source,
            features=p.features,
            prediction=p.prediction,
        )
        for p in q.all()
    ]