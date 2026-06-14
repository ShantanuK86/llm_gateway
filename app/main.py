from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router
from app.db.database import engine, Base, AsyncSessionLocal
from app.models.domain import User, ApiKey
from sqlalchemy.future import select
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the FastAPI app starts
    # We tell SQLAlchemy to create the tables in PostgreSQL if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed a test user and API key so we can test the gateway
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "test_user"))
        user = result.scalars().first()
        if not user:
            logger.info("Seeding test user into database...")
            user = User(username="test_user", email="test@example.com")
            session.add(user)
            await session.commit()
            
            api_key = ApiKey(key="test_api_key_123", user_id=user.id)
            session.add(api_key)
            await session.commit()
            logger.info("Test user seeded! Use Authorization: test_api_key_123")
            
    yield
    # This runs when the app shuts down

# Initialize OpenTelemetry Tracing
# This provider manages the creation of traces
provider = TracerProvider()
# We use ConsoleSpanExporter to print the traces directly to the terminal for learning!
# In production, you would export this to Jaeger, Datadog, or New Relic.
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

app = FastAPI(title="LLM Gateway", lifespan=lifespan)

# 1. Instrument FastAPI to automatically trace incoming requests
FastAPIInstrumentor.instrument_app(app)

# 2. Instrument HTTPX to automatically trace outgoing requests (to OpenAI/Gemini)
HTTPXClientInstrumentor().instrument()

app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "LLM Gateway is running successfully! 🚀",
        "documentation": "Visit http://localhost:8000/docs to view the interactive API",
        "status": "online"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
