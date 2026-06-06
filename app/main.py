from fastapi import FastAPI
from app.api.routes import router
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LLM Gateway")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
