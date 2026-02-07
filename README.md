# ✈️ Flight Price Prediction – End-to-End MLOps Pipeline

An end-to-end **Flight Price Prediction system** demonstrating a **full MLOps lifecycle**: data ingestion, validation, prediction, monitoring, alerting, and user interaction.

This project integrates **Machine Learning, Apache Airflow, Great Expectations, Grafana, PostgreSQL, Microsoft Teams alerts, and Streamlit**, all orchestrated using **Docker Compose**.

---

## 🚀 Project Highlights

- 🔹 Single & Batch flight price prediction (Streamlit UI)
- 🔹 Automated ingestion & prediction using Airflow DAGs
- 🔹 Data quality validation with Great Expectations
- 🔹 Monitoring dashboards in Grafana
- 🔹 Real-time alerts via Microsoft Teams
- 🔹 Prediction storage in PostgreSQL
- 🔹 Fully containerized multi-service architecture

---

## 🏗️ System Architecture
![System Architechture](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/SystemArch.png)

**High-level flow:**

1. Raw flight data ingestion  
2. Data quality validation (Great Expectations)  
3. Segregation of good / bad data  
4. Scheduled & on-demand predictions  
5. Monitoring & alerting  
6. User interaction through Streamlit  

---

## 🧰 Tech Stack

| Layer | Technology |
|------|-----------|
| Programming | Python 3.10 |
| ML | Scikit-Learn |
| Orchestration | Apache Airflow |
| Data Validation | Great Expectations |
| Monitoring | Grafana |
| Alerts | Microsoft Teams |
| Database | PostgreSQL |
| UI | Streamlit |
| Containers | Docker & Docker Compose |

---

## 📁 Project Structure

```text
FlightPricePrediction/
│
├── data/
│   ├── raw_data/
│   ├── good_data/
│   ├── bad_data/
│   ├── predictions/
│   └── reports/
│
├── dataset/
│   └── flights.csv
│
├── gx/                         # Great Expectations
│   ├── expectations/
│   ├── checkpoints/
│   └── ge_docs/
│
├── models/
│   └── model.joblib
│
├── scripts/
│   ├── error_generator.py
│   ├── split_dataset.py
│   └── train_model.py
│
├── services/
│   ├── airflow/
│   │   ├── dags/
│   │   ├── logs/
│   │   └── Dockerfile
│   │
│   ├── api/
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   │
│   └── webapp/
│       └── app.py
│
├── images/
├── docker-compose.yml
└── README.md
---
```

##⚙️ How to Run the Project
1️⃣ Clone the Repository
git clone <repository-url>
cd FlightPricePrediction
2️⃣ Start All Services
docker-compose up --build

This will start:

PostgreSQL
Airflow (Webserver + Scheduler)
Streamlit Web Application
Grafana

3️⃣ Access Services
#Service	URL :

Streamlit UI:http://localhost:8501

Airflow UI:http://localhost:8080

Grafana:http://localhost:3000

PostgreSQL:localhost:5432

---

##🧠 Machine Learning Pipeline

Dataset: Flight price dataset (CSV)
Features include airline, cities, duration, stops, class, days left
Model trained using train_model.py
Serialized model saved as model.joblib
Used by both Streamlit UI and Airflow prediction DAG

##🖥️ Streamlit Web Application

###🔹 Single Prediction
User selects flight attributes
Instant price prediction
Prediction stored in PostgreSQL

![Streamlit Single](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Streamlit-SinglePrediction.png)

###🔹 Batch Prediction
Upload CSV (without price column)
Batch predictions generated
Stored and monitored automatically

![Streamlit Batch](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Streamlit-BatchPrediction.png)

###🔹 Past Predictions
Filter predictions by date & source
Compare scheduled vs manual predictions

![Streamlit Past](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Streamlit-PastPrediction.png)

---

##⏱️ Airflow Workflows

#Ingestion DAG

![Airflow Ingestion](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Airflow-Ingestion.png)

Tasks:
Read raw data
Validate data quality
Generate Great Expectations report
Save valid / invalid data
Trigger alerts on failure


#Prediction DAG

![Airflow Prediction](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Airflow-Prediction.png)

Tasks:
Check for new data
Load trained model
Generate predictions
Store results in PostgreSQL

##✅ Data Validation (Great Expectations)

Schema checks
Null value checks
Categorical domain validation
Numerical range validation
HTML reports generated per run
Severity-based alerts triggered

##📊 Grafana Monitoring
### Ingestion Monitoring Dashboard

![Grafana Ingestion](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Grafana-IngestionDashboard.png)

**Monitors:**
- Total files ingested  
- Valid vs invalid rows  
- Severity over time  

### Prediction & Drift Monitoring

![Grafana Prediction](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Grafana-PredictionDashboard.png)

**Monitors:**
- Predictions per minute  
- Prediction value distribution  
- Feature drift (training vs serving)  

##🚨 Alerting (Microsoft Teams)

### Great Expectations Alerts
![GE Alerts](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Teams-GE-dataAlerts.png)

### Grafana Alerts

![Grafana Alerts](https://raw.githubusercontent.com/Bhavanaramesh-dsa/Flight-price-prediction/main/images/Teams-GrafanaAlerts.png)

##🎯 What This Project Demonstrates

✔ End-to-End MLOps Architecture
✔ Data Quality Engineering
✔ Workflow Automation
✔ Monitoring & Observability
✔ Production-style Pipelines
✔ Real-time Alerting

##🔮 Future Enhancements

Automated model retraining DAG
MLflow experiment tracking
Feature store integration
Cloud deployment (AWS / GCP)
CI/CD pipeline

##👩‍💻 Author

Bhavana Ramesh
Master’s in Data Science & Analytics – EPITA
Paris,France

##📜 License

This project is licensed under the MIT License.
