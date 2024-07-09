# app/services/auth_helper.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from database import db

import os
import random

user_collection = db.get_collection("users")


class AuthHelper:
    """
    Helper class for handling authentication-related tasks such as password hashing,
    token generation, and user authentication.

    This class includes methods to:
    - Generate a one-time password (OTP)
    - Generate an expiry time for OTP
    - Verify a plain password against a hashed password
    - Hash a plain password
    - Create a JWT access token
    - Authenticate a user by their email and password

    Attributes:
        SECRET_KEY (str): Secret key for JWT encoding.
        ALGORITHM (str): Algorithm used for JWT encoding.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Expiration time for access tokens in minutes.
        pwd_context (CryptContext): Password context for hashing and verifying passwords.
        oauth2_scheme (OAuth2PasswordBearer): OAuth2PasswordBearer instance for token URL.
    """

    SECRET_KEY = os.getenv("JWT_TOKEN_SECRET")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    @staticmethod
    def generate_otp() -> int:
        """
        Generate a 4-digit OTP (One-Time Password).

        Returns:
            int: A 4-digit OTP.
        """
        otp = random.randint(1000, 9999)  # Generate a 4-digit OTP
        return int(otp)

    @staticmethod
    def generate_expiry_time(minutes: int = 10) -> int:
        """
        Generate an expiry time in the form of a timestamp.

        Args:
            minutes (int, optional): Number of minutes until the expiry time. Defaults to 10.

        Returns:
            int: Expiry timestamp.
        """
        expiry_datetime = datetime.utcnow() + timedelta(minutes=minutes)
        expiry_timestamp = int(expiry_datetime.timestamp())
        return expiry_timestamp

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.

        Args:
            plain_password (str): The plain password to verify.
            hashed_password (str): The hashed password to verify against.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return AuthHelper.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a plain password.

        Args:
            password (str): The plain password to hash.

        Returns:
            str: The hashed password.
        """
        return AuthHelper.pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            data (dict): The data to encode in the token.
            expires_delta (Optional[timedelta], optional): The time delta until the token expires. Defaults to None.

        Returns:
            str: The encoded JWT token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=1440)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, AuthHelper.SECRET_KEY, algorithm=AuthHelper.ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[dict]:
        """
        Authenticate a user by email and password.

        Args:
            email (str): The user's email.
            password (str): The user's password.

        Returns:
            Optional[dict]: The user's data if authentication is successful, None otherwise.
        """
        user = await user_collection.find_one({"email": email})
        if not user or not AuthHelper.verify_password(password, user.get("password")):
            return None
        return user
