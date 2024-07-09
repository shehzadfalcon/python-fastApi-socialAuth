"""
Social Authentication Service.

This module provides methods for social authentication and account linking.

Imports:
- HTTPException: FastAPI exception handling for HTTP errors.
- status: HTTP status codes.
- db: Database connection instance.
- AuthHelper: Helper class for authentication operations.
- EErrorMessages: Enum containing error messages.
- EResponseMessages: Enum containing response messages.
- send_email: Function for sending emails.
- EEmailSubjectKeys: Enum containing email subject keys.
- Steps: Enum containing workflow steps.
- datetime: Module for date and time handling.
- LinkAccountDto: Data transfer object for linking accounts.
- time: Module for time-related operations.

Variables:
- user_collection: Collection instance for 'users' in the database.

Classes:
- SocialAuthService: Service class for social authentication operations.

"""

from fastapi import status, HTTPException
from database import db
from services.auth_helper import AuthHelper
from enums.error_messages import EErrorMessages
from services.email import send_email
from enums.email_subject_keys import EEmailSubjectKeys
from enums.steps import Steps
from datetime import datetime
from modules.auth.schemas.link_account import LinkAccountDto
import time
from modules.user.user_service import UserService

# interface
from interfaces.login import ILogin

# Initialize user collection from the database
user_collection = db.get_collection("users")


class SocialAuthService:
    """
    Service class for social authentication operations.

    Methods:
    - social_login: Handles social login authentication.
    - link_account: Handles linking of user accounts from different providers.
    """

    @staticmethod
    async def social_login(email: str, full_name: str, provider_id: str, provider: str) -> ILogin:
        """
        Handles social login authentication.

        Args:
        - email (str): Email address of the user.
        - full_name (str): Full name of the user.
        - provider_id (str): ID of the social provider.
        - provider (str): Name of the social provider.

        Returns:
        - dict: Returns a dictionary containing user and token data upon successful login or account linking initiation.
        """
        user = await user_collection.find_one({"email": email.lower()})

        if not user:
            # Create a new user if not found
            user_data = {
                "fullName": full_name,
                "email": email,
                "providers": [{"providerId": provider_id, "provider": provider}],
                "isActive": True,  # Example default value
            }
            inserted_user = await user_collection.insert_one(user_data)
            updated_user = await user_collection.find_one({"_id": inserted_user.inserted_id})

            # Generating auth token
            token_data = {
                "sub": str(updated_user["_id"]),
                "email": updated_user["email"],
            }
            token = AuthHelper.create_access_token(data=token_data)

            return {"user": UserService.formatUser(updated_user), "token": token}

        else:
            # Check if the social provider exists for the user
            social_provider = next(
                (p for p in user.get("providers", []) if p["providerId"] == provider_id and p["provider"] == provider),
                None,
            )

            if not social_provider:
                # Handle account linking scenario with OTP generation and email sending
                otp = AuthHelper.generate_otp()
                otp_expire_at = AuthHelper.generate_expiry_time()

                # Update user with OTP and OTP expiry time
                await user_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"OTP": otp, "OTPExpireAt": otp_expire_at}},
                )

                # Send email with OTP
                context = {"fullName": user["fullName"], "otp": otp}
                await send_email(
                    user["email"],
                    EEmailSubjectKeys.ACCOUNT_LINKING_SUBJECT,
                    "registration.html",
                    context,
                )

                return {"nextStep": Steps.ACCOUNT_LINKING.value}

            # Generating auth token
            token_data = {"sub": str(user["_id"]), "email": user["email"]}
            token = AuthHelper.create_access_token(data=token_data)

            return {"user": UserService.formatUser(user), "token": token}

    @staticmethod
    async def link_account(link_account_dto: LinkAccountDto) -> ILogin:
        """
        Handles linking of user accounts from different providers.

        Args:
        - link_account_dto (LinkAccountDto): Data transfer object containing account linking information.

        Returns:
        - dict: Returns a dictionary containing user and token data upon successful account linking.
        """
        user = await user_collection.find_one({"email": link_account_dto.email, "OTP": int(link_account_dto.otp)})

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.INVALID_OTP.value)

        otp_expire_at = user["OTPExpireAt"]
        current_time = int(time.time())

        if otp_expire_at > current_time:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EErrorMessages.OTP_EXPIRED.value)

        # Update the user with the new provider
        await user_collection.update_one(
            {
                "_id": user["_id"],
                "providers.provider": {"$ne": link_account_dto.provider},
            },
            {
                "$push": {
                    "providers": {
                        "providerId": link_account_dto.providerId,
                        "provider": link_account_dto.provider,
                    }
                },
                "$set": {"emailVerifiedAt": datetime.utcnow()},
            },
        )

        token_data = {"sub": str(user["_id"]), "email": user["email"]}
        token = AuthHelper.create_access_token(data=token_data)

        # Fetch the updated user data
        user = await user_collection.find_one({"_id": user["_id"]})
        user["_id"] = str(user["_id"])
        return {"user": UserService.formatUser(user), "token": token}
