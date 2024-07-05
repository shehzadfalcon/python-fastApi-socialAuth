from pydantic import BaseModel


class LinkAccountDto(BaseModel):
    email: str
    otp: str
    providerId: str
    provider: str
