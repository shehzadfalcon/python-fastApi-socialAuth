from fastapi import Request, status
from jose import JWTError, jwt
from bson import ObjectId
from typing import Callable
from functools import wraps
import os
from database import db

# utils
from utils.raise_response import raise_response
from enums.error_messages import EErrorMessages

SECRET_KEY = os.getenv("JWT_TOKEN_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


user_collection = db.get_collection("users")


# Custom decorator for protected routes
def UserDecorator(func: Callable):
    @wraps(func)
    async def decorated_function(request: Request, *args, **kwargs):
        token = request.headers.get("Authorization")
        if token:
            token = token.split("Bearer ")[-1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                _id = payload.get("sub")
                if _id is None:
                     raise_response(status.HTTP_404_NOT_FOUND, EErrorMessages.UNAUTHORIZED_USER.value)
            except JWTError:
                return raise_response(status.HTTP_401_UNAUTHORIZED, EErrorMessages.INVALID_TOKEN.value)

            user = await user_collection.find_one({"_id": ObjectId(_id)})
            if user is None:
                return raise_response(status.HTTP_404_NOT_FOUND, EErrorMessages.USER_NOT_EXISTS.value)
            user["_id"] = str(user["_id"])
            if "emailVerifiedAt" in user and user["emailVerifiedAt"]:
                user["emailVerifiedAt"] = str(user["emailVerifiedAt"])

            request.state.user = dict(user)
        else:
            return raise_response(status.HTTP_401_UNAUTHORIZED, EErrorMessages.UNAUTHORIZED_ACCESS.value)

        return await func(request, *args, **kwargs)

    return decorated_function
