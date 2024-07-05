from typing import Optional
from app.modules.user.user_model import User
from pydantic import BaseModel


class ILogin(BaseModel):
    nextStep: Optional[str] = None
    user: Optional[User] = None
    token: Optional[str] = None
