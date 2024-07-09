from pydantic import BaseModel, Field, validator
import re
from typing import Optional


class ResetPasswordSchema(BaseModel):
    otp: Optional[str] = None
    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password must be between 8 and 255 characters long",
    )

    @validator("password")
    def validate_password(cls, v):
        # Check for at least one digit, one lowercase letter, one uppercase letter, and one special character
        if not re.match(
            r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[-!$%^&*()_+|~=`{}\[\]:;"\'<>,.?\\/@#])',
            v,
        ):
            raise ValueError("Password must contain at least one number," "one lowercase letter, one uppercase letter," "and one special character")
        return v
