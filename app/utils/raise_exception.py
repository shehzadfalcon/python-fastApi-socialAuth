from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any, Union
from enums.error_messages import EErrorMessages


def raise_exception(status_code: int, message: Union[str, Any] = None) -> JSONResponse:
    """
    Formats a response dictionary with the given status code, message, and optional payload.

    Args:
        status_code (int): The HTTP status code.
        message (Union[str, Any]): The message or error detail to include in the response.

    Returns:
        JSONResponse: A JSONResponse object representing the formatted response.

    Example:
        >>> raise_exception(200, "Success", {"data": "value"})
        JSONResponse({'statusCode': 200, 'message': 'Success')

        >>> raise_exception(404, "Not Found")
        JSONResponse({'statusCode': 404, 'message': 'Not Found'})
    """
    if isinstance(message, HTTPException):
        if message.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR:
            message = message.detail
        else:
            message = EErrorMessages.SYSTEM_ERROR.value

    response = {"statusCode": status_code, "message": message}

    return JSONResponse(status_code=status_code, content=response)
