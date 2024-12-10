from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import JSON, Select, and_, cast, func, inspect, or_, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fastapi_admin_next.constants import OPERATORS_MAP
from fastapi_admin_next.db_connect import Base
from fastapi_admin_next.schemas import FilterOptions

ModelType = TypeVar("ModelType", bound=Base)  # pylint: disable=invalid-name


class CRUDGenerator(Generic[ModelType]):
    def __init__(
        self,
        model: type[ModelType],
        session: AsyncSession,
    ):
        self.session = session
        self.model: type[ModelType] = model

    async def get_related_options(
        self,
        model: ModelType,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Fetch related options for foreign key fields.
        Returns a dictionary where keys are field names, and values are lists of related data.
        """
        related_options = {}
        mapper = inspect(model)
        # Get the session directly
        for relationship in mapper.relationships:  # type: ignore
            related_model = relationship.mapper.class_
            field_name = relationship.key

            query = select(related_model)
            results = await self.session.execute(query)
            related_data = results.scalars().all()

            related_options[field_name] = [
                {"id": item.id, "label": str(item)} for item in related_data
            ]
        return related_options

    def _get_query(
        self,
        prefetch: tuple[str, ...] | None = None,
        options: list[Any] | None = None,
    ) -> Select[tuple[ModelType]]:
        query = select(self.model)
        if prefetch:
            if not options:
                options = []
            options.extend(joinedload(getattr(self.model, x)) for x in prefetch)
            query = query.options(*options).execution_options(populate_existing=True)
        return query

    def _build_sorting(self, sorting: dict[str, str]) -> list[Any]:
        """Build list of ORDER_BY clauses."""
        result = []
        for field_name, direction in sorting.items():
            field = getattr(self.model, field_name)
            result.append(getattr(field, direction)())
        return result

    def _build_filters(self, filters: dict[str, Any]) -> list[Any]:
        """Build list of WHERE conditions."""
        result = []
        for expression, value in filters.items():
            parts = expression.split("__")
            op_name = parts[1] if len(parts) > 1 else "exact"
            if op_name not in OPERATORS_MAP:
                msg = f"Expression {expression} has incorrect operator {op_name}"
                raise KeyError(msg)
            operator = OPERATORS_MAP[op_name]
            column = getattr(self.model, parts[0])
            result.append(operator(column, value))
        return result

    async def filter(
        self,
        filter_options: FilterOptions,
    ) -> Sequence[ModelType]:
        query = self._get_query(filter_options.prefetch)
        if filter_options.distinct_on:
            query = query.distinct(getattr(self.model, filter_options.distinct_on))
        if (
            filter_options.query_params
            and filter_options.query_params.sorting is not None
        ):
            query = query.order_by(
                *self._build_sorting(filter_options.query_params.sorting)
            )

        condition = (
            or_(*self._build_filters(filter_options.filters))
            if filter_options.use_or
            else and_(*self._build_filters(filter_options.filters))
        )
        # Get the session directly
        db_execute = await self.session.execute(query.where(condition))
        result = db_execute.scalars().all()
        return result

    async def paginate_filter(
        self,
        filter_options: FilterOptions,
    ) -> tuple[Sequence[ModelType], int]:
        query = self._get_query(filter_options.prefetch)

        if (
            filter_options.query_params
            and filter_options.query_params.sorting is not None
        ):
            query = query.order_by(
                *self._build_sorting(filter_options.query_params.sorting)
            )
        condition = (
            or_(*self._build_filters(filter_options.filters))
            if filter_options.use_or
            else and_(*self._build_filters(filter_options.filters))
        )

        # Add search condition if `search` is provided
        if filter_options.query_params and filter_options.query_params.search:
            search_condition = []
            if filter_options.query_params.search_fields:
                for field in filter_options.query_params.search_fields:
                    column = getattr(self.model, field, None)
                    if column:
                        search_condition.append(
                            column.ilike(f"%{filter_options.query_params.search}%")
                        )

            if search_condition:
                condition = condition & or_(*search_condition)

        # Get the session directly
        total_query = select(func.count()).select_from(
            query.where(condition).subquery()
        )
        total = await self.session.scalar(total_query) or 0
        if filter_options.query_params:
            query = query.offset(filter_options.query_params.skip).limit(
                filter_options.query_params.page_size
            )
        db_execute = await self.session.execute(query.where(condition))
        result = db_execute.scalars().all()
        return result, total

    async def get_all(
        self,
        filters: dict[str, str] | None = None,
    ) -> Sequence[ModelType]:
        query = select(self.model)
        if filters:
            for attr, value in filters.items():
                query = query.where(getattr(self.model, attr) == value)
        # Get the session directly
        results = await self.session.execute(query)
        return results.scalars().all()

    async def get_by_id(
        self, obj_id: str, prefetch: tuple[str, ...] | None = None
    ) -> ModelType | None:
        query = self._get_query(prefetch).where(self.model.id == obj_id)  # type: ignore
        # Get the session directly
        result_cursor = await self.session.execute(query)
        result = result_cursor.scalars().first()
        return result

    async def create(self, db: AsyncSession, obj_data: dict[str, Any]) -> ModelType:
        obj = self.model(**obj_data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self, where: dict[str, Any], values: dict[str, Any]) -> int:
        # Get the session directly
        filters = self._build_filters(where)

        update_values = {}
        for key, value in values.items():
            if isinstance(value, dict) and isinstance(
                getattr(self.model, key).type, JSON
            ):
                update_values[key] = cast(getattr(self.model, key), JSONB).concat(
                    cast(value, JSONB)
                )
            else:
                update_values[key] = value

        query = update(self.model).where(and_(True, *filters)).values(**update_values)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
