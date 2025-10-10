import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from controllers.predictionController import router as prediction_router
from helper.config import Base, engine, create_tables
import logging

app = FastAPI(title="Flight Price Prediction")

@app.on_event("startup")
def on_startup():
    logging.getLogger(__name__).info(" Starting up FastAPI application...")
    try:
        create_tables()
    except Exception as e:
        logging.getLogger(__name__).error(f" Database connection failed: {e}", exc_info=True)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

app.include_router(prediction_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)



