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

from fastapi import APIRouter, HTTPException, status, Request
from modules.user.user_service import UserService

#utils
from utils.format_response import format_response

#enums
from enums.response_messages import EResponseMessages
from enums.error_messages import EErrorMessages
from interfaces.response import IResponse

# schemas
from modules.user.schemas.update_profile import UpdateProfileSchema
from modules.user.schemas.update_password import UpdatePasswordSchema

# Decorator
from decorators.user import UserDecorator

router = APIRouter()


@router.get("/", response_model=IResponse)
@UserDecorator
async def get_profile(request: Request):
    """
    Retrieves the profile of the authenticated user.

    Args:
    - current_user (User): Current authenticated user obtained from UserService.

    Returns:
    - User: Returns the current user's profile.
    """
    try:
        user = request.state.user
        return format_response(status.HTTP_200_OK, EResponseMessages.PROFILE_FETCHED.value, {"user": UserService.formatUser(user)})
    except HTTPException as e:
        return format_response(e.status_code, EErrorMessages.SYSTEM_ERROR.value)


@router.get("/{user_id}", response_model=IResponse)
@UserDecorator
async def get_user(request: Request, user_id: str):
    """
    Retrieves a user by their ObjectId.s

    Args:
    - user_id (str): ObjectId of the user to retrieve.

    Returns:
    - User: Returns the user object if found.

    Raises:
    - HTTPException: Raises 404 HTTPException if user is not found.
    """

    try:
        return await UserService.get_user_by_id(user_id)
    except HTTPException as e:
        return format_response(e.status_code, EErrorMessages.SYSTEM_ERROR.value)


@router.put("/", response_model=IResponse)
@UserDecorator
async def update_user(request: Request, form_data: UpdateProfileSchema):
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
    try:
        current_user = request.state.user
        return await UserService.update_user(current_user["_id"], form_data)
    except HTTPException as e:
        print("Error--->", e)
        return format_response(e.status_code, EErrorMessages.SYSTEM_ERROR.value)


@router.put("/password", response_model=IResponse)
@UserDecorator
async def update_password(request: Request, form_data: UpdatePasswordSchema):
    """
    Updates a user's password information.

    Args:
    - user (User): Updated user pass data.

    Returns:
    - User: Returns the updated user object.

    Raises:
    - HTTPException: Raises 404 HTTPException if user is not found.
    """
    try:
        current_user = request.state.user
        return await UserService.update_password(current_user, form_data)

    except HTTPException as e:
        return format_response(e.status_code, EErrorMessages.SYSTEM_ERROR.value)
