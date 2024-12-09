from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fastapi_admin_next.service import AdminNextService

router = APIRouter(prefix="/admin")


service = AdminNextService()


@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request) -> Any:
    models = service.get_homepage()
    return service.templates.TemplateResponse(
        "index.html", {"request": request, "models": models}
    )
