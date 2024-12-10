from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    current_page: int
    next_page: int | None
    prev_page: int | None
    last_page: int
    extra: Any | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    data: Sequence[T]
    meta: PaginationMeta


class QueryParams(BaseModel):
    page: int = Field(1, ge=1, description="The page number to retrieve")
    page_size: int = Field(10, ge=1, le=100, description="The number of items per page")
    search: str | None = Field(None, description="The search query")
    search_fields: list[str] | None = None
    filter_params: dict[str, Any] | None = None
    sorting: dict[str, str] | None = None

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


class FilterOptions(BaseModel):
    filters: dict[str, Any]
    query_params: QueryParams | None = None
    prefetch: tuple[str, ...] | None = None
    use_or: bool = False
    distinct_on: str | None = None


class ListResponse(BaseModel, Generic[T]):
    rows: Sequence[T]
    total: int
    columns: list[str]
    filter_options: dict[str, Any]
    models: list[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class CreateForm(BaseModel):
    columns: list[str]
    enum_fields: dict[str, Any]
    related_options: dict[str, Any]
    fk_to_rel_map: dict[str, Any]
    models: list[str]


class SaveForm(BaseModel):
    errors: dict[str, Any] | None = None


class DetailResponse(BaseModel, Generic[T]):
    row: T
    columns: list[str]
    related_data: dict[str, Any]
    enum_fields: dict[str, Any]
    models: list[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NotFoundResponse(BaseModel):
    message: str
