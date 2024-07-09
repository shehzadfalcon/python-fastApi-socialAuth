from utils.raise_response import raise_response
from fastapi import status, Request
from fastapi.exceptions import RequestValidationError

# Custom error handling middleware for validation errors

"""
Custom error handling middleware for validation errors in FastAPI.
"""


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles validation exceptions and formats error messages.

    Args:
        request (Request): The incoming FastAPI request object.
        exc (RequestValidationError): The validation error exception.

    Returns:
        JSONResponse: A JSON response with the formatted error messages and a 400 status code.
    """
    error_messages = ""
    for error in exc.errors():
        field_name = error.get("loc")[0]  # Get the field name from the error location
        if error.get("type") == "value_error":
            error_messages += f"{field_name.capitalize()} {error.get('msg')}. "
        elif error.get("type") == "string_too_short":
            error_messages += f"{field_name.capitalize()} should have at least 8 characters. "
        else:
            error_messages += f"{field_name.capitalize()} {error.get('msg')}. "

    return raise_response(status.HTTP_400_BAD_REQUEST, error_messages.strip())
