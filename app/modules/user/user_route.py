"""
User Routes Module.

This module defines routes for user-related operations.

Imports:
- APIRouter: FastAPI router for defining API routes.
- HTTPException: FastAPI exception handling for HTTP errors.
- Depends: FastAPI dependency injection for handling dependencies.
- status: HTTP status codes.
- AuthHelper: Helper class for authentication operations.
- User: User model class.
- db: Database connection instance.
- ObjectId: MongoDB ObjectId type for document identification.
- UserService: Service class for user-related operations.
"""

from fastapi import APIRouter, Depends,status
from app.modules.user.user_model import User
from app.modules.user.user_service import UserService
from app.services.auth_helper import AuthHelper
from app.utils.create_response import create_response
from app.enums.response_messages import EResponseMessages
from app.interfaces.response import IResponse
from app.modules.user.schemas.update_profile import UpdateProfileSchema
from app.modules.user.schemas.update_password import UpdatePasswordSchema


router = APIRouter()


@router.get("/", response_model=IResponse)
async def get_profile(user = Depends(AuthHelper.get_authenticated_user)):
    """
    Retrieves the profile of the authenticated user.

    Args:
    - current_user (User): Current authenticated user obtained from UserService.

    Returns:
    - User: Returns the current user's profile.
    """
    return create_response(status.HTTP_200_OK, EResponseMessages.PROFILE_FETCHED,{"user":user})
    


@router.get("/{user_id}", response_model=IResponse)
async def get_user(user_id: str,current_user=Depends(AuthHelper.get_authenticated_user)):
    """
    Retrieves a user by their ObjectId.

    Args:
    - user_id (str): ObjectId of the user to retrieve.

    Returns:
    - User: Returns the user object if found.

    Raises:
    - HTTPException: Raises 404 HTTPException if user is not found.
    """
    return  await UserService.get_user_by_id(user_id)


@router.put("/", response_model=IResponse)
async def update_user(form_data: UpdateProfileSchema, current_user=Depends(AuthHelper.get_authenticated_user)):
    """
    Updates a user's profile information.

    Args:
    - user_id (str): ObjectId of the user to update.
    - user (User): Updated user data.

    Returns:
    - User: Returns the updated user object.

    Raises:
    - HTTPException: Raises 404 HTTPException if user is not found.
    """
    return await UserService.update_user(current_user._id, form_data)

@router.put("/password", response_model=IResponse)
async def update_user(form_data: UpdatePasswordSchema, current_user=Depends(AuthHelper.get_authenticated_user)):
    """
    Updates a user's password information.

    Args:
    - user (User): Updated user pass data.

    Returns:
    - User: Returns the updated user object.

    Raises:
    - HTTPException: Raises 404 HTTPException if user is not found.
    """
    return await UserService.update_pass(current_user, form_data)
    
