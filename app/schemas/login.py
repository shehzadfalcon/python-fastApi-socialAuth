from pydantic import EmailStr, BaseModel


class LoginSchema(BaseModel):
    email: EmailStr
    password: str
