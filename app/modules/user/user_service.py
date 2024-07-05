"""
User Service Module.

This module provides methods for user-related operations.

Imports:
- HTTPException: FastAPI exception handling for HTTP errors.
- status: HTTP status codes.
- db: Database connection instance.
- AuthHelper: Helper class for authentication operations.
- User: User model class.
- ObjectId: MongoDB ObjectId type for document identification.
"""

from fastapi import HTTPException, status, Depends
from app.modules.user.user_model import User
from app.database import db
from bson import ObjectId
from app.services.auth_helper import AuthHelper

# Initialize user collection from the database
user_collection = db.get_collection("users")


class UserService:
    """
    Service class for user-related operations.

    Methods:
    - get_profile: Retrieves the profile of the authenticated user.
    - get_user_by_id: Retrieves a user by their ObjectId.
    - update_user: Updates a user's profile information.
    """

    @staticmethod
    async def get_profile(
        current_user: User = Depends(AuthHelper.get_authenticated_user),
    ):
        """
        Retrieves the profile of the authenticated user.

        Args:
        - current_user (User): Current authenticated user obtained from AuthHelper.

        Returns:
        - dict: Returns a dictionary with 'user' and 'token' keys.
          'user' contains the current user's profile as a dictionary.
          'token' contains the authentication token as a string.
        """
        token_data = {
            "sub": str(current_user["_id"]),
            "email": current_user["email"],
        }
        token = AuthHelper.create_access_token(data=token_data)
        return {
            "statusCode": status.HTTP_200_OK,
            "message": None,
            "payload": {
                "user": dict(current_user),
                "token": token,
            },
        }

    @staticmethod
    async def get_user_by_id(user_id: str):
        """
        Retrieves a user by their ObjectId.

        Args:
        - user_id (str): ObjectId of the user to retrieve.

        Returns:
        - dict: Returns a dictionary with 'user' key containing the user's profile as a dictionary.

        Raises:
        - HTTPException: Raises 404 HTTPException if user is not found.
        """
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "statusCode": status.HTTP_200_OK,
            "message": None,
            "payload": {
                "user": dict(user),
            },
        }

    @staticmethod
    async def update_user(user_id: str, user: User):
        """
        Updates a user's profile information.

        Args:
        - user_id (str): ObjectId of the user to update.
        - user (User): Updated user data.

        Returns:
        - dict: Returns a dictionary with 'user' key containing the updated user's profile as a dictionary.

        Raises:
        - HTTPException: Raises 404 HTTPException if user is not found.
        """
        update_result = await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": user.dict(by_alias=True)})
        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})
        return {
            "statusCode": status.HTTP_200_OK,
            "message": None,
            "payload": {
                "user": dict(updated_user),
            },
        }
