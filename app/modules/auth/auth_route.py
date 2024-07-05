"""
Routes for authentication-related operations.

These routes handle user identification, registration, login, email verification,
password management (reset, forgot, resend OTP), and associated error handling.

Endpoints:
- /identify: Identify user by email.
- /register: Register a new user.
- /login: Log in a user.
- /verify-email: Verify user's email using OTP.
- /forgot-password: Handle forgot password process.
- /resend-otp: Resend OTP to user's email.
- /reset-password: Reset user's password using email or OTP.

Each endpoint returns an IResponse model, which includes statusCode, message,
and optional payload.

"""

from fastapi import APIRouter, HTTPException, status

# validation schema
from app.schemas.register import RegisterSchema
from app.schemas.login import LoginSchema
from app.schemas.verify_email import VerifyEmailSchema
from app.schemas.forgot_password import ForgotPasswordSchema
from app.schemas.reset_password import ResetPasswordSchema
from app.schemas.identify import IdentifyDto

# utils
from app.enums.error_messages import EErrorMessages
from app.enums.response_messages import EResponseMessages
from app.interfaces.response import IResponse
from app.utils.create_response import create_response


# auth service
from app.modules.auth.auth_service import AuthService

router = APIRouter()


@router.post("/identify", response_model=IResponse)
async def identify(identify_dto: IdentifyDto):
    """
    Identify the user by email.

    - **identify_dto**: IdentifyDto - Contains the user's email.
    """
    try:
        return await AuthService.identify_user(identify_dto.email)
    except HTTPException as e:
        return create_response(e.status_code, EErrorMessages.SYSTEM_ERROR)


@router.post("/register", response_model=IResponse)
async def register(form_data: RegisterSchema):
    """
    Register a new user.

    - **form_data**: RegisterSchema - Contains registration data (e.g., email, password).
    """
    try:
        user_dict = form_data.dict()
        return await AuthService.register_user(user_dict)
    except HTTPException as e:
        return create_response(e.status_code, EErrorMessages.SYSTEM_ERROR)


@router.post("/login", response_model=IResponse)
async def login(login_dto: LoginSchema):
    """
    Log in a user.

    - **login_dto**: LoginSchema - Contains login data (email and password).
    """
    try:
        return await AuthService.login_user(
            login_dto.email, login_dto.password
        )
    except HTTPException as e:
        return create_response(e.status_code, EErrorMessages.SYSTEM_ERROR)


@router.post("/verify-email", response_model=IResponse)
async def verify_email(verify_email_dto: VerifyEmailSchema):
    """
    Verify a user's email using OTP.

    - **verify_email_dto**: VerifyEmailSchema - Contains email, OTP, and verification status.
    """
    try:
        return await AuthService.verify_user_email(
            verify_email_dto.email,
            verify_email_dto.otp,
            verify_email_dto.isVerifyEmail,
        )
    except HTTPException as e:
        return create_response(e.status_code, EErrorMessages.SYSTEM_ERROR)


@router.post("/forgot-password", response_model=IResponse)
async def forgot_password(forgot_password: ForgotPasswordSchema):
    """
    Handle forgot password process.

    - **forgot_password**: ForgotPasswordSchema - Contains the user's email.
    """
    try:
        return await AuthService.handle_forgot_password(forgot_password.email)
    except HTTPException as e:
        return create_response(e.status_code, EErrorMessages.SYSTEM_ERROR)


@router.post("/resend-otp", response_model=IResponse)
async def resend_otp(resend_otp: ForgotPasswordSchema):
    """
    Resend OTP to the user's email.

    - **resend_otp**: ForgotPasswordSchema - Contains the user's email.
    """
    try:
        return await AuthService.handle_resend_otp(resend_otp.email)
    except HTTPException as e:
        return create_response(e.status_code, EErrorMessages.SYSTEM_ERROR)


@router.post("/reset-password", response_model=IResponse)
async def reset_password(reset_password: ResetPasswordSchema):
    """
    Reset the user's password using email or OTP.

    - **reset_password**: ResetPasswordSchema - Contains email, OTP, and new password.
    """
    try:
        return await AuthService.handle_reset_password(
            reset_password.email, reset_password.otp, reset_password.password
        )
    except HTTPException as e:
        return create_response(e.status_code, EErrorMessages.SYSTEM_ERROR)
