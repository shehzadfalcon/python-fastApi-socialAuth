"""
Authentication service functions.

This module provides functions for user authentication, registration, email verification,
password management (forgot, reset), OTP handling, and associated database operations.

Functions:
- identify_user(email: str): Identify a user by email.
- register_user(user_dict: dict): Register a new user.
- login_user(email: str, password: str): Log in a user.
- verify_user_email(email: str, otp: int, is_verify_email: bool): Verify user's email using OTP.
- handle_forgot_password(email: str): Handle the forgot password process.
- handle_resend_otp(email: str): Resend OTP to the user's email.
- handle_reset_password(email: str, otp: int, new_password: str): Reset user's password using email and OTP.

"""

# FastAPI status codes
from fastapi import status, HTTPException

# Database connection
from database import db

# Datetime module for handling timestamps
from datetime import datetime, timezone

# Email service for sending emails
from services.email import send_email

# Enums for error messages, response messages, email subjects, and steps
from enums.error_messages import EErrorMessages
from enums.email_subject_keys import EEmailSubjectKeys
from enums.steps import Steps

# Authentication helper service
from services.auth_helper import AuthHelper

# User service module for user-related operations
from modules.user.user_service import UserService

# BSON ObjectId for MongoDB
from bson import ObjectId

# Time module for handling timestamps
import time
from modules.auth.schemas.reset_password import ResetPasswordSchema

# interface
from interfaces.login import ILogin
from modules.user.user_model import EUserRole

# MongoDB collection for users
user_collection = db.get_collection("users")


