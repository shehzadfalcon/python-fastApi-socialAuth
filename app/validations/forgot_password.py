from pydantic import EmailStr, BaseModel


class ForgotPasswordSchema(BaseModel):
    email: EmailStr
