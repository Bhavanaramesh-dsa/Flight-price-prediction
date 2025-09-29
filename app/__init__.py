from fastapi import FastAPI


app = FastAPI(title="Flight Price Prediction API")

# Import routes (so FastAPI knows them)

from app.controllers import predictionController