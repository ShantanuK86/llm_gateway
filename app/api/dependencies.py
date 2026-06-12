from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.domain import ApiKey, User

# We expect the client to pass their API key in the "Authorization" header
# (In a real app, you might use 'Bearer <token>' or a custom header like 'x-api-key')
api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

async def get_current_user(
    header_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts the API key from the request header,
    validates it against the database, and returns the associated User.
    """
    # If using Bearer token, we strip the 'Bearer ' prefix
    actual_key = header_key.replace("Bearer ", "") if header_key.startswith("Bearer ") else header_key

    # Query the database for the active API key
    stmt = select(ApiKey).where(ApiKey.key == actual_key, ApiKey.is_active == True)
    result = await db.execute(stmt)
    api_key_record = result.scalars().first()

    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # Get the user associated with this key
    stmt_user = select(User).where(User.id == api_key_record.user_id)
    user_result = await db.execute(stmt_user)
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
