def create_response(status_code: int, message: str, payload=None):
    return {
        "statusCode": status_code,
        "message": message,
        "payload": payload,
    }
