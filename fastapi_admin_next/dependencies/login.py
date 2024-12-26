from fastapi.requests import Request

from fastapi_admin_next.error import LoginRequiredException


def login_required(request: Request) -> bool:
    if not request.user.is_authenticated:
        raise LoginRequiredException()
    return True
