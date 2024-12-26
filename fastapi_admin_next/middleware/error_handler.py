from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_admin_next.error import CustomException


class ExceptionRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Middleware that intercepts exceptions and redirects accordingly.

        :param request: The incoming request object.
        :param call_next: A callable that processes the request and returns a response.
        :return: A response (either redirected or the original response).
        """
        try:
            response = await call_next(request)
        except CustomException as e:
            if e.code == 401:
                return RedirectResponse(url="/admin/auth/login/", status_code=303)
        return response
