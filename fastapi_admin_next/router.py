from fastapi import APIRouter, Depends

from fastapi_admin_next.controllers import admin_router, auth_router
from fastapi_admin_next.dependencies import login_required

app_router = APIRouter()

include_api = app_router.include_router

routers = (
    (admin_router, "apps", "Buy Private", "private"),
    (auth_router, "auth", "Auth", "public"),
)

for router_item in routers:
    router, prefix, tag, api_type = router_item

    if api_type == "private":
        include_api(
            router,
            prefix=f"/{prefix}",
            tags=[tag],
            dependencies=[Depends(login_required)],
        )
    else:
        include_api(
            router,
            prefix=f"/{prefix}",
            tags=[tag],
        )
