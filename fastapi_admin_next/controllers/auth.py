from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from fastapi_admin_next.db_connect import DBConnector
from fastapi_admin_next.services import AuthService

router = APIRouter(prefix="")


service = AuthService()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.get("/login/")
async def login(
    request: Request,
) -> Any:
    return service.templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "errors": None,
        },
    )


@router.post("/login/")
async def login_action(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(DBConnector.dependency()),
) -> Any:
    form_data = await request.form()
    data_dict = {key: value or None for key, value in form_data.items()}
    data, is_valid = await service.login(data_dict=data_dict, db=db)

    if not is_valid:
        return service.templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "errors": data,
            },
        )

    response.set_cookie(**data)
    response.status_code = 303
    response.headers["Location"] = "/admin/apps/"
    return response


@router.get("/logout", response_class=HTMLResponse)
def logout_get_view(_: Request) -> Any:
    return service.redirect(path="/admin/auth/login/", remove_session=True)
