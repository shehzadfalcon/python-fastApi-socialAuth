# app/services/auth_helper.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import random
from app.database import db
from app.enums.error_messages import EErrorMessages

import os

user_collection = db.get_collection("users")


class AuthHelper:
    SECRET_KEY = os.getenv("JWT_TOKEN_SECRET")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    @staticmethod
    def generate_otp() -> int:
        otp = random.randint(1000, 9999)  # Generate a 4-digit OTP
        return int(otp)

    @staticmethod
    def generate_expiry_time(minutes: int = 10) -> int:
        expiry_datetime = datetime.utcnow() + timedelta(minutes=minutes)
        expiry_timestamp = int(expiry_datetime.timestamp())
        return expiry_timestamp

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return AuthHelper.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return AuthHelper.pwd_context.hash(password)

    @staticmethod
    def create_access_token(data, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, AuthHelper.SECRET_KEY, algorithm=AuthHelper.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[dict]:
        user = await user_collection.find_one({"email": email})
        if not user or not AuthHelper.verify_password(password, user.get("password")):
            return
        return user

    @staticmethod
    async def get_authenticated_user(
        token: str = Depends(oauth2_scheme),
    ) -> Optional[dict]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, AuthHelper.SECRET_KEY, algorithms=[AuthHelper.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = await user_collection.find_one({"email": username})
        if user is None:
            raise credentials_exception
        return user
