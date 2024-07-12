"""
Authentication and Social Login Router.

This module defines routes for authentication via Google OAuth and social login callbacks.

Imports:
- RedirectResponse: FastAPI response class for redirections.
- GoogleSSO: Google SSO integration for OAuth.
- APIRouter: FastAPI router for defining API routes.
- HTTPException: Exception handling for HTTP errors.
- status: HTTP status codes.
- Request: FastAPI request object.
- SocialAuthService: Service handling social authentication operations.
- EErrorMessages: Enum containing error messages.
- Fernet: Encryption module for token handling.
- LinkAccountDto: Data transfer object for linking accounts.
- Steps: Enum containing workflow steps.

Variables:
- CLIENT_ID: Google OAuth client ID retrieved from environment variables.
- CLIENT_SECRET: Google OAuth client secret retrieved from environment variables.
- REDIRECT_URI: Google OAuth callback URL retrieved from environment variables.
- sso: GoogleSSO instance for handling OAuth authentication.

Routes:
- /google: Initiates Google OAuth login process.
- /google/callback: Handles Google OAuth callback for user verification and redirection.
- /link-accounts: Handles linking of user accounts from different providers.

"""

import os
from fastapi.responses import RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
from fastapi import APIRouter, HTTPException, status, Request
from modules.social_auth.social_auth_service import SocialAuthService
from enums.response_messages import EResponseMessages
from enums.error_messages import EErrorMessages

from modules.auth.schemas.link_account import LinkAccountDto
from enums.steps import Steps

# utils
from utils.raise_response import raise_response
from utils.raise_exception import raise_exception
from interfaces.response import IResponse
import base64
import json
# Initialize APIRouter
router = APIRouter()

# Retrieve OAuth credentials from environment variables
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_CALLBACK_URL")

# Initialize GoogleSSO instance
sso = GoogleSSO(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    allow_insecure_http=True,  # Set to False in production
)


@router.get("/google")
async def auth_login():
    """
    Initiates Google OAuth login process.

    Returns:
    - RedirectResponse: Redirects user to Google login page.
    """
    with sso:
        return await sso.get_login_redirect()


@router.get("/google/callback")
async def auth_callback(request: Request):
    """
    Handles Google OAuth callback for user verification and redirection.

    Args:
    - request (Request): FastAPI request object containing user information.

    Returns:
    - RedirectResponse: Redirects user to appropriate frontend URL based on authentication result.
    - dict: Returns error response in case of HTTPException.
    """
    try:
        with sso:
            user = await sso.verify_and_process(request)

        if not user:
            RedirectResponse(url=f"{os.getenv('FRONTEND_URL')}/login")

        profile = user.dict()
        payload = await SocialAuthService.social_login(
            profile["email"],
            profile["display_name"],
            profile["id"],
            profile["provider"],
        )
        if payload and "token" in payload and "user" in payload:
            token =base64.b64encode(json.dumps(payload["token"]).encode()).decode()
            user= json.dumps(payload["user"])
            user_data =base64.b64encode(user.encode()).decode()
            redirect_url = f"{os.getenv('FRONTEND_URL')}/login/google?token={token}&user={user_data}"
            return RedirectResponse(url=redirect_url)

        elif payload.get("nextStep") == Steps.ACCOUNT_LINKING.value:
            provider_id =base64.b64encode(profile["id"].encode()).decode()
            provider = base64.b64encode(profile["provider"].encode()).decode()
            encoded_email = base64.b64encode(profile["email"].encode()).decode()
            redirect_url = f"{os.getenv('FRONTEND_URL')}/link-account?otp_token={encoded_email}&providerId={provider_id}&provider={provider}"
            return RedirectResponse(url=redirect_url)
        else:
            raise_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                EErrorMessages.SYSTEM_ERROR.value,
            )

    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)


@router.post("/link-accounts", response_model=IResponse)
async def link_account(link_account_dto: LinkAccountDto) -> IResponse:
    """
    Handles linking of user accounts from different providers.

    Args:
    - link_account_dto (LinkAccountDto): Data transfer object containing account linking information.

    Returns:
    - dict: Returns success or error response based on linking operation.
    """
    try:
        payload = await SocialAuthService.link_account(link_account_dto)
        return raise_response(status.HTTP_200_OK, EResponseMessages.OTP_VERIFIED.value, payload)

    except HTTPException as e:
        return raise_exception(e.status_code, e.detail)
