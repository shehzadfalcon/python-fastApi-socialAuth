from pydantic import EmailStr, BaseModel


class IdentifyDto(BaseModel):
    email: EmailStr
