from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

# Load .env
load_dotenv()

#  Default DB config
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Password")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "predictions")

#  Create database connection string
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ✅ Initialize engine
engine = create_engine(DATABASE_URL, echo=False, future=True)

print(f"[DEBUG] Using DATABASE_URL: {DATABASE_URL}")
print(f"[DEBUG] Engine created successfully: {engine}")
