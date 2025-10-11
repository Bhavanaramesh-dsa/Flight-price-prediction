# ✈️ Flight Price Prediction System

An **end-to-end Machine Learning system** that predicts flight ticket prices, automates scheduled batch predictions, and provides a **real-time dashboard** for data quality and model monitoring.  
This project integrates **Streamlit**, **FastAPI**, **Airflow**, **PostgreSQL**, and **Grafana** into one seamless solution.

🚀 Built with 💡 curiosity, ✈️ passion for travel, and 🧠 applied machine learning!

---

## 🌟 Table of Contents

- [Project Highlights](#-project-highlights)
- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Data Files](#-data-files)
- [Results & Monitoring](#-results--monitoring)
- [Conclusion](#-conclusion)

---

## 🌟 Project Highlights

- 🖥️ **Interactive Streamlit UI** for on-demand flight price predictions  
- ⚡ **FastAPI** backend to serve trained ML models  
- 🕒 **Airflow DAGs** for scheduled data ingestion & predictions  
- 🧹 **Automated data validation** and preprocessing  
- 🗄️ **PostgreSQL** for storing prediction records  
- 🧮 **CatBoost regression model** for accurate flight price prediction  
- 🧰 **Dockerized workflow** for reproducible development & deployment  

---

## 🛠 Tech Stack

| Category | Tools |
|-----------|-------|
| 💻 **Language** | Python 3.10+ |
| 🧠 **ML Framework** | CatBoost, scikit-learn |
| 🧹 **Data Processing** | pandas, numpy |
| ⚙️ **Orchestration** | Apache Airflow |
| 🌐 **APIs** | FastAPI |
| 🖥️ **Web Interface** | Streamlit |
| 🗄️ **Database** | PostgreSQL |
| 🧰 **Containerization** | Docker, Docker Compose |
| 💻 **IDE** | VS Code |
| 🔧 **Version Control** | Git + GitHub |

---

## 🧠 How It Works

### 1️⃣ Streamlit Interface
- Users enter flight details (Airline, Source, Stops, Duration, etc.)  
- The app calls the FastAPI endpoint for price prediction  
- Displays results with historical data from the database  

### 2️⃣ FastAPI Backend
- Hosts the trained CatBoost model  
- Provides `/predict` and `/past-predictions` endpoints  
- Logs every prediction (inputs + results + timestamp) in PostgreSQL  

### 3️⃣ Airflow Orchestration
- `data_ingestion_dag.py`: fetches new flight data and validates it  
- `prediction_dag.py`: performs scheduled batch predictions  
- Logs all jobs in Airflow’s metadata DB  

### 4️⃣ Data Validation & Preprocessing
- Automatically checks for missing or invalid values  
- Moves clean files to `good-data/`, invalid files to `raw-data/`  

### 5️⃣ Model & Storage
- Trained model: `catboost_flight_price_model.cbm`  
- Feature columns: `model_columns.pkl`  
- Stored in `/model` directory  
 
---

## 📂 Project Structure
FLIGHTPRICEPREDICTION/
│
├── airflow/
│ ├── config/
│ ├── dags/
│ │ ├── validation/
│ │ ├── data_ingestion_dag.py
│ │ └── prediction_dag.py
│ ├── data/
│ │ ├── good-data/
│ │ ├── predictions/
│ │ └── raw-data/
│ ├── plugins/
│ ├── Dockerfile.airflow
│ ├── requirements.txt
│ └── webserver_config.py
│
├── app/
│ └── controller/ # FastAPI app logic (if any)
│
├── dataset/
│ ├── dataset.csv
│ └── raw_data_with_errors.csv
│
├── logs/
│
├── model/
│ ├── catboost_flight_price_model.cbm
│ └── model_columns.pkl
│
├── notebook/
│ ├── data_quality_assessment.ipynb
│ ├── prediction.ipynb
│ └── saved_models/
│
├── plugins/
│
├── scripts/
│ ├── generate_data_errors.py
│ ├── split_raw_data.py
│ └── streamlit/
│ └── app.py # Streamlit application
│
├── .env
├── .gitignore
├── docker-compose.yaml
├── requirements.txt
└── README.md

---

## 🧠 How It Works

### 1️⃣ Streamlit Interface
- Users enter flight details (Airline, Source, Stops, Duration, etc.)  
- The app calls the FastAPI endpoint for price prediction  
- Displays results with historical data from the database  

### 2️⃣ FastAPI Backend
- Hosts the trained CatBoost model  
- Provides `/predict` and `/past-predictions` endpoints  
- Logs every prediction (inputs + results + timestamp) in PostgreSQL  

### 3️⃣ Airflow Orchestration
- `data_ingestion_dag.py`: fetches new flight data and validates it  
- `prediction_dag.py`: performs scheduled batch predictions  
- Logs all jobs in Airflow’s metadata DB  

### 4️⃣ Data Validation & Preprocessing
- Automatically checks for missing or invalid values  
- Moves clean files to `good-data/`, invalid files to `raw-data/`  

### 5️⃣ Model & Storage
- Trained model: `catboost_flight_price_model.cbm`  
- Feature columns: `model_columns.pkl`  
- Stored in `/model` directory  


## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/FlightPricePrediction.git
cd FlightPricePrediction


### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/FlightPricePrediction.git
cd FlightPricePrediction

python -m venv venv
source venv/bin/activate    # macOS/Linux
# OR
venv\Scripts\activate       # Windows

#Run Airflow using docker 
docker-compose up --build

# 1️⃣ Rebuild containers without cache (optional if changes were made)
docker compose build --no-cache

# 2️⃣ Start containers in detached mode
docker compose up -d

# 3️⃣ (Optional) View logs in real time
docker compose up

🏁 Conclusion
This project represents a complete production-ready ML workflow, integrating:
✅ Real-time prediction API
✅ User-friendly UI (Streamlit)
✅ Automated Airflow scheduling
✅ Centralized data storage
It’s a true example of end-to-end MLOps — combining data engineering, model deployment, and observability.
