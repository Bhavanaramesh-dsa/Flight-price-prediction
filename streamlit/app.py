import streamlit as st
import pandas as pd
import pickle
from catboost import CatBoostRegressor
import os

# ===============================
# 1. Load model and columns
# ===============================
model_path = "model/catboost_flight_price_model.cbm"
columns_path = "model/model_columns.pkl"

# Check if files exist
if not os.path.exists(model_path) or not os.path.exists(columns_path):
    st.error("❌ Model or columns file not found! Please train the model first.")
    st.stop()