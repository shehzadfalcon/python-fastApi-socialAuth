from typing import Generic, Optional, TypeVar, Union
from pydantic import BaseModel
from starlette.status import HTTP_200_OK
from interfaces.login import ILogin

"""
This module defines the IResponse class, a generic response model for API responses.
"""

T = TypeVar("T")


class IResponse(BaseModel, Generic[T]):
    """
    IResponse is a generic Pydantic model for API responses.

    Attributes:
        statusCode (int): The HTTP status code of the response, default is 200 (OK).
        message (Optional[str]): A message describing the response, default is an empty string.
        payload (Optional[Union[ILogin, dict]]): The data payload of the response, can be an ILogin instance or a dictionary.
    """

    statusCode: int = HTTP_200_OK
    message: Optional[str] = ""
    payload: Optional[Union[ILogin, dict]] = {}
