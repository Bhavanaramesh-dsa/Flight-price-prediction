import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Date, DateTime, Numeric, Text, SmallInteger, func
from pydantic import BaseSettings
from dotenv import load_dotenv



# CONFIG & SETTINGS

class config:
    env_file = ".env"


load_dotenv(config.env_file)  


class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "Password"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/predictions"


settings = Settings()
print(f"[DEBUG] Loaded DATABASE_URL: {settings.DATABASE_URL}")



# DATABASE SETUP

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()



# MODEL

class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    airline = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    destination = Column(Text, nullable=False)
    total_stops = Column(SmallInteger, nullable=False)
    date_of_journey = Column(Date, nullable=False)
    dep_datetime = Column(DateTime(timezone=False), nullable=False)
    arrival_datetime = Column(DateTime(timezone=False), nullable=False)
    duration_mins = Column(Integer, nullable=False)
    raw_duration = Column(Text)
    predicted_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


# ASYNC SESSION GENERATOR

async def get_db():
    print("[DEBUG] Entered get_db()")
    async with SessionLocal() as db:
        try:
            print("[DEBUG] Yielding DB session")
            yield db
        finally:
            print("[DEBUG] Closing DB session")
            await db.close()



# ASYNC DB CREATION HELPER
async def init_db():
    print("[DEBUG] Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DEBUG] Database initialized successfully ✅")


# Run DB creation on import (optional)
if __name__ == "__main__":
    asyncio.run(init_db())