class AuthService:
    @staticmethod
    async def identify_user(email: str) -> ILogin:
        """
        Identify a user by email.

        Args:
        - email (str): Email address of the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one({"email": email.lower()})
        if not user:
            return {"nextStep": Steps.USER_REGISTER.value}

        if user and not user.get("emailVerifiedAt"):
            otp = AuthHelper.generate_otp()
            otp_expire_at = AuthHelper.generate_expiry_time()
            context = {"fullName": user["fullName"], "otp": otp}
            await send_email(
                user["email"],
                EEmailSubjectKeys.REGISTER_EMAIL_SUBJECT,
                "registration.html",
                context,
            )
            await user_collection.update_one(
                {"_id": ObjectId(user["_id"])},
                {"$set": {"OTP": otp, "OTPExpireAt": otp_expire_at}},
            )
            return {"nextStep": Steps.VERIFY_EMAIL.value}

        return {"nextStep": Steps.SET_PASSWORD.value}

    @staticmethod
    async def register_user(user_dict: dict) -> None:
        """
        Register a new user.

        Args:
        - user_dict (dict): Dictionary containing user information.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        find_user = await user_collection.find_one({"email": user_dict.get("email")})
        if find_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EErrorMessages.USER_ALREADY_EXISTS.value)

        otp = AuthHelper.generate_otp()
        otp_expire_at = AuthHelper.generate_expiry_time()
        user_dict["OTP"] = otp
        user_dict["role"] = EUserRole.USER
        user_dict["isActive"] = True

        user_dict["OTPExpireAt"] = otp_expire_at
        user_dict["password"] = AuthHelper.get_password_hash(user_dict.get("password"))

        result = await user_collection.insert_one(user_dict)
        user = await user_collection.find_one({"_id": result.inserted_id})

        context = {"fullName": user["fullName"], "otp": otp}
        await send_email(
            user["email"],
            EEmailSubjectKeys.REGISTER_EMAIL_SUBJECT,
            "registration.html",
            context,
        )

    @staticmethod
    async def login_user(email: str, password: str) -> ILogin:
        """
        Log in a user.

        Args:
        - email (str): Email address of the user.
        - password (str): Password of the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one({"email": email.lower()})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.USER_NOT_EXISTS.value)

        if not user.get("emailVerifiedAt"):
            otp = AuthHelper.generate_otp()
            otp_expire_at = AuthHelper.generate_expiry_time()
            context = {"fullName": user["fullName"], "otp": otp}
            await send_email(
                user["email"],
                EEmailSubjectKeys.REGISTER_EMAIL_SUBJECT,
                "registration.html",
                context,
            )
            await user_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"OTP": otp, "OTPExpireAt": otp_expire_at}},
            )
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=EErrorMessages.USER_NOT_VERIFIED.value)

        is_correct = await AuthHelper.authenticate_user(email, password)
        if not is_correct:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EErrorMessages.INVALID_PASSWORD.value)

        token_data = {"sub": str(user["_id"]), "email": user["email"]}
        token = AuthHelper.create_access_token(data=token_data)

        return {"user": UserService.formatUser(user), "token":{"token":token}}

    @staticmethod
    async def verify_user_email(email: str, otp: int, is_verify_email: bool) -> ILogin:
        """
        Verify user's email using OTP.

        Args:
        - email (str): Email address of the user.
        - otp (int): OTP sent to the user's email for verification.
        - is_verify_email (bool): Flag indicating whether to verify the email.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one(
            {
                "$and": [
                    {"OTP": int(otp)},
                    {"email": email.lower()},
                ]
            }
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.INVALID_OTP.value)

        otp_expire_at = user["OTPExpireAt"]
        current_time = int(time.time())
        if otp_expire_at > current_time:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EErrorMessages.OTP_EXPIRED.value)

        token_data = {"sub": str(user["_id"]), "email": user["email"]}
        token = AuthHelper.create_access_token(data=token_data)

        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"emailVerifiedAt": datetime.now(timezone.utc)}},
        )

        if is_verify_email:
            context = {"fullName": user["fullName"]}
            await send_email(
                user["email"],
                EEmailSubjectKeys.WELCOME_SUBJECT,
                "welcome.html",
                context,
            )

            if not "password" in user:
                return {"nextStep": Steps.SETUP_PASSWORD.value}
        user["_id"] = str(user["_id"])
        return {"user": UserService.formatUser(user), "token":{"token":token}}

    @staticmethod
    async def handle_forgot_password(email: str) -> None:
        """
        Handle the forgot password process.

        Args:
        - email (str): Email address of the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one(
            {"email": email.lower()},
        )

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.USER_NOT_EXISTS.value)

        if not user.get("emailVerifiedAt"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EErrorMessages.USER_NOT_VERIFIED.value)

        OTP = AuthHelper.generate_otp()
        OTPExpireAt = AuthHelper.generate_expiry_time()
        context = {"fullName": user["fullName"], "otp": OTP}
        await send_email(
            user["email"],
            EEmailSubjectKeys.FORGOT_PASSWORD_EMAIL_SUBJECT,
            "forgot_password.html",
            context,
        )
        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"OTP": OTP, "OTPExpireAt": OTPExpireAt}},
        )

    @staticmethod
    async def handle_resend_otp(email: str) -> None:
        """
        Resend OTP to the user's email.

        Args:
        - email (str): Email address of the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one({"email": email.lower()})

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.USER_NOT_EXISTS.value)

        OTP = AuthHelper.generate_otp()
        OTPExpireAt = AuthHelper.generate_expiry_time()
        context = {"fullName": user["fullName"], "otp": OTP}
        await send_email(
            user["email"],
            EEmailSubjectKeys.RESEND_OTP_EMAIL_SUBJECT,
            "forgot_password.html",
            context,
        )
        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"OTP": OTP, "OTPExpireAt": OTPExpireAt}},
        )

    @staticmethod
    async def handle_reset_password(reset_password:ResetPasswordSchema) -> None:
        """
        Reset user's password using email and OTP.

        Args:
        - email (str): Email address of the user.
        - otp (int): OTP sent to the user's email for verification.
        - new_password (str): New password to be set for the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user =None
        if "otp" in dict(reset_password) and reset_password.otp:
             user = await user_collection.find_one({"OTP": int(reset_password.otp)})
        elif "email" in dict(reset_password) and reset_password.email:
             user = await user_collection.find_one({"email": reset_password.email})
 

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.INVALID_OTP.value)

        otp_expire_at = user["OTPExpireAt"]
        current_time = int(time.time())
        if otp_expire_at > current_time:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EErrorMessages.OTP_EXPIRED.value)

        hashed_password = AuthHelper.get_password_hash(reset_password.password)
        await user_collection.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$set": {"password": hashed_password}},
        )
