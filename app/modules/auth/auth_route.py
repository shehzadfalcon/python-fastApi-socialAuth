# app/routes/auth.py

from fastapi import APIRouter, HTTPException, Depends, status
from app.database import db
from app.models.users import User
from datetime import datetime, timezone

# validation schema
from app.validations.register import RegisterSchema
from app.validations.login import LoginSchema
from app.validations.verify_email import VerifyEmailSchema
from app.validations.forgot_password import ForgotPasswordSchema
from app.validations.reset_password import ResetPasswordSchema
from app.validations.identify import IdentifyDto
from app.services.email import send_email


from app.enums.error_messages import EErrorMessages
from app.enums.response_messages import EResponseMessages
from app.enums.email_subject_keys import EEmailSubjectKeys


from app.enums.steps import Steps

# from app.interfaces.login import ILogin
from app.interfaces.response import IResponse


import time
from app.services.auth_helper import AuthHelper
from bson import ObjectId

user_collection = db.get_collection("users")
router = APIRouter()


@router.post("/identify", response_model=IResponse)
async def identify(identify_dto: IdentifyDto):
    try:
        email = str(identify_dto.email)
        user = await user_collection.find_one({"email": email.lower()})
        if not user:
            return {
                "statusCode": status.HTTP_200_OK,
                "payload": {"nextStep": Steps.USER_REGISTER},
            }

        if user and not user.get("emailVerifiedAt"):
            otp = AuthHelper.generate_otp()
            otp_expire_at = AuthHelper.generate_expiry_time()
            context = {"fullName": user["fullName"], "otp": otp}
            await send_email(
                user["email"], 
                EEmailSubjectKeys.REGISTER_EMAIL_SUBJECT, 
                "registration.html", 
                context
            )
            await user_collection.update_one(
                {"_id": ObjectId(user["_id"])},
                {"$set": {"OTP": otp, "OTPExpireAt": otp_expire_at}},
            )
            return {
                "statusCode": status.HTTP_200_OK,
                "payload": {"nextStep": Steps.VERIFY_EMAIL},
            }

        return {
            "statusCode": status.HTTP_200_OK,
            "payload": {"nextStep": Steps.SET_PASSWORD},
        }
    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }


@router.post("/register", response_model=IResponse)
async def register(form_data: RegisterSchema):
    try:
        user_dict = form_data.dict()
        find_user = await user_collection.find_one({"email": user_dict.get("email")})
        if find_user:
            return {
                "statusCode": status.HTTP_409_CONFLICT,
                "message": EErrorMessages.USER_ALREADY_EXISTS,
            }
       
        otp = AuthHelper.generate_otp()
        otp_expire_at = AuthHelper.generate_expiry_time()
        user_dict["OTP"]= otp
        user_dict["OTPExpireAt"]= otp_expire_at
        user_dict["password"] = AuthHelper.get_password_hash(user_dict.get("password"))

        
        result = await user_collection.insert_one(user_dict)
        user=await user_collection.find_one({"_id": result.inserted_id})

        context = {"fullName": user["fullName"], "otp": otp}
        await send_email(
            user["email"], 
            EEmailSubjectKeys.REGISTER_EMAIL_SUBJECT, 
            "registration.html", 
            context
        )
        return {
            "statusCode": status.HTTP_200_OK,
            "message": EResponseMessages.USER_CREATED,
        }
    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }


@router.post("/login", response_model=IResponse)
async def login(login_dto: LoginSchema):
    try:
        # Check if a user with the provided email exists
        user = await user_collection.find_one({"email": login_dto.email.lower()})

        if not user:
            return {
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": EErrorMessages.USER_NOT_EXISTS,
            }

        # Check if the user is verified via OTP
        if not user.get("emailVerifiedAt"):
            otp = AuthHelper.generate_otp()
            otp_expire_at = AuthHelper.generate_expiry_time()
            context = {"fullName": user["fullName"], "otp": otp}
            await send_email(
                user["email"], 
                EEmailSubjectKeys.REGISTER_EMAIL_SUBJECT, 
                "registration.html", 
                context
            )
            await user_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"OTP": otp, "OTPExpireAt": otp_expire_at}},
            )

            return {
                "statusCode": status.HTTP_406_NOT_ACCEPTABLE,
                "message": EErrorMessages.USER_NOT_VERIFIED,
            }

        # Check Password
        is_correct = await AuthHelper.authenticate_user(
            login_dto.email, user["password"]
        )
        if not is_correct:
            return {
                "statusCode": status.HTTP_409_CONFLICT,
                "message": EErrorMessages.INVALID_PASSWORD,
            }

        # Generating auth token
        token_data = {"sub": str(user["_id"]), "email": user["email"]}
        token = AuthHelper.create_access_token(data=token_data)

        return {
            "statusCode": status.HTTP_200_OK,
            "message": EResponseMessages.USER_LOGIN,
            "payload": {"user": user, "token": {token}},
        }
    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }


