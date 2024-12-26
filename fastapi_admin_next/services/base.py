from typing import Any

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from fastapi_admin_next.jinja_filters import ceil_filter, getattr_filter
from fastapi_admin_next.registry import registry


class BaseService:
    def __init__(self) -> None:
        templates_directory = "fastapi_admin_next/templates"
        self.templates = Jinja2Templates(directory=templates_directory)
        self.templates.env.filters["getattr"] = getattr_filter
        self.templates.env.filters["ceil_filter"] = ceil_filter
        self.registry = registry

    def redirect(
        self,
        path: str,
        cookies: dict[str, Any] | None = None,
        remove_session: bool = False,
    ) -> RedirectResponse:
        if not cookies:
            cookies = {}
        response = RedirectResponse(path, status_code=302)
        for k, v in cookies.items():
            response.set_cookie(key=k, value=v, httponly=True)
        if remove_session:
            response.set_cookie(key="session_ended", value="1", httponly=True)
            response.delete_cookie("auth_token")
        return response
