# app/routes/user.py

from fastapi import APIRouter, HTTPException, Depends, status
from app.services.auth_helper import AuthHelper

from app.models.users import User
from app.database import db
from bson import ObjectId

router = APIRouter()

user_collection = db.get_collection("users")


@router.get("/profile", response_model=User)
async def get_profile(current_user: User = Depends(AuthHelper.get_authenticated_user)):
    return current_user


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    update_result = await user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": user.dict(by_alias=True)}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})
    return User(**updated_user)
