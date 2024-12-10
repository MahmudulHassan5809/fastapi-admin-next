from pydantic import BaseModel, ConfigDict, create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty

from fastapi_admin_next.db_connect import Base


def generate_pydantic_model(
    db_model: Base,
    *,
    exclude: list[str] | None = None,
) -> type[BaseModel]:
    config = (ConfigDict(from_attributes=True),)
    if not exclude:
        exclude = ["id"]
    mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty) and attr.columns:
            name = attr.key
            if name in exclude:
                continue
            column = attr.columns[0]
            python_type: type | None = None
            if hasattr(column.type, "impl"):
                if hasattr(column.type.impl, "python_type"):
                    python_type = column.type.impl.python_type
            elif hasattr(column.type, "python_type"):
                python_type = column.type.python_type
            assert python_type, f"Could not infer python_type for {column}"
            default = None
            if column.default is None and not column.nullable:
                default = ...
            fields[name] = (python_type, default)
    pydantic_model: type[BaseModel] = create_model(
        db_model.__name__, __config__=config, **fields  # type: ignore
    )
    return pydantic_model
