from sqlalchemy import Column, Integer, String, Float, JSON, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ---------------------------------------------------------
# prediction table (FastAPI writes here)
# ---------------------------------------------------------
class Prediction(Base):
    __tablename__ = "prediction"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=True)
    features = Column(JSONB, nullable=False)
    prediction = Column(Float, nullable=False)
    created_at = Column(
        TIMESTAMP, server_default=text("NOW()"), nullable=False
    )


# ---------------------------------------------------------
# ingestion_stats (used by ingestion_dag → save_stats)
# ---------------------------------------------------------
class IngestionStat(Base):
    __tablename__ = "ingestion_stats"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    n_rows = Column(Integer)
    n_valid = Column(Integer)
    n_invalid = Column(Integer)
    success = Column(String)     # Airflow DAG logs True/False as string
    severity = Column(String)
    report_path = Column(String)
    created_at = Column(
        TIMESTAMP, server_default=text("NOW()"), nullable=False
    )


# ---------------------------------------------------------
# data_issues (optional from ingestion, safe to include)
# ---------------------------------------------------------
class DataIssue(Base):
    __tablename__ = "data_issues"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    issue_type = Column(String)
    severity = Column(String)
    details = Column(JSONB)
    created_at = Column(
        TIMESTAMP, server_default=text("NOW()"), nullable=False
    )


# ---------------------------------------------------------
# processed_files (used by prediction_dag)
# ---------------------------------------------------------
class ProcessedFile(Base):
    __tablename__ = "processed_files"

    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True)
    processed_at = Column(
        TIMESTAMP, server_default=text("NOW()"), nullable=False
    )


# ---------------------------------------------------------
# training_stats — used by Grafana drift panel
# ---------------------------------------------------------
class TrainingStats(Base):
    __tablename__ = "training_stats"

    id = Column(Integer, primary_key=True)
    duration_mean = Column(Float, nullable=False)
    duration_std = Column(Float, nullable=False)
    created_at = Column(
        TIMESTAMP, server_default=text("NOW()"), nullable=False
    )