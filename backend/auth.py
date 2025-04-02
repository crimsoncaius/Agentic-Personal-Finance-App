from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging

from .database import get_db
from .models import User
from .schemas import TokenData

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Add leading slash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    logger.info(f"Creating access token for user data: {data}")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info("Access token created successfully")
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    logger.info("Attempting to get current user from token")
    logger.debug(f"Token received: {token[:10]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.info("Decoding JWT token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token payload: {payload}")

        user_id: int = payload.get("sub")
        if user_id is None:
            logger.error("No user_id found in token")
            raise credentials_exception

        token_data = TokenData(user_id=user_id, email=payload.get("email"))
        logger.info(
            f"Token data extracted: user_id={token_data.user_id}, email={token_data.email}"
        )
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        logger.error(f"No user found for id {token_data.user_id}")
        raise credentials_exception

    logger.info(f"User found: id={user.id}, email={user.email}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    logger.info(f"Checking if user {current_user.id} is active")
    if not current_user:
        logger.error(f"User {current_user.id} is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
