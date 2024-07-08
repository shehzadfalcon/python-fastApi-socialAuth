from pydantic import BaseModel


class UpdateProfileSchema(BaseModel):
    fullName: str
