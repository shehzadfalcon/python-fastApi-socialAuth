# app/responses/response.py

from typing import Generic, Optional, TypeVar, Union
from pydantic import BaseModel
from starlette.status import HTTP_200_OK
from interfaces.login import ILogin


T = TypeVar("T")


class IResponse(BaseModel, Generic[T]):
    statusCode: int = HTTP_200_OK
    message: Optional[str] = ""
    payload: Optional[Union[ILogin, dict]] = {}
