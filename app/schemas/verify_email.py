from pydantic import EmailStr, BaseModel
from typing import Optional


class VerifyEmailSchema(BaseModel):
    otp: str
    isVerifyEmail: Optional[bool] = False
    email: EmailStr
