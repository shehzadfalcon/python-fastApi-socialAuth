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
from modules.auth.schemas.register import RegisterSchema
from modules.auth.schemas.login import LoginSchema
from modules.auth.schemas.verify_email import VerifyEmailSchema
from modules.auth.schemas.forgot_password import ForgotPasswordSchema
from modules.auth.schemas.reset_password import ResetPasswordSchema
from modules.auth.schemas.identify import IdentifyDto

# utils
from interfaces.response import IResponse
from utils.raise_response import raise_response
from utils.raise_exception import raise_exception

from enums.response_messages import EResponseMessages


# auth service
from .auth_service import AuthService

router = APIRouter()


@router.post("/identify", response_model=IResponse)
async def identify(identify_dto: IdentifyDto) -> IResponse:
    """
    Identify the user by email.

    - **identify_dto**: IdentifyDto - Contains the user's email.
    """
    try:
        data = await AuthService.identify_user(identify_dto.email)
        return raise_response(status.HTTP_200_OK, EResponseMessages.USER_IDENTIFIED.value, data)
    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)


@router.post("/register", response_model=IResponse)
async def register(form_data: RegisterSchema) -> IResponse:
    """
    Register a new user.

    - **form_data**: RegisterSchema - Contains registration data (e.g., email, password).
    """
    try:
        user_dict = form_data.dict()
        await AuthService.register_user(user_dict)
        return raise_response(status.HTTP_200_OK, EResponseMessages.USER_CREATED.value)
    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)


@router.post("/login", response_model=IResponse)
async def login(login_dto: LoginSchema) -> IResponse:
    """
    Log in a user.

    - **login_dto**: LoginSchema - Contains login data (email and password).
    """
    try:
        payload = await AuthService.login_user(login_dto.email, login_dto.password)
        return raise_response(
            status.HTTP_200_OK,
            EResponseMessages.USER_LOGIN.value,
            payload,
        )
    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)


@router.post("/verify-email", response_model=IResponse)
async def verify_email(verify_email_dto: VerifyEmailSchema) -> IResponse:
    """
    Verify a user's email using OTP.

    - **verify_email_dto**: VerifyEmailSchema - Contains email, OTP, and verification status.
    """
    try:
        payload = await AuthService.verify_user_email(
            verify_email_dto.email,
            verify_email_dto.otp,
            verify_email_dto.isVerifyEmail,
        )
        return raise_response(status.HTTP_200_OK, EResponseMessages.OTP_VERIFIED.value, payload)
    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)


@router.post("/forgot-password", response_model=IResponse)
async def forgot_password(forgot_password: ForgotPasswordSchema) -> IResponse:
    """
    Handle forgot password process.

    - **forgot_password**: ForgotPasswordSchema - Contains the user's email.
    """
    try:
        await AuthService.handle_forgot_password(forgot_password.email)
        return raise_response(status.HTTP_200_OK, EResponseMessages.PASSWORD_RESET_EMAIL.value)
    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)


@router.post("/resend-otp", response_model=IResponse)
async def resend_otp(resend_otp: ForgotPasswordSchema) -> IResponse:
    """
    Resend OTP to the user's email.

    - **resend_otp**: ForgotPasswordSchema - Contains the user's email.
    """
    try:
        await AuthService.handle_resend_otp(resend_otp.email)
        return raise_response(status.HTTP_200_OK, EResponseMessages.OTP_RESEND.value)
    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)


@router.post("/reset-password", response_model=IResponse)
async def reset_password(reset_password: ResetPasswordSchema) -> IResponse:
    """
    Reset the user's password using email or OTP.

    - **reset_password**: ResetPasswordSchema - Contains email, OTP, and new password.
    """
    try:
        await AuthService.handle_reset_password(reset_password.otp, reset_password.password)
        return raise_response(status.HTTP_200_OK, EResponseMessages.PASSWORD_RESET.value)
    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)
