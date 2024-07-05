# app/services/auth_service.py
from fastapi import  status
from app.database import db
from app.models.users import User
from datetime import datetime, timezone
from app.services.email import send_email
from app.enums.error_messages import EErrorMessages
from app.enums.response_messages import EResponseMessages
from app.enums.email_subject_keys import EEmailSubjectKeys
from app.enums.steps import Steps
from app.services.auth_helper import AuthHelper
from bson import ObjectId
import time

user_collection = db.get_collection("users")

async def identify_user(email: str):
    user = await user_collection.find_one({"email": email.lower()})
    if not user:
        return {
            "statusCode": status.HTTP_404_NOT_FOUND,
            "message": EErrorMessages.USER_NOT_EXISTS,
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
            "message": None,
            "payload": {"nextStep": Steps.VERIFY_EMAIL},
        }

    return {
        "statusCode": status.HTTP_200_OK,
        "message": None,
        "payload": {"nextStep": Steps.SET_PASSWORD},
    }

async def register_user(user_dict: dict):
    find_user = await user_collection.find_one({"email": user_dict.get("email")})
    if find_user:
        return {
            "statusCode": status.HTTP_409_CONFLICT,
            "message": EErrorMessages.USER_ALREADY_EXISTS,
            "payload": None,
        }

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
        context
    )
    return {
        "statusCode": status.HTTP_200_OK,
        "message": EResponseMessages.USER_CREATED,
        "payload": None,
    }

async def login_user(email: str, password: str):
    user = await user_collection.find_one({"email": email.lower()})
    if not user:
        return {
            "statusCode": status.HTTP_404_NOT_FOUND,
            "message": EErrorMessages.USER_NOT_EXISTS,
            "payload": None,
        }

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
            "payload": None,
        }

    is_correct = await AuthHelper.authenticate_user(email, user["password"])
    if not is_correct:
        return {
            "statusCode": status.HTTP_409_CONFLICT,
            "message": EErrorMessages.INVALID_PASSWORD,
            "payload": None,
        }

    token_data = {"sub": str(user["_id"]), "email": user["email"]}
    token = AuthHelper.create_access_token(data=token_data)

    return {
        "statusCode": status.HTTP_200_OK,
        "message": EResponseMessages.USER_LOGIN,
        "payload": {"user": user, "token": token},
    }

async def verify_user_email(email: str, otp: int, is_verify_email: bool):
    user = await user_collection.find_one(
        {"$and": [
            {"OTP": otp},
            {"email": email.lower()},
        ]}
    )

    if not user:
        return {
            "statusCode": status.HTTP_404_NOT_FOUND,
            "message": EErrorMessages.INVALID_OTP,
            "payload": None,
        }

    otp_expire_at = user["OTPExpireAt"]
    current_time = int(time.time())
    if otp_expire_at > current_time:
        return {
            "statusCode": status.HTTP_409_CONFLICT,
            "message": EErrorMessages.OTP_EXPIRED,
            "payload": None,
        }

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
            context
        )

    if not user["password"]:
        return {
            "statusCode": status.HTTP_200_OK,
            "message": None,
            "payload": {"nextStep": Steps.SETUP_PASSWORD},
        }

    return {
        "statusCode": status.HTTP_200_OK,
        "message": None,
        "payload": {"user": user, "token": token},
    }

async def handle_forgot_password(email: str):
    user = await user_collection.find_one(
        {"email": email.lower()},
        {"_id": 1, "fullName": 1, "emailVerifiedAt": 1},
    )

    if not user:
        return {
            "statusCode": status.HTTP_404_NOT_FOUND,
            "message": EErrorMessages.USER_NOT_EXISTS,
            "payload": None,
        }

    if not user.get("emailVerifiedAt"):
        return {
            "statusCode": status.HTTP_409_CONFLICT,
            "message": EErrorMessages.USER_NOT_VERIFIED,
            "payload": None,
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
        "payload": None,
    }

async def handle_resend_otp(email: str):
    user = await user_collection.find_one(
        {"email": email.lower()},
        {"_id": 1, "fullName": 1, "emailVerifiedAt": 1},
    )

    if not user:
        return {
            "statusCode": status.HTTP_404_NOT_FOUND,
            "message": EErrorMessages.USER_NOT_EXISTS,
            "payload": None,
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
        "payload": None,
    }

async def handle_reset_password(email: str, otp: int, new_password: str):
    user = await user_collection.find_one({"email": email.lower(), "OTP": otp})

    if not user:
        return {
            "statusCode": status.HTTP_404_NOT_FOUND,
            "message": EErrorMessages.INVALID_OTP,
            "payload": None,
        }

    otp_expire_at = user["OTPExpireAt"]
    current_time = int(time.time())
    if otp_expire_at > current_time:
        return {
            "statusCode": status.HTTP_409_CONFLICT,
            "message": EErrorMessages.OTP_EXPIRED,
            "payload": None,
        }

    hashed_password = AuthHelper.get_password_hash(new_password)
    await user_collection.update_one(
        {"_id": ObjectId(user["_id"])}, {"$set": {"password": hashed_password}}
    )
    return {
        "statusCode": status.HTTP_200_OK,
        "message": EResponseMessages.PASSWORD_RESET,
        "payload": None,
    }
