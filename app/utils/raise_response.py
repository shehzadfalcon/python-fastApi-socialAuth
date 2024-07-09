from fastapi.responses import JSONResponse


def raise_response(status_code: int, message: str = None, payload: dict = None) -> dict:
    """
    Formats a response dictionary with the given status code, message, and optional payload.

    Args:
        status_code (int): The HTTP status code.
        message (str): The message to include in the response.
        payload (dict, optional): The data payload to include if any. Defaults to None.

    Returns:
        dict: A dictionary representing the formatted response.

    Example:
        >>> raise_response(200, "Success", {"data": "value"})
        {'statusCode': 200, 'message': 'Success', 'payload': {'data': 'value'}}

        >>> raise_response(404, "Not Found")
        {'statusCode': 404, 'message': 'Not Found'}
    """
    response = {"statusCode": status_code, "message": message}
    if payload is not None:
        response["payload"] = payload

    return JSONResponse(status_code=status_code, content=response)
