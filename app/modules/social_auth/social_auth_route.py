import os
from fastapi.responses import RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
from fastapi import APIRouter, HTTPException, status, Request
from app.modules.social_auth.social_auth_service import SocialAuthService


from app.enums.error_messages import EErrorMessages
from cryptography.fernet import Fernet
from app.validations.link_account import LinkAccountDto
from app.enums.steps import Steps

router = APIRouter()
# fernet_key = os.getenv('FERNET_SECRET_KEY').encode()
# # key = Fernet.generate_key()
# fernet = Fernet(fernet_key)

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
    """Initiate Google login process"""
    with sso:
        return await sso.get_login_redirect()


@router.get("/google/callback")
async def auth_callback(request: Request):
 try:
    with sso:
        user = await sso.verify_and_process(request)
    if not user:
        RedirectResponse(url=f"{os.getenv('FRONTED_URL')}/login")
    profile = user.dict()
    payload= await SocialAuthService.social_login(
        profile["email"], profile["display_name"], profile["id"], profile["provider"]
    )

    if payload and "token" in payload and "user" in payload:
        token = payload["token"]
        user_data = str(payload["user"])
        redirect_url = f"{os.getenv('FRONTED_URL')}/login/google?token={token}&user={user_data}"
        return RedirectResponse(url=redirect_url)
    
    elif payload.get("nextStep") == Steps.ACCOUNT_LINKING:
        provider_id = profile["id"]
        provider = profile["provider"]
        encoded_email = profile["email"]
        redirect_url = f"{os.getenv('FRONTED_URL')}/link-account?otp_token={encoded_email}&providerId={provider_id}&provider={provider}"
        return RedirectResponse(url=redirect_url)
    else:
        return {
            "statusCode":status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }
 except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }

@router.post("/link-accounts", response_model=dict)
async def link_account(link_account_dto: LinkAccountDto):
    try:
        return await SocialAuthService.link_account(link_account_dto)

    except HTTPException as e:
        return {
            "statusCode": e.status_code,
            "message": EErrorMessages.SYSTEM_ERROR,
            "payload": None,
        }
