


# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from controllers.predictionController import router as prediction_router

from models.dbConfig import Base, engine, create_tables

app = FastAPI(title="Flight Price Prediction")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Create tables at startup (do this here once)
Base.metadata.create_all(bind=engine)

try:
    create_tables()
except Exception:
    # not fatal: log and continue
    import logging, traceback
    logging.getLogger(__name__).warning("create_tables() raised an exception:\n" + traceback.format_exc())

# include router once (router already has prefix="/api")
app.include_router(prediction_router)


if __name__ == "__main__":
    # When running python main.py directly, bind to 0.0.0.0 so docker can reach it if needed
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
