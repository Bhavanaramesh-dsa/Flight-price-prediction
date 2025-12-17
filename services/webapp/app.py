import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Flight Price Prediction", layout="wide")
st.title("✈️ Flight Price Prediction")

tab1, tab2 = st.tabs(["Predict", "Past Predictions"])

REQUIRED_COLS = [
    "airline",
    "source_city",
    "departure_time",
    "stops",
    "arrival_time",
    "destination_city",
    "class",
    "duration",
    "days_left",
]

# ------------------------------------------------------
# TAB 1 — PREDICT
# ------------------------------------------------------
with tab1:
    st.subheader("Single Prediction")
    cols = st.columns(4)

    airline = cols[0].selectbox("airline", ["SpiceJet", "IndiGo", "Air India", "GoAir", "Vistara", "AirAsia"])
    source_city = cols[1].selectbox("source_city", ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"])
    departure_time = cols[2].selectbox("departure_time", ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"])

    # FIXED: removed invalid "three"
    stops = cols[3].selectbox("stops", ["zero", "one", "two_or_more"])

    arrival_time = cols[0].selectbox("arrival_time", ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"])
    destination_city = cols[1].selectbox("destination_city", ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"])
    cls = cols[2].selectbox("class", ["Economy", "Business"])
    duration = cols[3].number_input("duration (hours)", min_value=0.0, value=2.5, step=0.1)
    days_left = cols[0].number_input("days_left", min_value=0, value=10, step=1)

    if st.button("Predict (Single)"):
        payload = {
            "source": "webapp",
            "records": [{
                "airline": airline,
                "source_city": source_city,
                "departure_time": departure_time,
                "stops": stops,
                "arrival_time": arrival_time,
                "destination_city": destination_city,
                "class": cls,
                "duration": duration,
                "days_left": days_left
            }]
        }

        with st.spinner("Predicting..."):
            try:
                r = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
                r.raise_for_status()
                st.success("Prediction completed")
                st.dataframe(pd.DataFrame(r.json()))
            except Exception as e:
                st.error(f"API error: {e}")

    st.markdown("---")
    st.subheader("Batch Prediction (CSV without 'price')")

    file = st.file_uploader("Upload CSV", type=["csv"])

    if file is not None:
        df = pd.read_csv(file)
        st.write("Preview:", df.head())

        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            st.error(f"Missing required columns: {missing}")

        if st.button("Predict (Batch)") and not missing:
            payload = {"source": "webapp", "records": df.to_dict(orient="records")}

            with st.spinner("Predicting..."):
                try:
                    r = requests.post(f"{API_URL}/predict", json=payload, timeout=20)
                    r.raise_for_status()
                    st.success("Batch prediction completed")
                    st.dataframe(pd.DataFrame(r.json()))
                except Exception as e:
                    st.error(f"API error: {e}")


# ------------------------------------------------------
# TAB 2 — PAST PREDICTIONS
# ------------------------------------------------------
with tab2:
    st.subheader("Past Predictions")
    colA, colB, colC = st.columns(3)

    start = colA.date_input("Start date", value=datetime.utcnow().date() - timedelta(days=7))
    end = colB.date_input("End date", value=datetime.utcnow().date())
    source = colC.selectbox("Source", ["all", "webapp", "scheduled"])

    if st.button("Load"):
        payload = {
            "start": f"{start}T00:00:00",
            "end": f"{end}T23:59:59",
            "source": source
        }

        with st.spinner("Loading..."):
            try:
                r = requests.post(f"{API_URL}/past-predictions", json=payload, timeout=20)
                r.raise_for_status()
                st.dataframe(pd.DataFrame(r.json()))
            except Exception as e:
                st.error(f"API error: {e}")