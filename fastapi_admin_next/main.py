"""Fast Api module"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from fastapi_admin_next.controllers import router
from fastapi_admin_next.db_connect import DBConnector


class FastAPIAdminNextApp:
    def __init__(self) -> None:
        self.app = FastAPI(
            title="FastAPI Admin Next",
            description="FastAPI Admin Next",
        )
        self.make_middleware()

    def make_middleware(self) -> None:

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )

    def init_routers(self) -> None:
        self.app.include_router(router)

    def create_app(self, db_url: str) -> FastAPI:
        DBConnector.register_db(db_url)
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        self.app.mount(
            "/admin/static",
            StaticFiles(directory=static_dir, html=True),
            name="static",
        )
        self.init_routers()
        return self.app


fastapi_admin_next_app = FastAPIAdminNextApp()
