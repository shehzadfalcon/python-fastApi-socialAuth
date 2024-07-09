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

from fastapi import HTTPException, status
from modules.user.user_model import User
from database import db
from bson import ObjectId

# utils
from services.auth_helper import AuthHelper

# enums
from enums.error_messages import EErrorMessages

# schemas
from modules.user.schemas.update_password import UpdatePasswordSchema
from modules.user.schemas.update_profile import UpdateProfileSchema


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
    def formatUser(user: User) -> User:
        user["_id"] = str(user["_id"])
        if "emailVerifiedAt" in user and user["emailVerifiedAt"]:
            user["emailVerifiedAt"] = str(user["emailVerifiedAt"])

        return user

    @staticmethod
    async def get_user_by_id(user_id: str) -> dict[User]:
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.USER_NOT_EXISTS)
        user["_id"] = str(user["_id"])
        user["emailVerifiedAt"] = str(user["emailVerifiedAt"])
        user["password"] = None
        return {"user": UserService.formatUser(user)}

    @staticmethod
    async def update_user(user_id: str, user: UpdateProfileSchema) -> dict[User]:
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.USER_NOT_EXISTS)

        updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})
        return {"user": UserService.formatUser(updated_user)}

    @staticmethod
    async def update_password(current_user: User, updatePasswordSchema: UpdatePasswordSchema) -> dict[User]:
        """
        Updates a user's password information.

        Args:
        - user (User): Updated user pass data.

        Returns:
        - User: Returns the updated user object.

        Raises:
        - HTTPException: Raises 404 HTTPException if user is not found.
        """

        is_correct = await AuthHelper.authenticate_user(current_user["email"], updatePasswordSchema.oldPassword)
        if not is_correct:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EErrorMessages.INVALID_OLD_PASSWORD.value)

        user_dict = {"password": AuthHelper.get_password_hash(updatePasswordSchema.password)}
        update_result = await user_collection.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": user_dict})
        if update_result.modified_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EErrorMessages.USER_NOT_EXISTS)

        updated_user = await user_collection.find_one({"_id": ObjectId(current_user["_id"])})
        return {"user": UserService.formatUser(updated_user)}
