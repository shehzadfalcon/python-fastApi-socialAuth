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

from fastapi import APIRouter, Depends
from app.models.users import User
from app.modules.user.user_service import UserService

router = APIRouter()


@router.get("/profile", response_model=User)
async def get_profile(current_user: User = Depends(UserService.get_profile)):
    """
    Retrieves the profile of the authenticated user.

    Args:
    - current_user (User): Current authenticated user obtained from UserService.

    Returns:
    - User: Returns the current user's profile.
    """
    return current_user


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """
    Retrieves a user by their ObjectId.

    Args:
    - user_id (str): ObjectId of the user to retrieve.

    Returns:
    - User: Returns the user object if found.

    Raises:
    - HTTPException: Raises 404 HTTPException if user is not found.
    """
    return await UserService.get_user_by_id(user_id)


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
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
    return await UserService.update_user(user_id, user)
