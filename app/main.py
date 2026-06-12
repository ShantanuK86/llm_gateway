from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router
from app.db.database import engine, Base
import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the FastAPI app starts
    # We tell SQLAlchemy to create the tables in PostgreSQL if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # This runs when the app shuts down

app = FastAPI(title="LLM Gateway", lifespan=lifespan)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
