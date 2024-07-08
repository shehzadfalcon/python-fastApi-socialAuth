from typing import Optional
from app.modules.user.user_model import User
from pydantic import BaseModel,BaseModel, Field
from typing import Optional,Union
from bson import ObjectId

class ExtendedUser(User):
    id: Optional[str] = Field(None, alias="_id")
class ILogin(BaseModel):
    nextStep: Optional[str] = None
    user: Optional[ExtendedUser] = None
    token: Optional[str] = None
