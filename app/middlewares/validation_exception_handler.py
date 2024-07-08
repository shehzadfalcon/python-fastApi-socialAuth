
from utils.format_response import format_response
from fastapi import status,Request
from fastapi.exceptions import RequestValidationError

# Custom error handling middleware for validation errors
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = ""
    for error in exc.errors():
        field_name = error.get("loc")[0]  # Get the field name from the error location
        if error.get("type") == "value_error":
            error_messages += f"{field_name.capitalize()} {error.get('msg')}. "
        elif error.get("type") == "string_too_short":
            error_messages += f"{field_name.capitalize()} should have at least 8 characters. "
        else:
            error_messages += f"{field_name.capitalize()} {error.get('msg')}. "

    return format_response(status.HTTP_400_BAD_REQUEST,error_messages.strip())
