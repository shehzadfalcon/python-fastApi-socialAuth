from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone

# Enum for User Role
from enum import Enum


class EUserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


# Define the Provider model (if you have a Provider model)
class Provider(BaseModel):
    # Add the fields for Provider here
    providerId: str
    provider: str
    pass


class User(BaseModel):
    full_name: str = Field(..., alias="fullName", min_length=1)
    avatar: Optional[str] = None
    email: EmailStr
    password: str = Field("", min_length=6)
    email_verified_at: Optional[datetime] = Field(None, alias="emailVerifiedAt")
    otp_expire_at: Optional[int] = Field(None, alias="OTPExpireAt")
    otp: Optional[int] = Field(None, alias="OTP")
    is_active: bool = Field(True, alias="isActive")
    providers: Optional[List[Provider]] = None
    role: EUserRole = Field(default=EUserRole.USER, alias="role")
    deleted_at: Optional[datetime] = Field(None, alias="deletedAt")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")
