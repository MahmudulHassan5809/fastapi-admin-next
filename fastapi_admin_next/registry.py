from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.inspection import inspect


class ModelRegistry:
    """
    A registry to manage SQLAlchemy models. Keeps track of all registered models
    and provides access to them for CRUD or admin-like functionalities.
    """

    def __init__(self) -> None:
        self._models: list[type[DeclarativeMeta]] = []
        self._filter_fields: dict[Any, Any] = {}
        self._search_fields: dict[Any, Any] = {}

    def register(
        self,
        model: type[DeclarativeMeta],
        filter_fields: list[str] | None = None,
        search_fields: list[str] | None = None,
    ) -> None:
        """
        Register a SQLAlchemy model with its filter and search fields.
        """
        if filter_fields is None:
            filter_fields = []
        if search_fields is None:
            search_fields = []
        if model not in self._models:
            self._models.append(model)
            self._filter_fields[model] = filter_fields
            self._search_fields[model] = search_fields

    def get_models(self) -> list[type[DeclarativeMeta]]:
        """
        Get a list of all registered SQLAlchemy models.
        """
        return self._models

    def get_filter_fields(self, model: type[DeclarativeMeta]) -> list[str]:
        """
        Get the filter fields for a model.
        """
        return self._filter_fields.get(model, [])  # type: ignore

    def get_search_fields(self, model: type[DeclarativeMeta]) -> list[str]:
        """
        Get the search fields for a model.
        """
        return self._search_fields.get(model, [])  # type: ignore

    async def get_filter_options(
        self, model: type[DeclarativeMeta], field: str, db_session: AsyncSession
    ) -> list[dict[str, Any]]:
        """
        Get filter options for a given field, such as foreign key options,
        choice options, or enum options, using AsyncSession.
        """

        inspected_model = inspect(model)
        column = None

        for c in inspected_model.columns:  # type: ignore
            if c.name == field:
                column = c
                break

        if column is None:
            return []

        if column.foreign_keys:
            foreign_key = list(column.foreign_keys)[0]
            related_table = foreign_key.column.table

            related_model = None
            for mapper in model.registry.mappers:
                if mapper.persist_selectable == related_table:
                    related_model = mapper.class_
                    break

            if related_model is None:
                raise ValueError(f"Could not find ORM model for table {related_table}")

            result = await db_session.execute(related_model.__table__.select())
            related_objects = result.all()
            return [{"value": obj.id, "label": obj} for obj in related_objects]
        if hasattr(column.type, "enums"):
            return [
                {"value": value.value, "label": value} for value in column.type.enums
            ]

        result = await db_session.execute(
            model.__table__.select().with_only_columns([column]).distinct()  # type: ignore
        )
        distinct_values = result.scalars().all()

        return [{"value": value, "label": str(value)} for value in distinct_values]


registry = ModelRegistry()