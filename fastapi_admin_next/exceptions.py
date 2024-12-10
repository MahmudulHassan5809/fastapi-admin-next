from fastapi import status


class CustomException(Exception):
    code = status.HTTP_502_BAD_GATEWAY
    message = "Bad Gateway"

    def __init__(
        self, errors: dict[str, str] | None = None, message: str | None = None
    ):
        self.errors = errors
        self.message = message or self.message


class DatabaseError(CustomException):
    code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Database Error"


class ValidationException(CustomException):
    code = status.HTTP_400_BAD_REQUEST
    message = "Validation failed"
