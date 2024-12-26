from typing import Any

from pydantic import ValidationError
from sqlalchemy import Enum, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from fastapi_admin_next.configs import AuthConfigManager
from fastapi_admin_next.crud import CRUDGenerator
from fastapi_admin_next.db_connect import Base
from fastapi_admin_next.schemas import (
    CreateForm,
    DetailResponse,
    FilterOptions,
    ListResponse,
    NotFoundResponse,
    QueryParams,
    SaveForm,
)
from fastapi_admin_next.security import PasswordHandler

from .base import BaseService


class AdminNextService(BaseService):

    def get_models(self) -> list[str]:
        return [model.__name__ for model in self.registry.get_models()]

    def get_homepage(self) -> list[str]:
        return self.get_models()

    async def get_list_view(
        self,
        model: type[Base],
        query_params: QueryParams,
        db: AsyncSession,
    ) -> ListResponse[Base]:
        filters = query_params.filter_params
        query_params.search_fields = self.registry.get_search_fields(model)
        filter_fields = self.registry.get_filter_fields(model)
        filter_options = {}
        for field in filter_fields:
            filter_options[field] = await self.registry.get_filter_options(
                model, field, db
            )

        crud: CRUDGenerator[Base] = CRUDGenerator(model=model, session=db)

        rows, total = await crud.paginate_filter(
            filter_options=FilterOptions(
                filters=filters,
                query_params=query_params,
                sorting=query_params.sorting,
            ),
        )

        display_fields = self.registry.get_display_fields(model)
        columns = (
            display_fields
            if display_fields
            else [column.name for column in model.__table__.columns]
        )

        return ListResponse(
            rows=rows,
            total=total,
            columns=columns,
            filter_options=filter_options,
            models=self.get_models(),
        )

    async def get_create_view(
        self,
        model: type[Base],
        db: AsyncSession,
    ) -> CreateForm:
        inspector = inspect(model)
        columns = [col.key for col in inspector.columns if col.key != "id"]
        relationships = inspector.relationships

        fk_to_rel_map = {
            fk.name: rel.key
            for rel in relationships.values()
            for fk in rel._calculated_foreign_keys  # pylint: disable=protected-access
        }

        enum_fields = {
            col.key: list(col.type.enums)
            for col in inspector.columns.values()
            if isinstance(col.type, Enum)
        }

        related_options = {}
        for _, rel in relationships.items():
            stmt = select(rel.mapper.class_)
            related_rows = await db.execute(stmt)
            related_options[rel.key] = [
                {"id": getattr(row, "id"), "label": str(row)}
                for row in related_rows.scalars()
            ]

        return CreateForm(
            columns=columns,
            enum_fields=enum_fields,
            related_options=related_options,
            fk_to_rel_map=fk_to_rel_map,
            models=self.get_models(),
        )

    async def save_view(
        self,
        data_dict: dict[str, Any],
        model: type[Base],
        db: AsyncSession,
    ) -> SaveForm:

        try:
            processed_data = {
                key: (
                    PasswordHandler.hash(value)
                    if "password" in key.lower() and isinstance(value, str)
                    else value
                )
                for key, value in data_dict.items()
            }

            validated_data = self.registry.get_pydantic_model(model)(**processed_data)
            obj = model(**validated_data.model_dump())
            db.add(obj)
            await db.commit()
            return SaveForm(errors=None)
        except ValidationError as e:
            error_messages = {err["loc"][-1]: err["msg"] for err in e.errors()}
            return SaveForm(errors=error_messages)

    async def get_detail_view(
        self,
        model: type[Base],
        obj_id: str,
        db: AsyncSession,
    ) -> DetailResponse[Base] | NotFoundResponse:
        inspector = inspect(model)
        crud = CRUDGenerator(model=model, session=db)
        obj_to_update = await crud.get_by_id(obj_id=obj_id)
        if not obj_to_update:
            return NotFoundResponse(message="Object not found")

        # relationships = inspect(model).relationships
        # related_data = {}
        # for _, rel in relationships.items():
        #     # Use the foreign key column name as the key
        #     fk_column = list(rel.local_columns)[0].name
        #     stmt = select(rel.mapper.class_)

        #     related_rows = await db.execute(stmt)
        #     related_data[fk_column] = [
        #         (getattr(row, "id"), str(row)) for row in related_rows.scalars()
        #     ]

        # print(related_data, "-----")

        related_data = {}
        for _, rel in inspect(model).relationships.items():
            related_result = await db.execute(text(f"SELECT * FROM {rel.target}"))
            fk_column = list(rel.local_columns)[0].name
            related_data[fk_column] = [
                (row[0], str(row)) for row in related_result.fetchall()
            ]

        columns = [
            column.name for column in model.__table__.columns if column.name != "id"
        ]

        enum_fields = {
            col.key: list(col.type.enums)
            for col in inspector.columns.values()
            if isinstance(col.type, Enum)
        }

        return DetailResponse(
            row=obj_to_update,
            columns=columns,
            related_data=related_data,
            enum_fields=enum_fields,
            models=self.get_models(),
        )

    async def update_view(
        self,
        data_dict: dict[str, Any],
        model: type[Base],
        obj_id: int,
        db: AsyncSession,
    ) -> SaveForm:
        try:
            validated_data = self.registry.get_pydantic_model(model)(**data_dict)
            data_dict = validated_data.model_dump()
            id = obj_id  # pylint: disable=redefined-builtin
            obj = await db.get(model, id)
            if not obj:
                return SaveForm(errors={"id": "Object not found"})

            auth_config = AuthConfigManager.get_auth_config()
            if data_dict.get(auth_config.password_field):
                if data_dict.get(auth_config.password_field) != getattr(
                    obj, auth_config.password_field
                ):
                    data_dict[auth_config.password_field] = PasswordHandler.hash(
                        data_dict[auth_config.password_field]
                    )
                else:
                    data_dict.pop(auth_config.password_field)

            for key, value in data_dict.items():
                setattr(obj, key, value)
            await db.commit()
            return SaveForm(errors=None)
        except ValidationError as e:
            error_messages = {err["loc"][-1]: err["msg"] for err in e.errors()}
            return SaveForm(errors=error_messages)
