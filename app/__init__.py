# app/__init__.py

import os

# Only initialize FastAPI if running inside the FastAPI container
# (Airflow just needs to import database logic)
if os.getenv("FASTAPI_MODE", "false").lower() == "true":
    from fastapi import FastAPI
    from controllers import predictionController

    app = FastAPI(title="Flight Price Prediction API")

    # Register routes
    app.include_router(predictionController.router)
else:
    app = None  # No FastAPI needed for Airflow
