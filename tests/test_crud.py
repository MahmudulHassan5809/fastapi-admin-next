from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_admin_next.crud import CRUDGenerator

from .utils import MockModel, RelatedModel


@pytest.mark.asyncio
async def test_get_related_options() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    related_instance = RelatedModel(id=1)
    mock_query_result = MagicMock()
    mock_query_result.scalars().all.return_value = [related_instance]
    mock_session.execute.return_value = mock_query_result
    crud_generator = CRUDGenerator(MockModel, mock_session)
    result = await crud_generator.get_related_options(MockModel)  # type: ignore
    assert "related" in result
    assert result["related"] == [{"id": 1, "label": "RelatedModel"}]
    mock_session.execute.assert_called_once()
    mock_query_result.scalars().all.assert_called_once()


@pytest.mark.asyncio
async def test_get_query() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    crud_generator = CRUDGenerator(MockModel, mock_session)
    query = crud_generator._get_query(  # pylint: disable=protected-access
        prefetch=("related",)
    )
    assert "SELECT" in str(query), "Query should include SELECT statement"
    assert "related" in str(query), "Query should include prefetch field"


@pytest.mark.asyncio
async def test_build_sorting() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    crud_generator = CRUDGenerator(MockModel, mock_session)
    sorting_params = {"id": "asc"}
    result = crud_generator._build_sorting(  # pylint: disable=protected-access
        sorting_params
    )
    assert len(result) == 1, "Sorting should return one clause"
    assert "ASC" in str(result[0]), "Sorting direction should be ascending"


@pytest.mark.asyncio
async def test_build_filters() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    crud_generator = CRUDGenerator(MockModel, mock_session)
    filters = {"id__exact": 1}
    result = crud_generator._build_filters(filters)  # pylint: disable=protected-access
    assert len(result) == 1, "Filters should return one condition"
    assert "id" in str(result[0]), "Condition should include field name"
    assert "1" in str(result[0]), "Condition should include filter value"


@pytest.mark.asyncio
async def test_get_by_id() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    mock_query_result = MagicMock()
    mock_query_result.scalars().first.return_value = MockModel(id=1)
    mock_session.execute.return_value = mock_query_result
    crud_generator = CRUDGenerator(MockModel, mock_session)
    result = await crud_generator.get_by_id(obj_id="1")
    assert result.id == 1, "Should return the model with the correct ID"  # type: ignore
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    crud_generator = CRUDGenerator(MockModel, mock_session)
    obj_data = {"id": 1}
    result = await crud_generator.create(mock_session, obj_data)
    assert result.id == 1, "Should create a model instance with the correct data"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    crud_generator = CRUDGenerator(MockModel, mock_session)
    where = {"id__exact": 1}
    values = {"related_field_id": 2}

    row_count = await crud_generator.update(where, values)

    assert (
        row_count == mock_session.execute.return_value.rowcount
    ), "Should return the correct row count"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_paginate_filter() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    mock_query_result = MagicMock()
    mock_query_result.scalars().all.return_value = [MockModel(id=1)]
    mock_session.execute.return_value = mock_query_result
    mock_session.scalar.return_value = 1  # Total count
    crud_generator = CRUDGenerator(MockModel, mock_session)
    filter_options = MagicMock()
    filter_options.filters = {"id__exact": 1}
    filter_options.prefetch = None
    filter_options.query_params = None
    filter_options.use_or = False
    result, total = await crud_generator.paginate_filter(filter_options)
    assert len(result) == 1, "Should return one filtered result"
    assert total == 1, "Should return the total count"
