import jwt
from datetime import datetime, timedelta
from typing import Dict
import os
from database.connection import get_db

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def generate_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_tokens(user_id: str) -> Dict[str, str]:
    return {
        "access_token": generate_access_token(user_id),
        "refresh_token": generate_refresh_token(user_id)
    }

async def is_token_blacklisted(token: str) -> bool:
    db = await get_db()
    blacklisted = await db.blacklistedtoken.find_unique(
        where={"token": token}
    )
    return blacklisted is not None

async def verify_token(token: str) -> Dict:
    try:
        # Check if token is blacklisted
        if await is_token_blacklisted(token):
            raise ValueError("Token has been revoked")
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")