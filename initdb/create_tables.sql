-- ==============================================
-- DSP: PREDICTIONS DATABASE INITIAL SCHEMA
-- ==============================================

\connect predictions;

-- ------------------------------------------------
-- 1. Prediction logs (FastAPI)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS prediction (
    id SERIAL PRIMARY KEY,
    source TEXT,
    features JSONB NOT NULL,
    prediction NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------
-- 2. Training stats (Grafana drift monitoring)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS training_stats (
    id SERIAL PRIMARY KEY,
    duration_mean NUMERIC NOT NULL,
    duration_std NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------
-- 3. Ingestion stats (ingestion_dag)
-- REQUIRED FIX → contains "success" BOOLEAN
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS ingestion_stats (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    n_rows INTEGER NOT NULL,
    n_valid INTEGER NOT NULL,
    n_invalid INTEGER NOT NULL,
    severity TEXT,
    report_path TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    success BOOLEAN DEFAULT false         -- <== REQUIRED BY DAG
);

-- ------------------------------------------------
-- 4. Row-level issues (data_issues)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS data_issues (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------
-- 5. Processed file tracking (prediction_dag)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS processed_files (
    id SERIAL PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------
-- 6. Prediction runs (success/fail tracking)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS prediction_runs (
    id SERIAL PRIMARY KEY,
    filename TEXT,
    n_rows INTEGER,
    source TEXT DEFAULT 'scheduled',
    status TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);