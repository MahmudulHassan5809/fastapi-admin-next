from typing import Any
from sqlalchemy.sql import operators

OPERATORS_MAP: dict[str, Any] = {
    "isnull": lambda c, v: (c is None) if v else (c is not None),
    "exact": operators.eq,
    "ne": operators.ne,
    "gt": operators.gt,
    "ge": operators.ge,
    "lt": operators.lt,
    "le": operators.le,
    "in": operators.in_op,
    "notin": operators.notin_op,
    "between": lambda c, v: c.between(v[0], v[1]),
    "like": operators.like_op,
    "ilike": operators.ilike_op,
    "startswith": operators.startswith_op,
    "istartswith": lambda c, v: c.ilike(v + "%"),
    "endswith": operators.endswith_op,
    "iendswith": lambda c, v: c.ilike("%" + v),
    "overlaps": lambda c, v: c.overlaps(v),
}
