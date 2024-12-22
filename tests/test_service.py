from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_admin_next.crud import CRUDGenerator
from fastapi_admin_next.db_connect import Base
from fastapi_admin_next.schemas import (
    CreateForm,
    DetailResponse,
    ListResponse,
    QueryParams,
    SaveForm,
)
from fastapi_admin_next.service import AdminNextService

from .utils import MockModel, RelatedModel


@pytest.mark.asyncio
async def test_get_create_view() -> None:
    service = AdminNextService()
    mock_db = AsyncMock(spec=AsyncSession)
    mock_related_result = MagicMock()
    mock_related_result.scalars.return_value = [RelatedModel(id=1, name="Related")]
    mock_db.execute.return_value = mock_related_result
    result = await service.get_create_view(MockModel, mock_db)
    assert isinstance(result, CreateForm)
    assert "enum_field" in result.enum_fields
    assert result.enum_fields["enum_field"] == ["option1", "option2"]
    assert "related" in result.related_options
    assert result.related_options["related"] == [{"id": 1, "label": "RelatedModel"}]
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_list_view() -> None:
    service = AdminNextService()
    mock_db = AsyncMock(spec=AsyncSession)
    mock_model = MagicMock(spec=Base)
    mock_model.__table__ = MagicMock()
    column1 = MagicMock()
    column1.name = "field1"
    column2 = MagicMock()
    column2.name = "field2"
    mock_model.__table__.columns = [column1, column2]
    mock_query_params = QueryParams(
        page=1,
        page_size=10,
        filter_params={},
        search_fields=["field1", "field2"],
        sorting=None,
    )
    with patch.object(
        service.registry, "get_search_fields", return_value=["field1", "field2"]
    ), patch.object(
        service.registry, "get_filter_fields", return_value=["field1"]
    ), patch.object(
        service.registry,
        "get_filter_options",
        AsyncMock(return_value=["option1", "option2"]),
    ) as mock_get_filter_options:
        mock_crud = AsyncMock(spec=CRUDGenerator)
        mock_crud.paginate_filter.return_value = ([{"id": 1}], 1)
        with patch("fastapi_admin_next.service.CRUDGenerator", return_value=mock_crud):
            result = await service.get_list_view(mock_model, mock_query_params, mock_db)
    assert isinstance(result, ListResponse)
    assert result.rows == [{"id": 1}]  # type: ignore
    assert result.total == 1
    assert result.columns == ["field1", "field2"]
    mock_get_filter_options.assert_called_once()


@pytest.mark.asyncio
async def test_save_view() -> None:
    service = AdminNextService()
    mock_db = AsyncMock(spec=AsyncSession)
    mock_model = MagicMock(spec=Base)
    valid_data = {"field1": "value1", "field2": "value2"}
    with patch.object(service.registry, "get_pydantic_model") as mock_get_pydantic:
        mock_get_pydantic.return_value = MagicMock(
            return_value=MagicMock(model_dump=lambda: valid_data)
        )

        result = await service.save_view(valid_data, mock_model, mock_db)
    assert isinstance(result, SaveForm)
    assert result.errors is None
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_save_view_with_validation_error() -> None:
    service = AdminNextService()
    mock_db = AsyncMock(spec=AsyncSession)
    mock_model = MagicMock(spec=Base)
    invalid_data = {"field1": "invalid"}

    with patch.object(service.registry, "get_pydantic_model") as mock_get_pydantic:
        mock_get_pydantic.side_effect = ValidationError.from_exception_data(
            "ValueError",
            [
                InitErrorDetails(  # type: ignore
                    type=PydanticCustomError("field1", "Invalid value"),
                    loc=("query", "field1"),
                )
            ],
        )

        result = await service.save_view(invalid_data, mock_model, mock_db)

    assert isinstance(result, SaveForm)
    assert result.errors is not None
    assert result.errors == {"field1": "Invalid value"}


@pytest.mark.asyncio
async def test_get_detail_view_with_relations() -> None:
    service = AdminNextService()
    mock_db = AsyncMock()
    mock_inspector = MagicMock()
    mock_inspector.relationships = {
        "related": MagicMock(
            target="related_model",
        )
    }
    mock_inspector.columns = {
        "field1": MagicMock(name="field1"),
        "field2": MagicMock(name="field2"),
        "related_id": MagicMock(name="related_id"),
    }
    mock_related_result = MagicMock()
    related_mock = MagicMock(id=1, name="Related 1", __str__=lambda self: "Related 1")
    related_mock.related_id = 1
    mock_related_result.fetchall.return_value = [(1, "Related 1")]
    mock_db.execute.return_value = mock_related_result
    with patch("sqlalchemy.inspection.inspect", return_value=mock_inspector):
        mock_crud = AsyncMock()
        mock_crud.get_by_id.return_value = {
            "id": 1,
            "field1": "value1",
            "field2": "value2",
            "related_id": 1,
        }
        with patch("fastapi_admin_next.service.CRUDGenerator", return_value=mock_crud):
            result = await service.get_detail_view(MockModel, "1", mock_db)
    assert isinstance(result, DetailResponse)
    assert result.row == {  # type: ignore
        "id": 1,
        "field1": "value1",
        "field2": "value2",
        "related_id": 1,
    }
    assert result.related_data == {"related_id": [(1, "(1, 'Related 1')")]}


@pytest.mark.asyncio
async def test_get_detail_view_not_found() -> None:
    pass


@pytest.mark.asyncio
async def test_update_view() -> None:
    service = AdminNextService()
    mock_db = AsyncMock(spec=AsyncSession)
    mock_model = MagicMock(spec=Base)
    valid_data = {"field1": "value1"}
    with patch.object(service.registry, "get_pydantic_model") as mock_get_pydantic:
        mock_pydantic_instance = MagicMock()
        mock_pydantic_instance.model_dump.return_value = valid_data
        mock_get_pydantic.return_value.return_value = mock_pydantic_instance

        result = await service.update_view(valid_data, mock_model, 1, mock_db)

    assert isinstance(result, SaveForm)
    assert result.errors is None
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_view_not_found() -> None:
    service = AdminNextService()
    mock_db = AsyncMock(spec=AsyncSession)
    mock_model = MagicMock(spec=Base)
    mock_db.get.return_value = None
    valid_data = {"field1": "value1"}
    with patch.object(service.registry, "get_pydantic_model") as mock_get_pydantic:
        mock_pydantic_instance = MagicMock()
        mock_pydantic_instance.model_dump.return_value = valid_data
        mock_get_pydantic.return_value.return_value = mock_pydantic_instance
        result = await service.update_view({}, mock_model, 1, mock_db)
    assert isinstance(result, SaveForm)
    assert result.errors == {"id": "Object not found"}
