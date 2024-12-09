import os

from fastapi.templating import Jinja2Templates

from fastapi_admin_next.registry import ModelRegistry


class AdminNextService:
    def __init__(self) -> None:
        templates_directory = os.path.join(os.path.dirname(__file__), "../../templates")
        self.templates = Jinja2Templates(directory=templates_directory)
        self.registry = ModelRegistry()

    def get_homepage(self) -> list[str]:
        return [model.__name__ for model in self.registry.get_models()]
