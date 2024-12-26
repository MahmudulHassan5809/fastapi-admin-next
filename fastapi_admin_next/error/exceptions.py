from fastapi import status


class CustomException(Exception):
    code = status.HTTP_502_BAD_GATEWAY
    message = "Bad Gateway"


class LoginRequiredException(CustomException):
    code = status.HTTP_401_UNAUTHORIZED
