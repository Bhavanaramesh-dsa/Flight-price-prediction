# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.controllers.predictionController import router as prediction_router
from app.models.dbConfig import Base, engine, create_tables

app = FastAPI(title="Flight Price Prediction")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Create tables at startup
Base.metadata.create_all(bind=engine)
create_tables()

app.include_router(prediction_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
