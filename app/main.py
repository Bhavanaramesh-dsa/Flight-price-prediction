from inspect import getmodule
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.controllers.predictionController import router as prediction_router
from app.models.dbConfig import Settings
from app.models.dbConfig import database, create_tables

app = FastAPI(title="Flight Price Prediction")

# Root redirects to Swagger UI
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Include prediction router
app.include_router(prediction_router)

# Startup event
@app.on_event("startup")
async def startup():
    # Connect DB
    await database.connect()
    # Create tables
    create_tables()
    # Load model
    _ = getmodule()
    print("Startup complete: DB connected and model loaded.")

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Run with uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=Settings.APP_HOST,
        port=Settings.APP_PORT,
        reload=True
    )
