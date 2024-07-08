from typing import Optional
from modules.user.user_model import User
from pydantic import BaseModel, Field


class ExtendedUser(User):
    id: Optional[str] = Field(None, alias="_id")


class ILogin(BaseModel):
    nextStep: Optional[str] = None
    user: Optional[ExtendedUser] = None
    token: Optional[str] = None
