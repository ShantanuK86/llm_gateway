from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Create the async engine connected to PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Session factory for generating new database sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for our SQLAlchemy models
Base = declarative_base()

# Dependency to get the DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
