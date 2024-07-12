from typing import Optional
from modules.user.user_model import User
from pydantic import BaseModel, Field

"""
This module defines Pydantic models for user-related data, extending
existing models and adding new ones for specific use cases.
"""
class Token(BaseModel):
    token:str

class ExtendedUser(User):
    """
    ExtendedUser is a Pydantic model that extends the User model, adding an
    optional 'id' field which is an alias for '_id'.

    Attributes:
        id (Optional[str]): The unique identifier for the user, aliased from '_id'.
    """

    id: Optional[str] = Field(None, alias="_id")


class ILogin(BaseModel):
    """
    ILogin is a Pydantic model that represents the data structure for a
    login response.

    Attributes:
        nextStep (Optional[str]): The next step in the authentication process.
        user (Optional[ExtendedUser]): The user's profile information.
        token (Optional[str]): The authentication token.
    """

    nextStep: Optional[str] = None
    user: Optional[ExtendedUser] = None
    token: Optional[Token] = None
