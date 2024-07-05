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

from fastapi import status
from app.database import db
from datetime import datetime, timezone
from app.services.email import send_email
from app.enums.error_messages import EErrorMessages
from app.enums.response_messages import EResponseMessages
from app.enums.email_subject_keys import EEmailSubjectKeys
from app.enums.steps import Steps
from app.services.auth_helper import AuthHelper
from bson import ObjectId
import time
from app.utils.create_response import create_response

user_collection = db.get_collection("users")


class AuthService:
    @staticmethod
    async def identify_user(email: str):
        """
        Identify a user by email.

        Args:
        - email (str): Email address of the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one({"email": email.lower()})
        if not user:
            return create_response(
                status.HTTP_404_NOT_FOUND,
                EErrorMessages.USER_NOT_EXISTS,
                {"nextStep": Steps.USER_REGISTER},
            )

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
            return create_response(status.HTTP_200_OK, None, {"nextStep": Steps.VERIFY_EMAIL})

        return create_response(status.HTTP_200_OK, None, {"nextStep": Steps.SET_PASSWORD})

    @staticmethod
    async def register_user(user_dict: dict):
        """
        Register a new user.

        Args:
        - user_dict (dict): Dictionary containing user information.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        find_user = await user_collection.find_one({"email": user_dict.get("email")})
        if find_user:
            return create_response(
                status.HTTP_409_CONFLICT,
                EErrorMessages.USER_ALREADY_EXISTS,
            )

        otp = AuthHelper.generate_otp()
        otp_expire_at = AuthHelper.generate_expiry_time()
        user_dict["OTP"] = otp
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
        return create_response(status.HTTP_200_OK, EResponseMessages.USER_CREATED)

    @staticmethod
    async def login_user(email: str, password: str):
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
            return create_response(status.HTTP_404_NOT_FOUND, EErrorMessages.USER_NOT_EXISTS)

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
            return create_response(
                status.HTTP_406_NOT_ACCEPTABLE,
                EErrorMessages.USER_NOT_VERIFIED,
            )

        is_correct = await AuthHelper.authenticate_user(email, user["password"])
        if not is_correct:
            return create_response(status.HTTP_409_CONFLICT, EErrorMessages.INVALID_PASSWORD)

        token_data = {"sub": str(user["_id"]), "email": user["email"]}
        token = AuthHelper.create_access_token(data=token_data)

        return create_response(
            status.HTTP_200_OK,
            EResponseMessages.USER_LOGIN,
            {"user": user, "token": token},
        )

    @staticmethod
    async def verify_user_email(email: str, otp: int, is_verify_email: bool):
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
                    {"OTP": otp},
                    {"email": email.lower()},
                ]
            }
        )

        if not user:
            return create_response(status.HTTP_404_NOT_FOUND, EErrorMessages.INVALID_OTP)

        otp_expire_at = user["OTPExpireAt"]
        current_time = int(time.time())
        if otp_expire_at > current_time:
            return create_response(status.HTTP_409_CONFLICT, EErrorMessages.OTP_EXPIRED)

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

        if not user["password"]:
            return create_response(status.HTTP_200_OK, None, {"nextStep": Steps.SETUP_PASSWORD})

        return create_response(status.HTTP_200_OK, None, {"user": user, "token": token})

    @staticmethod
    async def handle_forgot_password(email: str):
        """
        Handle the forgot password process.

        Args:
        - email (str): Email address of the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one(
            {"email": email.lower()},
            {"_id": 1, "fullName": 1, "emailVerifiedAt": 1},
        )

        if not user:
            return create_response(status.HTTP_404_NOT_FOUND, EErrorMessages.USER_NOT_EXISTS)

        if not user.get("emailVerifiedAt"):
            return create_response(
                status.HTTP_409_CONFLICT,
                EErrorMessages.USER_NOT_VERIFIED,
            )

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

        return create_response(status.HTTP_200_OK, EResponseMessages.PASSWORD_RESET_EMAIL)

    @staticmethod
    async def handle_resend_otp(email: str):
        """
        Resend OTP to the user's email.

        Args:
        - email (str): Email address of the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one({"email": email.lower()})

        if not user:
            return create_response(status.HTTP_404_NOT_FOUND, EErrorMessages.USER_NOT_EXISTS)

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

        return create_response(status.HTTP_200_OK, EResponseMessages.OTP_RESEND)

    @staticmethod
    async def handle_reset_password(email: str, otp: int, new_password: str):
        """
        Reset user's password using email and OTP.

        Args:
        - email (str): Email address of the user.
        - otp (int): OTP sent to the user's email for verification.
        - new_password (str): New password to be set for the user.

        Returns:
        - dict: Response dictionary with statusCode, message, and payload fields.
        """
        user = await user_collection.find_one({"email": email.lower(), "OTP": otp})

        if not user:
            return create_response(status.HTTP_404_NOT_FOUND, EErrorMessages.INVALID_OTP)

        otp_expire_at = user["OTPExpireAt"]
        current_time = int(time.time())
        if otp_expire_at > current_time:
            return create_response(status.HTTP_409_CONFLICT, EErrorMessages.OTP_EXPIRED)

        hashed_password = AuthHelper.get_password_hash(new_password)
        await user_collection.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$set": {"password": hashed_password}},
        )
        return create_response(status.HTTP_200_OK, EResponseMessages.PASSWORD_RESET)
