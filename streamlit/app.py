import streamlit as st
import pandas as pd
import pickle
from catboost import CatBoostRegressor
import os

# 1. Load model and columns

model_path = "model/catboost_flight_price_model.cbm"
columns_path = "model/model_columns.pkl"

# Check if files exist
if not os.path.exists(model_path) or not os.path.exists(columns_path):
    st.error(" Model or columns file not found! Please train the model first.")
    st.stop()

# Load CatBoost model
model = CatBoostRegressor()
model.load_model(model_path)

# Load training columns
model_columns = pickle.load(open(columns_path, "rb"))

#  Streamlit UI
st.title(" Flight Price Prediction App ")

# Flight details input
airline = st.selectbox("Airline", ["Jet Airways", "IndiGo", "Air India", "SpiceJet", "GoAir"])
source = st.selectbox("Source", ["Delhi", "Kolkata", "Mumbai", "Chennai", "Bangalore"])
destination = st.selectbox("Destination", ["Cochin", "Banglore", "Delhi", "New Delhi", "Hyderabad"])
total_stops = st.number_input("Total Stops", min_value=0, max_value=5, value=1)
journey_day = st.number_input("Journey Day", min_value=1, max_value=31, value=15)
journey_month = st.number_input("Journey Month", min_value=1, max_value=12, value=6)
dep_hour = st.number_input("Departure Hour", min_value=0, max_value=23, value=9)
dep_minute = st.number_input("Departure Minute", min_value=0, max_value=59, value=45)
duration_hours = st.number_input("Duration Hours", min_value=0, max_value=24, value=2)
duration_mins = st.number_input("Duration Minutes", min_value=0, max_value=59, value=30)

#  Prediction
if st.button("Predict Price"):
    # Create input DataFrame
    input_dict = {
        "Total_Stops": [total_stops],
        "Journey_day": [journey_day],
        "Journey_month": [journey_month],
        "Dep_hour": [dep_hour],
        "Dep_min": [dep_minute],
        "Duration_hours": [duration_hours],
        "Duration_mins": [duration_mins],
        "Airline_" + airline: [1],
        "Source_" + source: [1],
        "Destination_" + destination: [1]
    }

    input_df = pd.DataFrame(input_dict)

    # Align input with training columns
    input_df = input_df.reindex(columns=model_columns, fill_value=0)

    # Predict
    predicted_price = model.predict(input_df)[0]

    st.success(f" Predicted Flight Price: ₹ {predicted_price:,.2f}")