@router.post("/verify-email", response_model=IResponse)
async def verify_email(verify_email_dto: VerifyEmailSchema):
    try:
        OTP = int(verify_email_dto.otp)
        user = await user_collection.find_one(
            {
                "$and": [
                    {"OTP": OTP},
                    {"email": verify_email_dto.email.lower()},
                ]
            }
        )

        if not user:
            return {
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": EErrorMessages.INVALID_OTP,
            }

        # Compare with current time in seconds

        otp_expire_at = user["OTPExpireAt"]
        current_time = int(time.time())
        if otp_expire_at > current_time:
            return {
                "statusCode": status.HTTP_409_CONFLICT,
                "message": EErrorMessages.OTP_EXPIRED,
            }

        token_data = {"sub": str(user["_id"]), "email": user["email"]}
        token = AuthHelper.create_access_token(data=token_data)

        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"emailVerifiedAt": datetime.now(timezone.utc)}},
        )

        if verify_email_dto.isVerifyEmail:
              context = {"fullName": user["fullName"]}
              await send_email(
                    user["email"], 
                    EEmailSubjectKeys.WELCOME_SUBJECT, 
                    "welcome.html",
                    context
                )

        if not user["password"]:
            return {
                "statusCode": status.HTTP_200_OK,
                "payload": {"nextStep": Steps.SETUP_PASSWORD},
            }

        return {
            "statusCode": status.HTTP_200_OK,
            "payload": {"user": user, "token": {token}},
        }
    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }


@router.post("/forgot-password", response_model=IResponse)
async def forgot_password(forgot_password: ForgotPasswordSchema):
    try:
        user = await user_collection.find_one(
            {"email": forgot_password.email.lower()},
            {"_id": 1, "fullName": 1, "emailVerifiedAt": 1},
        )

        if not user:
            return {
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": EErrorMessages.USER_NOT_EXISTS,
            }

        if not user.get("emailVerifiedAt"):
            return {
                "statusCode": status.HTTP_409_CONFLICT,
                "message": EErrorMessages.USER_NOT_VERIFIED,
            }

        OTP = AuthHelper.generate_otp()
        OTPExpireAt = AuthHelper.generate_expiry_time()
        context = {"fullName": user["fullName"], "otp": OTP}
        await send_email(
                    user["email"], 
                    EEmailSubjectKeys.FORGOT_PASSWORD_EMAIL_SUBJECT, 
                    "forgot_password.html", 
                    context
                )
        await user_collection.update_one(
            {"_id": user["_id"]}, {"$set": {"OTP": OTP, "OTPExpireAt": OTPExpireAt}}
        )

        return {
            "statusCode": status.HTTP_200_OK,
            "message": EResponseMessages.PASSWORD_RESET_EMAIL,
        }
    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }


@router.post("/resend-otp", response_model=IResponse)
async def resend_otp(resend_otp: ForgotPasswordSchema):
    try:
        user = await user_collection.find_one(
            {"email": resend_otp.email.lower()},
            {"_id": 1, "fullName": 1, "emailVerifiedAt": 1},
        )

        if not user:
            return {
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": EErrorMessages.USER_NOT_EXISTS,
            }

        OTP = AuthHelper.generate_otp()
        OTPExpireAt = AuthHelper.generate_expiry_time()
        context = {"fullName": user["fullName"], "otp": OTP}
        await send_email(
                    user["email"], 
                    EEmailSubjectKeys.RESEND_OTP_EMAIL_SUBJECT, 
                    "forgot_password.html", 
                    context
                )
        await user_collection.update_one(
            {"_id": user["_id"]}, {"$set": {"OTP": OTP, "OTPExpireAt": OTPExpireAt}}
        )

        return {
            "statusCode": status.HTTP_200_OK,
            "message": EResponseMessages.OTP_RESEND,
        }
    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }


@router.post("/reset-password", response_model=IResponse)
async def reset_password(reset_password: ResetPasswordSchema):
    try:

        user = None

        if reset_password.otp:
            user = await user_collection.find_one(
                {"OTP": int(reset_password.otp)},
            )

        if reset_password.email and not user:
            user = await user_collection.find_one(
                {"email": reset_password.email.lower()},
            )

        if not user:
            return {
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": EErrorMessages.INVALID_OTP,
            }

        otp_expire_at = user["OTPExpireAt"]
        current_time = int(time.time())

        if otp_expire_at > current_time:
            return {
                "statusCode": status.HTTP_409_CONFLICT,
                "message": EErrorMessages.OTP_EXPIRED,
            }

        hashed_password = AuthHelper.get_password_hash(reset_password.password)

        await user_collection.update_one(
            {"_id": ObjectId(user["_id"])}, {"$set": {"password": hashed_password}}
        )
        context = {"fullName": user["fullName"]}
        await send_email(
                    user["email"], 
                    EEmailSubjectKeys.PASSWORD_RESET_CONFIRMATION_EMAIL_SUBJECT, 
                    "password_reset_confirmation.html", 
                    context
                )
        return {
            "statusCode": status.HTTP_200_OK,
            "message": EResponseMessages.PASSWORD_UPDATED,
        }
    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }
