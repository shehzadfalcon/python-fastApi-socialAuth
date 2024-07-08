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
from app.utils.create_response import create_response
from app.enums.error_messages import EErrorMessages
from app.enums.response_messages import EResponseMessages

from app.modules.user.schemas.update_password import UpdatePasswordSchema
from app.modules.user.schemas.update_profile import UpdateProfileSchema


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
        user["_id"]=str(user["_id"])
        user["password"]=None

        return create_response(status.HTTP_200_OK, EResponseMessages.PROFILE_FETCHED,{"user":user})

    @staticmethod
    async def update_user(user_id: str, user: UpdateProfileSchema):
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
        updated_user["_id"]=str(updated_user["_id"])
        return create_response(status.HTTP_200_OK, EResponseMessages.PROFILE_UPDATED,{"user":updated_user})

    

    @staticmethod
    async def update_pass(current_user:User, updatePasswordSchema:UpdatePasswordSchema):
        """
        Updates a user's password information.

        Args:
        - user (User): Updated user pass data.

        Returns:
        - User: Returns the updated user object.

        Raises:
        - HTTPException: Raises 404 HTTPException if user is not found.
        """
        print("user_dict----->",current_user)

        is_correct = await AuthHelper.authenticate_user(current_user['email'], updatePasswordSchema.oldPassword)
        if not is_correct:
            return create_response(status.HTTP_409_CONFLICT, EErrorMessages.INVALID_OLD_PASSWORD)
        user_dict = {"password":AuthHelper.get_password_hash(updatePasswordSchema.password)}
        update_result = await user_collection.update_one({"_id": ObjectId(current_user['_id'])}, {"$set": user_dict})
        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        updated_user = await user_collection.find_one({"_id": ObjectId(current_user['_id'])})
        updated_user["_id"]=str(updated_user["_id"])
        return create_response(status.HTTP_200_OK, EResponseMessages.PROFILE_UPDATED,{"user":updated_user})